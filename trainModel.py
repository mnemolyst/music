import midiKeras as mk
import sys
from os import path
import pickle
from keras.callbacks import EarlyStopping

if __name__ == '__main__':
    midiKeras = mk.MidiKeras()
    doRewrite = False
    isTrainFile = True
    trainFiles = []
    testFiles = []
    vocab = [None]
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == 'train':
            isTrainFile = True
        elif sys.argv[i] == 'test':
            isTrainFile = False
        elif sys.argv[i] == 'rewrite':
            doRewrite = True
        elif sys.argv[i] == 'vocab':
            with open(sys.argv[i + 1]) as f:
                vocab = pickle.loads(f.read())
            i += 1
        elif path.exists(sys.argv[i]):
            if isTrainFile:
                trainFiles.append(sys.argv[i])
            else:
                testFiles.append(sys.argv[i])
        i += 1

    trainData = []
    for f in trainFiles:
        print f
        (vData, vocab) = midiKeras.vocabNotes(midiKeras.midiRip(f), vocab)
        trainData.append(vData)
        #print vData
        print 'len vData', len(vData)
        #print vocab
        print 'len vocab', len(vocab)
        if doRewrite:
            midiOut(vData, 'midi/rewrite/' + path.basename(f))

    testData = []
    for f in testFiles:
        print f
        (vData, vocab) = midiKeras.vocabNotes(midiKeras.midiRip(f), vocab)
        testData.append(vData)
        #print vData
        print 'len vData', len(vData)
        #print vocab
        print 'len vocab', len(vocab)
        if doRewrite:
            midiKeras.midiOut(vData, 'midi/rewrite/' + path.basename(f))

    with open(path.join('keras_models', 'vocab'), 'w') as f:
        f.write(pickle.dumps(vocab))

    if len(trainData) and not doRewrite:
        model = midiKeras.genModel(len(vocab))
        (fTrainData, fTrainLabels) = midiKeras.formatData(trainData, 128, 512, len(vocab))
        if len(testData):
            (fTestData, fTestLabels) = midiKeras.formatData(testData, 128, 512, len(vocab))
            earlyStopping = EarlyStopping(monitor = 'val_loss', mode = 'min')
            model.fit(fTrainData, fTrainLabels, nb_epoch = 10, batch_size = 32, validation_data = (fTestData, fTestLabels), callbacks = [earlyStopping])
        else:
            model.fit(fTrainData, fTrainLabels, nb_epoch = 10, batch_size = 32)
