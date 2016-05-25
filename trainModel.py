import midiKeras as mk
import sys
from os import path
from time import strftime
import pickle
from keras.callbacks import EarlyStopping
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
                rms = RMSprop(lr = 0.001)
                model.compile(optimizer = rms, loss = 'mse', metrics = ['accuracy'])
            if path.exists(pathPrefix + '-vocab.pickle'):
                with open(pathPrefix + '-vocab.pickle') as f:
                    vocab = pickle.loads(f.read())
                addToVocab = False
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

    if len(trainData) and not doRewrite:
        if model == None:
            model = midiKeras.genModel()
        (fTrainData, fTrainLabels) = midiKeras.formatData(trainData, 16, 512)
        if len(testData):
            (fTestData, fTestLabels) = midiKeras.formatData(testData, 16, 512)
            earlyStopping = EarlyStopping(monitor = 'val_loss', mode = 'min', patience = 1)
            history = model.fit(fTrainData, fTrainLabels, nb_epoch = 10, batch_size = 32, validation_data = (fTestData, fTestLabels), callbacks = [earlyStopping])
        else:
            history = model.fit(fTrainData, fTrainLabels, nb_epoch = 10, batch_size = 32)
        model.save_weights(pathPrefix + '-weights.h5', overwrite = True)
        with open(pathPrefix + '-struct.json', 'w') as f:
            f.write(model.to_json())
        with open(pathPrefix + '-history.pickle', 'w') as f:
            f.write(pickle.dumps(history.history))
