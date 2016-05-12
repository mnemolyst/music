import midi
import glob
import sys
import random
from os import path

import keras
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, LSTM, Embedding, Activation
from keras.optimizers import SGD
from keras.utils.np_utils import to_categorical

NOTE_ON = 0
NOTE_OFF = 1
NOTE_HOLD = 2
NOTE_REAR = 3 # rearticulate
NOTE_BLIP = 4

keyMap = {
    'bwv772.mid': 72,
    'bwv773.mid': 72,
    'bwv774.mid': 74,
    'bwv775.mid': 74,
    'bwv776.mid': 75,
    'bwv777.mid': 76,
    'bwv778.mid': 76,
    'bwv779.mid': 77,
    'bwv780.mid': 77,
    'bwv781.mid': 79,
    'bwv782.mid': 79,
    'bwv783.mid': 69,
    'bwv784.mid': 69,
    'bwv785.mid': 70,
    'bwv786.mid': 71,
    'abroad_.mid':  77, # f maj
    'air_.mid':     77, # f maj
    'alaurie_.mid': 72, # c maj
    'alie_.mid':    76, # e min
    'argyle_.mid':  78, # f# maj
    'baliff_.mid':  74, # d maj
    'ballycopyright_1.mid': 74, # d maj
    'ballycopyright_2.mid': 74, # d maj
    'ballycopyright_3.mid': 74, # d maj
    'bluebell_1.mid': 71, # b min
    'bluebell_2.mid': 71, # b min
    'bluebell_3.mid': 71, # b min
    'meadow1_.mid':   78, # f# maj
    'meadow2_.mid':   74, # d maj
    'undaunt_.mid':   75, # eb maj
}
vocab = [None]
model = None
resolution = None
RES = None

def stripOnes(l):
    startIdx = 0
    stopIdx = len(l)
    for i in range(len(l)):
        if l[i] != 1:
            startIdx = i
            break
    for i in reversed(range(len(l))):
        if l[i] != 1:
            stopIdx = i + 1
            break
    return l[startIdx:stopIdx]

def midiRip(midiFile):
    global keyMap, vocab, resolution, RES
    pattern = midi.read_midifile(midiFile)
    resolution = pattern.resolution
    RES = resolution / 16
    if path.basename(midiFile) in keyMap:
        offset = keyMap[path.basename(midiFile)]
    else:
        raise Exception('no offset')
        offset = 0

    pData = []
    lastNoteEnd = 0
    notes = []
    for t in pattern:
        time = 0
        notesOn = {}
        for e in t:
            #print e
            time += e.tick
            if isinstance(e, midi.NoteOnEvent) and e.velocity > 0:
                key = (e.channel, e.pitch - offset)
                notesOn[key] = time
            elif isinstance(e, midi.NoteOffEvent) or (isinstance(e, midi.NoteOnEvent) and e.velocity == 0):
                key = (e.channel, e.pitch - offset)
                if key in notesOn:
                    notes.append({
                        'start': notesOn[key],
                        'stop': time,
                        'pitch': e.pitch - offset,
                    })
                    if lastNoteEnd < time:
                        lastNoteEnd = time

    eData = []
    for i in range(lastNoteEnd / RES + 1):
        eData.append({})
    for note in notes:
        startIdx = note['start'] / RES
        stopIdx = note['stop'] / RES
        if startIdx == stopIdx:
            eData[startIdx][note['pitch']] = NOTE_BLIP
        else:
            if startIdx in eData and eData[startIdx] == NOTE_OFF:
                eData[startIdx][note['pitch']] = NOTE_REAR
            else:
                eData[startIdx][note['pitch']] = NOTE_ON

            for i in range(startIdx + 1, stopIdx):
                eData[i][note['pitch']] = NOTE_HOLD

            if stopIdx in eData and eData[stopIdx] == NOTE_ON:
                eData[stopIdx][note['pitch']] = NOTE_REAR
            else:
                eData[stopIdx][note['pitch']] = NOTE_OFF
    for e in eData:
        if e in vocab:
            k = vocab.index(e)
        else:
            vocab.append(e.copy())
            k = len(vocab) - 1
        pData.append(k)
    return stripOnes(pData)

