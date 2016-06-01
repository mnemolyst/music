import midiKeras as mk
import sys
from os import path
from time import strftime
import pickle
import numpy as np
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import model_from_json
from keras.optimizers import RMSprop

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
                model.compile(optimizer = 'rmsprop', loss = 'mse', metrics = ['accuracy'])
            if path.exists(pathPrefix + '-vocab.pickle'):
                with open(pathPrefix + '-vocab.pickle') as f:
                    vocab = pickle.loads(f.read())
                addToVocab = False
        elif sys.argv[i] == 'epochs':
            nbEpoch = sys.argv[i + 1]
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
        vData = midiKeras.vocabularize(notes, resolution / 16, addNew = addToVocab)
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
        vData = midiKeras.vocabularize(notes, resolution / 16, addNew = addToVocab)
        if {} in midiKeras.vocab:
            vData = midiKeras.stripSilence(vData, midiKeras.vocab.index({}))
        testData.append(vData)
        print 'len vData', len(vData)
        if doRewrite:
            midiKeras.midiOut(vData, 'midi/rewrite/' + path.basename(f), resolution)

    #print 'vocab', midiKeras.vocab
    print 'len vocab', len(midiKeras.vocab)
    if addToVocab:
        with open(pathPrefix + '-vocab.pickle', 'w') as f:
            f.write(pickle.dumps(midiKeras.vocab))

    # vocab complexity
    #for t in trainData:
    #    lens = {}
    #    for k in t:
    #        e = midiKeras.vocab[k]
    #        for n in e:
    #            l = len(e[n])
    #            if l not in lens:
    #                lens[l] = 0
    #            lens[l] += 1
    #    print 'lens', lens
    #lens = {}
    #for e in midiKeras.vocab[1:]:
    #    for n in e:
    #        l = len(e[n])
    #        if l not in lens:
    #            lens[l] = 0
    #        lens[l] += 1
    #print 'vocab lens', lens

    if len(trainData) and not doRewrite:
        batchShape = (len(trainData), 1)
        if model == None:
            model = midiKeras.genModel(batchShape)
            with open(pathPrefix + '-struct.json', 'w') as f:
                f.write(model.to_json())

        (fTrainData, fTrainLabels) = midiKeras.formatData(trainData)

        if len(testData):
            (fTestData, fTestLabels) = midiKeras.formatData(testData)
            earlyStopping = EarlyStopping(monitor = 'val_loss', patience = 1)
            modelCheckpoint = ModelCheckpoint(pathPrefix + '-weights.h5', monitor = 'val_loss', verbose = 0, save_best_only = True)
            history = model.fit(fTrainData, fTrainLabels, nb_epoch = nbEpoch, batch_size = batchShape[0], shuffle = False, validation_data = (fTestData, fTestLabels), callbacks = [earlyStopping, modelCheckpoint])
        else:
            earlyStopping = EarlyStopping(monitor = 'acc', patience = 1)
            modelCheckpoint = ModelCheckpoint(pathPrefix + '-weights.h5')
            history = model.fit(fTrainData, fTrainLabels, nb_epoch = nbEpoch, batch_size = batchShape[0], shuffle = False, callbacks = [earlyStopping, modelCheckpoint])

            #model2 = midiKeras.genModel2(batchShape)
            #model2.layers[0].set_weights(model.layers[0].get_weights())
            #model2.layers[0].trainable = False
            #model2.layers[1].set_weights(model.layers[1].get_weights())
            #model2.layers[1].trainable = False
            #a = model2.layers[2].get_weights()
            #for i in [0,1,3,4,6,7,9,10]:
            #    a[i] = np.identity(128)
            #for i in [2,5,8,11]:
            #    a[i] = np.zeros(128)
            #model2.layers[2].set_weights(a)
            #model2.layers[3].set_weights(model.layers[2].get_weights())
            #model2.layers[4].set_weights(model.layers[3].get_weights())
            #model2.layers[5].set_weights(model.layers[4].get_weights())
            #model2.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])
            ##earlyStopping = EarlyStopping(monitor = 'acc', patience = 1)
            #modelCheckpoint = ModelCheckpoint(pathPrefix + '2-weights.h5')
            #history = model2.fit(fTrainData, fTrainLabels, nb_epoch = nbEpoch, batch_size = batchShape[0], shuffle = False, callbacks = [modelCheckpoint])

        #with open(pathPrefix + '-history.pickle', 'w') as f:
        #    f.write(pickle.dumps(history.history))
