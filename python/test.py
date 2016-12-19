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
from keras.layers import Input, Embedding, LSTM, Dense, Activation, merge
#from keras.utils.visualize_util import plot
#from keras.optimizers import RMSprop
import PIL
from random import random
import math

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

    #print 'vocab', midiKeras.vocab
    print 'len vocab', len(midiKeras.vocab)
    if addToVocab:
        with open(pathPrefix + '-vocab.pickle', 'w') as f:
            f.write(pickle.dumps(midiKeras.vocab))

    # vocab complexity
    for t in trainData:
        lens = {}
        for k in t:
            e = midiKeras.vocab[k]
            for n in e:
                l = len(e[n])
                if l not in lens:
                    lens[l] = 0
                lens[l] += 1
        print 'note lens', lens
    lens = {}
    for e in midiKeras.vocab[1:]:
        for n in e:
            l = len(e[n])
            if l not in lens:
                lens[l] = 0
            lens[l] += 1
    print 'vocab lens', lens

    trainBS = (len(trainData), 1)
    testBS = (len(testData), 1)
    (fTrainData, fTrainLabels) = midiKeras.formatData(trainData)
    (fTestData, fTestLabels) = midiKeras.formatData(testData)

    for m in ['iter', 'iter2', 'iter3', 'iter4', 'iter5', 'iter6', 'iter7']:
        with open('keras_models/' + m + '-struct.json') as f:
            model = model_from_json(f.read())
            model.load_weights('keras_models/' + m + '-weights.h5')
            model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])
            test1 = midiKeras.rebatchModel(model, len(trainData))
            test1.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])
            test2 = midiKeras.rebatchModel(model, len(testData))
            test2.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])

        print m
        print test1.evaluate(fTrainData, fTrainLabels, len(trainData))
        print test2.evaluate(fTestData, fTestLabels, len(testData))