def midiOut(tData, fileName):
    global vocab, resolution, RES
    outPattern = midi.Pattern()
    outPattern.resolution = resolution
    track = midi.Track()
    track.append(midi.TrackNameEvent(tick=0, text='JOSH'))
    track.append(midi.SetTempoEvent(tick=0, bpm=120))
    tick = 0
    for k in tData:
        e = vocab[k]
        tick += RES
        for f in e:
            if e[f] == NOTE_ON:
                track.append(midi.NoteOnEvent(pitch = f, tick = tick, velocity = 127))
                tick = 0
            elif e[f] == NOTE_OFF:
                track.append(midi.NoteOffEvent(pitch = f, tick = tick, velocity = 127))
                tick = 0
            elif e[f] == NOTE_HOLD:
                pass
            elif e[f] == NOTE_REAR:
                track.append(midi.NoteOffEvent(pitch = f, tick = tick, velocity = 127))
                track.append(midi.NoteOnEvent(pitch = f, tick = 0, velocity = 127))
                tick = 0
            elif e[f] == NOTE_BLIP:
                raise Exception('BLIP')
                #track.append(midi.NoteOnEvent(pitch = f, tick = 0.25 * tick))
                #track.append(midi.NoteOffEvent(pitch = f, tick = 0.5 * tick))
    track.append(midi.EndOfTrackEvent(tick = 0))
    outPattern.append(track)
    midi.write_midifile(fileName, outPattern)

def formatData(data, minSeq, maxSeq):
    global vocab, model
    nData = sum([(min(maxSeq + 1, len(x)) - minSeq) + (len(x) - maxSeq - 1) for x in data])# * 2
    fData = np.zeros((nData, maxSeq))
    fLabels = np.zeros((nData, 1))
    p = 0
    for i in data:
        for j in range(minSeq, min(maxSeq + 1, len(i))):
            fData[p, :j] = i[:j]
            fLabels[p] = i[j]
            #fData[p + 1, :j] = [x for x in reversed(i[-j:])]
            #fLabels[p + 1] = i[-j - 1]
            p += 1
        for j in range(len(i) - maxSeq - 1):
            fData[p] = i[j + 1 : maxSeq + j + 1]
            fLabels[p] = i[maxSeq + j + 1]
            p += 1
    fLabels = to_categorical(fLabels.astype('int'), len(vocab) - 1)
    return (fData, fLabels)

def genModel():
    global vocab, model
    model = Sequential()
    model.add(Embedding(len(vocab) - 1, 64, mask_zero = True))
    model.add(LSTM(64))
    model.add(Dense(len(vocab) - 1))
    model.add(Activation('softmax'))
    sgd = SGD(lr = 0.1, decay = 1e-6, momentum = 0.9, nesterov = True)
    model.compile(loss = 'categorical_crossentropy', optimizer = sgd)

def train(data, labels, nb_epoch = 1):
    global model
    model.fit(data, labels, nb_epoch = nb_epoch, batch_size = 16)

def test(data, labels):
    global model
    return model.evaluate(data, labels, batch_size = 16)

doMidiOut = False
isTrainFile = True
trainFiles = []
testFiles = []
for arg in sys.argv[1:]:
    if arg == 'train':
        isTrainFile = True
    elif arg == 'test':
        isTrainFile = False
    elif arg == 'rewrite':
        doMidiOut = True
    elif path.exists(arg):
        if isTrainFile:
            trainFiles.append(arg)
        else:
            testFiles.append(arg)

trainData = []
for f in trainFiles:
    print f
    pData = midiRip(f)
    trainData.append(pData)
    #print pData
    print 'len pData', len(pData)
    #print vocab
    print 'len vocab', len(vocab)
    if doMidiOut:
        midiOut(pData, 'midi/rewrite/' + path.basename(f))

testData = []
for f in testFiles:
    print f
    pData = midiRip(f)
    testData.append(pData)
    #print pData
    print 'len pData', len(pData)
    #print vocab
    print 'len vocab', len(vocab)
    if doMidiOut:
        midiOut(pData, 'midi/rewrite/' + path.basename(f))

if len(trainData):
    genModel()
    (fData, fLabels) = formatData(trainData, 16, 256)
    train(fData, fLabels)

if len(testData):
    (fData, fLabels) = formatData(testData, 16, 256)
    testScore = test(fData, fLabels)
    print testScore
