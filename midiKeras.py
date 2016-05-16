import midi
import glob
import sys
import random
import json
from os import path

import keras
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, LSTM, Embedding, Activation
from keras.optimizers import RMSprop
from keras.callbacks import EarlyStopping
from keras.utils.np_utils import to_categorical

NOTE_ON = 0
NOTE_HOLD = 1
NOTE_OFF = 2

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
    'alaurie_.mid': 72, # c# maj
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
    'aberdovy_.mid':  79, # g maj
    'alicegry_.mid':  71, # b maj
    'billyboy_.mid':  72, # c maj
    'billyeng_.mid':  77, # f maj
    'billyire_.mid':  75, # eb maj
    'blackhair_1.mid': 76, # e min
    'blackhair_2.mid': 76, # e min
    'blackhair_3.mid': 76, # e min
    'blackhair_4.mid': 76, # e min
    'blowind_.mid':    79, # g maj
    'boldsold_.mid':   74, # d maj
    'candles_.mid':    74, # d min
    'charms_.mid':     72, # c min
    'lesley_.mid':     77, # f maj
    'susan_.mid':      80, # ab min
}
vocab = [None]
model = None
resolution = None
RES = None

def stripSilence(l):
    global vocab
    if {} in vocab:
        sIdx = vocab.index({})
    else:
        return l

    startIdx = 0
    stopIdx = len(l)
    for i in range(len(l)):
        if l[i] != sIdx:
            startIdx = i
            break
    for i in reversed(range(len(l))):
        if l[i] != sIdx:
            stopIdx = i + 1
            break
    return l[startIdx:stopIdx]

def midiRip(midiFile):
    global keyMap, resolution, RES
    pattern = midi.read_midifile(midiFile)
    resolution = pattern.resolution
    RES = resolution / 16
    if not doRewrite and path.basename(midiFile) in keyMap:
        offset = keyMap[path.basename(midiFile)]
    else:
        if not doRewrite:
            raise Exception('no offset')
        offset = 0

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
    return notes

def vocabNotes(notes):
    global RES, vocab
    firstTime = None
    lastTime = None
    for note in notes:
        if firstTime == None or note['start'] < firstTime:
            firstTime = note['start']
        if lastTime == None or lastTime < note['stop']:
            lastTime = note['stop']

    eData = []
    for i in range((lastTime - firstTime) / RES + 1):
        eData.append({})
    for note in notes:
        startIdx = (note['start'] - firstTime) / RES
        stopIdx = (note['stop'] - firstTime) / RES

        if note['pitch'] not in eData[startIdx]:
            eData[startIdx][note['pitch']] = []
        e = (NOTE_ON, note['start'] - firstTime - startIdx * RES)
        if e not in eData[startIdx][note['pitch']]:
            eData[startIdx][note['pitch']].append(e)

        for i in range(startIdx + 1, stopIdx):
            if note['pitch'] not in eData[i]:
                eData[i][note['pitch']] = []
            e = (NOTE_HOLD, 0)
            if e not in eData[i][note['pitch']]:
                eData[i][note['pitch']].append(e)

        if note['pitch'] not in eData[stopIdx]:
            eData[stopIdx][note['pitch']] = []
        e = (NOTE_OFF, note['stop'] - firstTime - stopIdx * RES)
        if e not in eData[stopIdx][note['pitch']]:
            eData[stopIdx][note['pitch']].append(e)

    vData = []
    for e in eData:
        for p in e:
            e[p] = [x[0] for x in sorted(e[p], key = lambda y: y[1])]
        if e in vocab:
            k = vocab.index(e)
        else:
            vocab.append(e.copy())
            k = len(vocab) - 1
        vData.append(k)
    vData = stripSilence(vData)
    return vData

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
        l = max([len(e[x]) for x in e])
        for t in range(l):
            if tick == 0:
                tick = RES / l
            for f in e:
                if t < len(e[f]):
                    if e[f][t] == NOTE_ON:
                        track.append(midi.NoteOnEvent(pitch = f, tick = tick, velocity = 127))
                        tick = 0
                    elif e[f][t] == NOTE_OFF:
                        track.append(midi.NoteOffEvent(pitch = f, tick = tick, velocity = 127))
                        tick = 0
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
    fLabels = to_categorical(fLabels.astype('int'), len(vocab))
    return (fData, fLabels)

def genModel():
    global vocab, model
    model = Sequential()
    model.add(Embedding(len(vocab), 64, mask_zero = True))
    model.add(LSTM(128))
    model.add(Dense(128))
    model.add(Dense(len(vocab)))
    model.add(Activation('softmax'))
    rms = RMSprop(lr = 0.001)
    model.compile(loss = 'categorical_crossentropy', optimizer = rms)

doRewrite = False
isTrainFile = True
doPredict = False
trainFiles = []
testFiles = []
for arg in sys.argv[1:]:
    if arg == 'train':
        isTrainFile = True
    elif arg == 'test':
        isTrainFile = False
    elif arg == 'rewrite':
        doRewrite = True
    elif arg == 'predict':
        doPredict = True
    elif path.exists(arg):
        if isTrainFile:
            trainFiles.append(arg)
        else:
            testFiles.append(arg)

trainData = []
for f in trainFiles:
    print f
    vData = vocabNotes(midiRip(f))
    trainData.append(pData)
    #print pData
    print 'len pData', len(pData)
    #print vocab
    print 'len vocab', len(vocab)
    if doRewrite:
        midiOut(pData, 'midi/rewrite/' + path.basename(f))

testData = []
for f in testFiles:
    print f
    vData = vocabNotes(midiRip(f))
    testData.append(pData)
    #print pData
    print 'len pData', len(pData)
    #print vocab
    print 'len vocab', len(vocab)
    if doRewrite:
        midiOut(pData, 'midi/rewrite/' + path.basename(f))

if doPredict:
    notesJson = json.load(sys.stdin)
    with open(sys.stdout, 'w') as f:
        f.write(notesJson)

if len(trainData) and not doRewrite:
    genModel()
    (fTrainData, fTrainLabels) = formatData(trainData, 128, 512)
    if len(testData):
        (fTestData, fTestLabels) = formatData(testData, 128, 512)
        earlyStopping = EarlyStopping(monitor = 'val_loss', mode = 'min')
        model.fit(fTrainData, fTrainLabels, nb_epoch = 10, batch_size = 32, validation_data = (fTestData, fTestLabels), callbacks = [earlyStopping])
    else:
        model.fit(fTrainData, fTrainLabels, nb_epoch = 10, batch_size = 32)
