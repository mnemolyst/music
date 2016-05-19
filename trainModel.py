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
        (notes, resolution) = midiKeras.midiRip(f)
        vData = midiKeras.vocabNotes(notes, resolution / 16)
        trainData.append(vData)
        print 'len vData', len(vData)
        if doRewrite:
            midiKeras.midiOut(vData, 'midi/rewrite/' + path.basename(f), resolution)

    testData = []
    for f in testFiles:
        print f
        (notes, resolution) = midiKeras.midiRip(f)
        vData = midiKeras.vocabNotes(notes, resolution / 16)
        testData.append(vData)
        print 'len vData', len(vData)
        if doRewrite:
            midiKeras.midiOut(vData, 'midi/rewrite/' + path.basename(f), resolution)

    #print 'vocab', midiKeras.vocab
    print 'len vocab', len(midiKeras.vocab)
    with open(path.join('keras_models', 'vocab'), 'w') as f:
        f.write(pickle.dumps(midiKeras.vocab))

    if len(trainData) and not doRewrite:
        model = midiKeras.genModel()
        (fTrainData, fTrainLabels) = midiKeras.formatData(trainData, 128, 512)
        if len(testData):
            (fTestData, fTestLabels) = midiKeras.formatData(testData, 128, 512)
            earlyStopping = EarlyStopping(monitor = 'val_loss', mode = 'min')
            model.fit(fTrainData, fTrainLabels, nb_epoch = 10, batch_size = 32, validation_data = (fTestData, fTestLabels), callbacks = [earlyStopping])
        else:
            model.fit(fTrainData, fTrainLabels, nb_epoch = 10, batch_size = 32)
