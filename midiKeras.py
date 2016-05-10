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
}
vocab = [None]
eData = []
resolution = None
RES = None

def midiRip(midiFile):
    global keyMap, vocab, resolution, RES
    pattern = midi.read_midifile(midiFile)
    resolution = pattern.resolution
    RES = resolution / 16
    if path.basename(midiFile) in keyMap:
        offset = keyMap[path.basename(midiFile)]
    else:
        offset = 0

    pData = []
    lastNoteEnd = 0
    notes = []
    for t in pattern:
        time = 0
        notesOn = {}
        for e in t:
            print e
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
    return pData

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
                track.append(midi.NoteOnEvent(pitch = f, tick = tick, velocity = 127))
                tick = 0
            elif e[f] == NOTE_BLIP:
                print 'blip'
                #track.append(midi.NoteOnEvent(pitch = f, tick = 0.25 * tick))
                #track.append(midi.NoteOffEvent(pitch = f, tick = 0.5 * tick))
    track.append(midi.EndOfTrackEvent(tick = 0))
    outPattern.append(track)
    midi.write_midifile(fileName, outPattern)

def train():
    global eData
    minSeq = 16
    maxSeq = 64
    #eData = [range(1,32),range(2,33),range(3,35)]
    #vocab = range(35)
    trainLen = len(eData) * max([min(maxSeq, len(x)) - minSeq for x in eData])# * 2
    trainData = np.zeros((trainLen, maxSeq))
    labels = np.zeros((trainLen, 1))
    p = 0
    for i in eData:
        for j in range(minSeq, min(maxSeq, len(i))):
            trainData[p, :j] = i[:j]
            labels[p] = i[j]
            #trainData[p + 1, :j] = [x for x in reversed(i[-j:])]
            #labels[p + 1] = i[-j - 1]
            p += 1

    model = Sequential()
    model.add(Embedding(len(vocab), 64, mask_zero = True))
    model.add(LSTM(64))
    model.add(Dense(len(vocab)))
    model.add(Activation('softmax'))
    sgd = SGD(lr = 0.1, decay = 1e-6, momentum = 0.9, nesterov = True)
    model.compile(loss = 'categorical_crossentropy', optimizer = sgd)
    labels = to_categorical(labels.astype('int'), len(vocab))
    model.fit(trainData, labels, nb_epoch = 100, batch_size = 16)

doTrain = False
doMidiOut = False
fileNames = []
for arg in sys.argv[1:]:
    if arg == 'train':
        doTrain = True
    elif arg == 'rewrite':
        doMidiOut = True
    else:
        fileNames.append(arg)

for f in fileNames:
    print f
    pData = midiRip(f)
    print pData
    print vocab
    print len(vocab)
    #pData.sort(key = lambda x: len(x))
    eData.append(pData[-1])
    if doMidiOut:
        midiOut(pData, 'midi/test/' + path.basename(f))
