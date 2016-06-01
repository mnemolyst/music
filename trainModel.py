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
from keras.layers import Input, Embedding, LSTM, Dense, Activation
#from keras.optimizers import RMSprop

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
            #earlyStopping = EarlyStopping(monitor = 'acc', patience = 1)
            #modelCheckpoint = ModelCheckpoint(pathPrefix + '-weights.h5')
            #history = model.fit(fTrainData, fTrainLabels, nb_epoch = nbEpoch, batch_size = batchShape[0], shuffle = False, callbacks = [earlyStopping, modelCheckpoint])

            input = Input(batch_shape = batchShape, dtype = 'int32', name = 'input')
            x = Embedding(len(midiKeras.vocab), 128, mask_zero = True, dropout = 0.5)(input)
            x = LSTM(32, return_sequences = True, stateful = True, dropout_W = 0.5, dropout_U = 0.5)(x)
            x = LSTM(32, return_sequences = True, stateful = True, dropout_W = 0.5, dropout_U = 0.5)(x)
            x = LSTM(32, return_sequences = True, stateful = True, dropout_W = 0.5, dropout_U = 0.5)(x)
            x = LSTM(32, stateful = True, dropout_W = 0.5, dropout_U = 0.5)(x)
            aux_loss = Dense(len(midiKeras.vocab), activation = 'softmax', name = 'aux_loss')(x)
            x = Dense(64, activation = 'relu')(x)
            x = Dense(64, activation = 'relu')(x)
            x = Dense(64, activation = 'relu')(x)
            x = Dense(64, activation = 'relu')(x)
            main_loss = Dense(len(midiKeras.vocab), activation = 'softmax', name = 'main_loss')(x)
            model2 = Model(input = input, output = [aux_loss, main_loss])
            #model2 = Model(input = input, output = main_loss)
            model2.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'], loss_weights = {'aux_loss': 0.2, 'main_loss': 1})
            #model2.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])
            #earlyStopping = EarlyStopping(monitor = 'acc', patience = 1)
            modelCheckpoint = ModelCheckpoint(pathPrefix + '2-weights.h5')
            history = model2.fit({'input': fTrainData}, {'aux_loss': fTrainLabels, 'main_loss': fTrainLabels}, nb_epoch = nbEpoch, batch_size = batchShape[0], shuffle = False, callbacks = [modelCheckpoint])
            #history = model2.fit(fTrainData, fTrainLabels, nb_epoch = nbEpoch, batch_size = batchShape[0], shuffle = False, callbacks = [modelCheckpoint])

        #with open(pathPrefix + '-history.pickle', 'w') as f:
        #    f.write(pickle.dumps(history.history))
