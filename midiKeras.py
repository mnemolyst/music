import midi
import glob
import sys

NOTE_ON = 0
NOTE_OFF = 1
NOTE_HOLD = 2
NOTE_REAR = 3 # rearticulate
NOTE_BLIP = 4

#import keras
#import numpy as np
#from keras.models import Sequential
#from keras.layers import Dense, Merge, LSTM, Embedding
#from keras.utils.np_utils import to_categorical
#
#data = np.random.randint(0, 2, (1000, 128))
#
#model = Sequential()
#model.add(LSTM(32))

midiFiles = glob.glob(sys.argv[1])
vocab = []
for f in midiFiles:
    pattern = midi.read_midifile(f)
    RES = pattern.resolution / 4

    # Collect tempo events
    #tempoEvents = []
    #for t in pattern:
    #    tick = 0
    #    for e in t:
    #        if isinstance(e, midi.SetTempoEvent):
    #            tempoEvents.append({'tick': tick + e.tick, 'bpm': e.bpm})
    #        tick += e.tick
    #tempoEvents.sort(key = lambda x: x['tick'])

    for t in pattern:
        tData = []
        time = 0
        lastRes = 0
        atLast = {}
        for e in t:
            time += e.tick
            elapsed = time - lastRes
            held = {k: NOTE_HOLD for k in atLast if atLast[k] in [NOTE_ON, NOTE_HOLD, NOTE_REAR]}
            print 'e', e
            print 'time', time
            print 'elapsed', elapsed
            print 'held', held

            if isinstance(e, midi.NoteOnEvent):
                if e.pitch not in atLast:
                    atLast[e.pitch] = NOTE_ON
                elif atLast[e.pitch] in [NOTE_OFF, NOTE_HOLD]:
                    atLast[e.pitch] = NOTE_REAR
                elif atLast[e.pitch] == NOTE_BLIP:
                    atLast[e.pitch] = NOTE_ON
            elif isinstance(e, midi.NoteOffEvent):
                if e.pitch not in atLast:
                    atLast[e.pitch] = NOTE_OFF
                elif atLast[e.pitch] == NOTE_ON:
                    atLast[e.pitch] = NOTE_BLIP
                elif atLast[e.pitch] in [NOTE_HOLD, NOTE_REAR]:
                    atLast[e.pitch] = NOTE_OFF

            if elapsed >= RES:
                n = elapsed / RES
                r = elapsed % RES
                print 'n', n
                print 'r', r
                lastRes = time - r
                print 'lastRes', lastRes

                if n > 1:
                    if held in vocab:
                        k = vocab.index(held)
                        print 'exist', k, held
                    else:
                        vocab.append(held)
                        k = len(vocab) - 1
                        print 'new', k, held
                    tData += [k] * (n - 1)

                if atLast in vocab:
                    k = vocab.index(atLast)
                    print 'exist', k, atLast
                else:
                    vocab.append(atLast)
                    k = len(vocab) - 1
                    print 'new', k, atLast
                tData.append(k)

        print 'tData', tData
    print 'vocab', vocab
