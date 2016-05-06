import midi
import glob
import sys
import random

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
}
midiFiles = sys.argv[1:]
vocab = []
data = []
for f in midiFiles:
    offset = keyMap[f]
    #offset = 0
    print f
    pattern = midi.read_midifile(f)
    RES = pattern.resolution / 4

    pData = []
    for t in pattern:
        tData = []
        time = 0
        lastRes = 0
        atLast = {}
        for e in t:
            time += e.tick
            elapsed = time - lastRes

            if elapsed >= RES and atLast:
                n = elapsed / RES
                r = elapsed % RES
                lastRes = time - r
                held = {k: NOTE_HOLD for k in atLast if atLast[k] in [NOTE_ON, NOTE_HOLD, NOTE_REAR]}

                if atLast in vocab:
                    k = vocab.index(atLast)
                else:
                    vocab.append(atLast.copy())
                    k = len(vocab) - 1
                tData.append(k)

                if n > 1 and held:
                    if held in vocab:
                        k = vocab.index(held)
                    else:
                        vocab.append(held.copy())
                        k = len(vocab) - 1
                    tData += [k] * (n - 1)

                atLast = held.copy()

            if isinstance(e, midi.NoteOnEvent):
                pitch = e.pitch - offset
                if pitch not in atLast:
                    atLast[pitch] = NOTE_ON
                elif atLast[pitch] in [NOTE_ON, NOTE_BLIP]:
                    atLast[pitch] = NOTE_ON
                elif atLast[pitch] in [NOTE_OFF, NOTE_HOLD, NOTE_REAR]:
                    atLast[pitch] = NOTE_REAR
            elif isinstance(e, midi.NoteOffEvent):
                pitch = e.pitch - offset
                if pitch not in atLast:
                    pass
                elif atLast[pitch] == [NOTE_ON, NOTE_BLIP]:
                    atLast[pitch] = NOTE_BLIP
                elif atLast[pitch] in [NOTE_OFF, NOTE_HOLD, NOTE_REAR]:
                    atLast[pitch] = NOTE_OFF

        pData.append(tData)
    #print len(vocab)
    pData.sort(key = lambda x: len(x))
    data.append(pData[-1])

model = Sequential()
model.add(Embedding(len(vocab), 64, mask_zero = True))
model.add(LSTM(64))
model.add(Dense(len(vocab)))
model.add(Activation('softmax'))
sgd = SGD(lr = 0.1, decay = 1e-6, momentum = 0.9, nesterov = True)
model.compile(loss = 'categorical_crossentropy', optimizer = sgd)
for i in range(100):
    for j in data:
        x = random.randrange(100, len(j))
        label = to_categorical(j[x:x], len(vocab))
        model.fit(data[:x], label, nb_epoch = 1, batch_size = 1)

    #outPattern = midi.Pattern()
    #outPattern.resolution = pattern.resolution
    #track = midi.Track()
    #track.append(midi.TrackNameEvent(tick=0, text='JOSH'))
    #track.append(midi.SetTempoEvent(tick=0, bpm=120))
    #tick = 0
    #for k in pData[1]:
    #    e = vocab[k]
    #    tick += RES
    #    for f in e:
    #        if e[f] == NOTE_ON:
    #            track.append(midi.NoteOnEvent(pitch = f, tick = tick, velocity = 127))
    #            tick = 0
    #        elif e[f] == NOTE_OFF:
    #            track.append(midi.NoteOffEvent(pitch = f, tick = tick, velocity = 0))
    #            tick = 0
    #        elif e[f] == NOTE_HOLD:
    #            pass
    #        elif e[f] == NOTE_REAR:
    #            track.append(midi.NoteOnEvent(pitch = f, tick = tick, velocity = 127))
    #            tick = 0
    #        elif e[f] == NOTE_BLIP:
    #            print 'blip'
    #            #track.append(midi.NoteOnEvent(pitch = f, tick = 0.25 * tick))
    #            #track.append(midi.NoteOffEvent(pitch = f, tick = 0.5 * tick))
    #track.append(midi.EndOfTrackEvent(tick = 0))
    #outPattern.append(track)
    #midi.write_midifile('test.mid', outPattern)
