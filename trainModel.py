import midiKeras as mk
import sys
from os import path
from time import strftime
import pickle
import numpy as np
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import model_from_json
# XXX testing
from keras.models import Sequential, Model
from keras.layers import Input, Embedding, LSTM, Dense, Activation, Highway
from keras import backend as K
from theano import function
#from keras.utils.visualize_util import plot
#from keras.optimizers import RMSprop
import PIL
from random import random, randint
import math
import json

if __name__ == '__main__':
    doRewrite = False
    isTrainFile = True
    trainFiles = []
    testFiles = []
    model = None
    vocab = [None, {}]
    addToVocab = True
    pathPrefix = path.join('keras_models', strftime('%d-%b-%H:%M'))
    nbEpoch = 10
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == 'train':
            isTrainFile = True
        elif sys.argv[i] == 'test':
            isTrainFile = False
        elif sys.argv[i] == 'rewrite':
            doRewrite = True
        elif sys.argv[i] == 'model':
            pathPrefix = sys.argv[i + 1]
            i += 1
            if path.exists(pathPrefix + '-struct.json'):
                with open(pathPrefix + '-struct.json') as f:
                    model = model_from_json(f.read())
                if path.exists(pathPrefix + '-weights.h5'):
                    model.load_weights(pathPrefix + '-weights.h5')
                model.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])
            if path.exists(pathPrefix + '-vocab.pickle'):
                with open(pathPrefix + '-vocab.pickle') as f:
                    vocab = pickle.loads(f.read())
                addToVocab = False
        elif sys.argv[i] == 'epochs':
            nbEpoch = int(sys.argv[i + 1])
            i += 1
        elif path.exists(sys.argv[i]):
            if isTrainFile:
                trainFiles.append(sys.argv[i])
            else:
                testFiles.append(sys.argv[i])
        i += 1

    midiKeras = mk.MidiKeras(vocab)

    trainData = []
    for f in trainFiles:
        print f
        (notes, resolution) = midiKeras.midiRip(f)
        vData = midiKeras.vocabularize(notes, resolution / 4, addNew = addToVocab)
        if {} in midiKeras.vocab:
            vData = midiKeras.stripSilence(vData, midiKeras.vocab.index({}))
        trainData.append(vData)
        print 'len vData', len(vData)
        if doRewrite:
            midiKeras.midiOut(vData, 'midi/rewrite/' + path.basename(f), resolution)

    testData = []
    for f in testFiles:
        print f
        (notes, resolution) = midiKeras.midiRip(f)
        vData = midiKeras.vocabularize(notes, resolution / 4, addNew = False)
        if {} in midiKeras.vocab:
            vData = midiKeras.stripSilence(vData, midiKeras.vocab.index({}))
        testData.append(vData)
        print 'len vData', len(vData)
        if doRewrite:
            midiKeras.midiOut(vData, 'midi/rewrite/' + path.basename(f), resolution)

    # generate random training data
    if not len(trainData):
        for note in range(40, 70):
            midiKeras.vocab.append( {note: [mk.NOTE_ON]} )
            midiKeras.vocab.append( {note: [mk.NOTE_HOLD]} )
            midiKeras.vocab.append( {note: [mk.NOTE_OFF]} )
        for i in range(1):
            vData = [ ]
            for j in range(64):
                vData.append( randint(0, len(midiKeras.vocab) - 1) )
            trainData.append(vData)

    print midiKeras.vocab
    print trainData

    #print 'vocab', midiKeras.vocab
    print 'len vocab', len(midiKeras.vocab)
    if addToVocab:
        with open(pathPrefix + '-vocab.pickle', 'w') as f:
            f.write(pickle.dumps(midiKeras.vocab))

    # vocab complexity
    for t in trainData:
        lens = { }
        for k in t:
            e = midiKeras.vocab[k]
            for n in e:
                l = len(e[n])
                if l not in lens:
                    lens[l] = 0
                lens[l] += 1
        print 'note lens', lens
    lens = { }
    for e in midiKeras.vocab[1:]:
        for n in e:
            l = len(e[n])
            if l not in lens:
                lens[l] = 0
            lens[l] += 1
    print 'vocab lens', lens

    if len(trainData) and not doRewrite:
        batchShape = (len(trainData), 1)
        if model == None:
            model = midiKeras.genModel(batchShape)

        (fTrainData, fTrainLabels) = midiKeras.formatData(trainData)

        if False and len(testData):
            (fTestData, fTestLabels) = midiKeras.formatData(testData)
            earlyStopping = EarlyStopping(monitor = 'val_loss', patience = 1)
            modelCheckpoint = ModelCheckpoint(pathPrefix + '-weights.h5', monitor = 'val_loss', verbose = 0, save_best_only = True)
            history = model.fit(fTrainData, fTrainLabels, nb_epoch = nbEpoch, batch_size = batchShape[0], shuffle = False, validation_data = (fTestData, fTestLabels), callbacks = [earlyStopping, modelCheckpoint])
        else: # XXX only do this
            def imgTest(model, iterN):
                model.reset_states()
                img = PIL.Image.new('RGB', (max(len(x) for x in trainData), 129 * len(trainData)))
                for i, t in enumerate(trainData):
                    for j, k in enumerate(t):
                        e = midiKeras.vocab[k]
                        for n in e:
                            img.putpixel((j, 129 * i + n), (255, 255, 255))
                pred = model.predict_classes(fTrainData, batch_size = batchShape[0])
                i = 0
                for batchIdx in range(0, len(pred), batchShape[0]):
                    batch = pred[batchIdx : batchIdx + batchShape[0]]
                    es = [midiKeras.vocab[x] for x in batch]
                    for j, e in enumerate(es):
                        if e != None:
                            for n in e:
                                p = img.getpixel((i, 129 * j + n))
                                img.putpixel((i, 129 * j + n), (255, p[1] / 2, p[2] / 2))
                    i += 1
                img.save(pathPrefix + '-i' + str(iterN) + '.png')

            def train(model, idx = None):
                lossHist = []
                i = 1
                while True:
                    print 'i', i
                    metrics = np.zeros((len(model.metrics_names), ))
                    for j in range(0, len(fTrainData), batchShape[0]):
                        batch = (fTrainData[j:j + batchShape[0]], fTrainLabels[j:j + batchShape[0]])
                        metrics += model.train_on_batch(batch[0], batch[1])
                    model.reset_states()
                    metrics /= len(fTrainData) / float(batchShape[0])
                    lossHist = lossHist[-14:] + [metrics[model.metrics_names.index('loss')]]
                    print zip(model.metrics_names, metrics)
                    if len(lossHist) == 15:
                        fit = np.polyfit(range(15), lossHist, 1)
                        if fit[0] > 0:
                            break
                    imgTest(model, i)

                    #################
                    # image weights #
                    #################
                    #if idx != None:
                    #    for l in model.layers:
                    #        weights = l.get_weights()
                    #        for j, m in enumerate(weights):
                    #            m = (m.astype(np.float32) - np.min(m)) / (np.max(m) - np.min(m)) * 256
                    #            if len(m.shape) < 2:
                    #                continue
                    #                #m = np.reshape(m, (m.shape[0], -1))
                    #            img = PIL.Image.fromarray(m, 'L')
                    #            img.save(pathPrefix + '-' + str(idx) + '-i' + str(i) + '-layer-' + l.name + '-' + str(j) + '.png')
                    i += 1
                return lossHist[-1]

            #f = K.function([model.layers[0].input, K.learning_phase()], [x.updates for x in model.layers if type(x) == LSTM])
            #o = f([fTrainData[0 : batchShape[0]], 1])
            imgTest(model, 0)
            train(model)

            loss = None
            while False:
                defn = json.loads(model.to_json())
                defn['config'] = defn['config'][:-1] + defn['config'][-2:-1] + defn['config'][-1:]
                newModel = model_from_json(json.dumps(defn))
                for l in defn['config'][:-2]:
                    #l.trainable = False
                    newModel.add(l)
                newModel.add(LSTM(64, return_sequences = True, stateful = True))
                newModel.add(LSTM(64, stateful = True))
                newModel.add(Dense(len(midiKeras.vocab), activation = 'softmax'))
                newModel.layers[-3].set_weights(model.layers[-2].get_weights())
                newModel.layers[-1].set_weights(model.layers[-1].get_weights())
                newModel.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])
                print len(newModel.layers), 'layers'
                #train(newModel)

                #for l in newModel.layers:
                #    l.trainable = True
                #print 'fine tuning'
                #newModel.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])
                lastLoss = loss
                loss = train(newModel)
                model = newModel
                if lastLoss != None and lastLoss < loss:
                    break

            with open(pathPrefix + '-struct.json', 'w') as f:
                f.write(model.to_json())
            model.save_weights(pathPrefix + '-weights.h5')
    elif False and len(testData):
        batchShape = (len(testData), 1)
        if model == None:
            model = midiKeras.genModel(batchShape)
            with open(pathPrefix + '-struct.json', 'w') as f:
                f.write(model.to_json())
        #else:
        #    model.layers[0].batch_input_shape = batchShape
        #    model.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])

        (fTestData, fTestLabels) = midiKeras.formatData(testData)

        print len(fTestData)
        a = model.evaluate(fTestData, fTestLabels, batch_size = batchShape[0])
        print a
