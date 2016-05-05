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

    pData = []
    for t in pattern:
        tData = []
        time = 0
        lastRes = 0
        atLast = {}
        for e in t:
            time += e.tick
            elapsed = time - lastRes
            print '\ne', e

            if elapsed >= RES and atLast:
                n = elapsed / RES
                r = elapsed % RES
                lastRes = time - r
                held = {k: NOTE_HOLD for k in atLast if atLast[k] in [NOTE_ON, NOTE_HOLD, NOTE_REAR]}
                #print 'n', n

                #print 'atLast', atLast
                if atLast in vocab:
                    k = vocab.index(atLast)
                    #print 'exist', k, atLast
                else:
                    vocab.append(atLast.copy())
                    k = len(vocab) - 1
                    #print 'new', k, atLast
                tData.append(k)

                #print 'held', held
                if n > 1 and held:
                    if held in vocab:
                        k = vocab.index(held)
                        #print 'exist', k, held
                    else:
                        vocab.append(held.copy())
                        k = len(vocab) - 1
                        #print 'new', k, held
                    tData += [k] * (n - 1)

                atLast = held
                #print '\ttData', tData

            if isinstance(e, midi.NoteOnEvent):
                if e.pitch not in atLast:
                    atLast[e.pitch] = NOTE_ON
                elif atLast[e.pitch] in [NOTE_ON, NOTE_BLIP]:
                    atLast[e.pitch] = NOTE_ON
                elif atLast[e.pitch] in [NOTE_OFF, NOTE_HOLD, NOTE_REAR]:
                    atLast[e.pitch] = NOTE_REAR
            elif isinstance(e, midi.NoteOffEvent):
                if e.pitch not in atLast:
                    pass
                elif atLast[e.pitch] == [NOTE_ON, NOTE_BLIP]:
                    atLast[e.pitch] = NOTE_BLIP
                elif atLast[e.pitch] in [NOTE_OFF, NOTE_HOLD, NOTE_REAR]:
                    atLast[e.pitch] = NOTE_OFF

        pData.append(tData)
    #print 'vocab', vocab
    outPattern = midi.Pattern()
    outPattern.resolution = pattern.resolution
    track = midi.Track()
    track.append(midi.TrackNameEvent(tick=0, text='JOSH'))
    for e in pData[1]:
        tick = RES
        for f in vocab[e]:
            if vocab[e][f] == NOTE_ON:
                track.append(midi.NoteOnEvent(pitch = f, tick = tick, velocity = 127))
            elif vocab[e][f] == NOTE_OFF:
                track.append(midi.NoteOffEvent(pitch = f, tick = tick, velocity = 0))
            elif vocab[e][f] == NOTE_HOLD:
                pass
            elif vocab[e][f] == NOTE_REAR:
                track.append(midi.NoteOnEvent(pitch = f, tick = tick, velocity = 127))
            elif vocab[e][f] == NOTE_BLIP:
                print 'blip'
                #track.append(midi.NoteOnEvent(pitch = f, tick = 0.25 * tick))
                #track.append(midi.NoteOffEvent(pitch = f, tick = 0.5 * tick))
            tick = 0
    track.append(midi.EndOfTrackEvent(tick = 0))
    outPattern.append(track)
    midi.write_midifile('test.mid', outPattern)
