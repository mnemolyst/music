import midi
import glob
import sys
import random
from os import path
import json

import keras
import numpy as np
from keras.models import Sequential, Model, model_from_json
from keras.layers import Input, Embedding, LSTM, Dense, Activation, Highway
#from keras.optimizers import RMSprop
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

class MidiKeras:
    def __init__(self, vocab = [None, {}]):
        self.vocab = vocab

    def stripSilence(self, l, silence):
        startIdx = 0
        stopIdx = len(l)
        for i in range(len(l)):
            if l[i] != silence:
                startIdx = i
                break
        for i in reversed(range(len(l))):
            if l[i] != silence:
                stopIdx = i + 1
                break
        return l[startIdx:stopIdx]

    def midiRip(self, midiFile):
        global keyMap
        pattern = midi.read_midifile(midiFile)
        if path.basename(midiFile) in keyMap:
            offset = keyMap[path.basename(midiFile)] - 69
        else:
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
                            't': notesOn[key],
                            'd': time - notesOn[key],
                            'n': e.pitch - offset,
                        })
        return (notes, pattern.resolution)

    def vocabDiff(self, v, e):
        d1 = len(set(v.keys()) - set(e.keys()))
        d2 = len(set(e.keys()) - set(v.keys()))
        d3 = sum([v[i] != e[i] for i in set(v.keys()).intersection(set(e.keys()))])
        return (d1 + d2) * 100 + d1 * 10 + d3

    def notesLimits(self, notes):
        firstTime = None
        lastTime = None
        for note in notes:
            if firstTime == None or note['t'] < firstTime:
                firstTime = note['t']
            if lastTime == None or lastTime < note['t'] + note['d']:
                lastTime = note['t'] + note['d']
        return (firstTime, lastTime)

    def vocabularize(self, notes, res, limitTime = None, addNew = True, missed = None):
        (firstTime, lastTime) = self.notesLimits(notes)
        if limitTime != None:
            if lastTime < limitTime:
                lastTime = limitTime
            if limitTime < firstTime:
                firstTime = limitTime

        smallestBad = None
        largestGood = None
        goodEData = None
        while True:
            eData = []
            print 'res', res
            for i in range((lastTime - firstTime) / res + 1):
                eData.append({})
            for note in notes:
                startIdx = (note['t'] - firstTime) / res
                stopIdx = (note['t'] + note['d'] - firstTime) / res

                if note['n'] not in eData[startIdx]:
                    eData[startIdx][note['n']] = []
                e = (NOTE_ON, note['t'] - firstTime - startIdx * res)
                if e not in eData[startIdx][note['n']]:
                    eData[startIdx][note['n']].append(e)

                for i in range(startIdx + 1, stopIdx):
                    if note['n'] not in eData[i]:
                        eData[i][note['n']] = []
                    e = (NOTE_HOLD, 0)
                    if e not in eData[i][note['n']]:
                        eData[i][note['n']].append(e)

                if note['n'] not in eData[stopIdx]:
                    eData[stopIdx][note['n']] = []
                e = (NOTE_OFF, note['t'] + note['d'] - firstTime - stopIdx * res)
                if e not in eData[stopIdx][note['n']]:
                    eData[stopIdx][note['n']].append(e)

            lens = {}
            for e in eData:
                for n in e:
                    l = len(e[n])
                    if l not in lens:
                        lens[l] = 0
                    lens[l] += 1
            r = float(sum([lens[x] for x in lens if x > 1])) / sum([lens[x] for x in lens])
            print 'lens', lens
            print 'r', r
            if r > 0.1 and res >= 2:
                if smallestBad == None or res < smallestBad:
                    smallestBad = res
                res /= 2
            else:
                if largestGood == None or res > largestGood:
                    largestGood = res
                res *= 2
                goodEData = eData

            if smallestBad and largestGood and goodEData and smallestBad == largestGood * 2:
                eData = goodEData
                break

        vData = []
        idx = 0
        for e in eData:
            for p in e:
                e[p] = [x[0] for x in sorted(e[p], key = lambda y: y[1])]
            if e in self.vocab:
                k = self.vocab.index(e)
            elif addNew:
                self.vocab.append(e.copy())
                k = len(self.vocab) - 1
            else:
                a = [(i, self.vocabDiff(x, e)) for i, x in enumerate(self.vocab) if i > 0]
                a.sort(key = lambda x: x[1])
                k = a[0][0]
                if missed != None:
                    missed[0] += 1
                #print 'unknown, maybe', [(x[0], self.vocab[x[0]]) for x in a[:3]]
                #print 'idx', idx, 'e', e, 'vocab[k]', self.vocab[k]
            idx += 1
            vData.append(k)

        return vData

    def predictSequence(self, model, data, num = 1):
        inSeq = data[:]
        out = []
        while len(out) < num:
            modelIn = np.array(inSeq).reshape((1, -1))
            modelOut = model.predict(modelIn, batch_size = 1)
            inSeq.append(np.argmax(modelOut, 1))
            if out == []:
                out = modelOut
            else:
                out = np.append(out, modelOut, 0)
        return out

    def tryResVocab(self, notes, baseRes):
        vData = []
        return self.vocabularize(notes, int(baseRes), addNew = False)
        #missed = [0, 0, 0]
        #vData.append(self.vocabularize(notes, int(baseRes * 0.9), addNew = False, missed = missed))
        #missed = missed[1:] + [missed[0] * 0.9]
        #vData.append(self.vocabularize(notes, int(baseRes), addNew = False, missed = missed))
        #missed = missed[1:] + missed[:1]
        #vData.append(self.vocabularize(notes, int(baseRes * 1.1), addNew = False, missed = missed))
        #missed = missed[1:] + [missed[0] * 1.1]
        #statsArgMin = min(enumerate(missed), key = lambda x: x[1])[0]
        #return vData[statsArgMin]

    def midiOut(self, vData, fileName, resolution):
        outPattern = midi.Pattern()
        outPattern.resolution = resolution
        track = midi.Track()
        track.append(midi.TrackNameEvent(tick=0, text='JOSH'))
        track.append(midi.SetTempoEvent(tick=0, bpm=120))
        tick = 0
        for k in tData:
            e = self.vocab[k]
            tick += res
            l = max([len(e[x]) for x in e])
            for t in range(l):
                if tick == 0:
                    tick = res / l
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

    # for non-stateful RNNs
    #def formatData(self, data, minSeq, maxSeq):
    #    nData = sum([(min(maxSeq + 1, len(x)) - minSeq) + (len(x) - maxSeq - 1) for x in data]) * 2
    #    fData = np.zeros((nData, maxSeq))
    #    fLabels = np.zeros((nData, 1))
    #    p = 0
    #    for i in data:
    #        for j in range(minSeq, min(maxSeq + 1, len(i))):
    #            fData[p, :j] = i[:j]
    #            fLabels[p] = i[j]

    #            fData[p + 1, :j] = list(reversed(i[-j:]))
    #            fLabels[p + 1] = i[-j - 1]
    #            p += 2
    #        for j in range(1, len(i) - maxSeq):
    #            fData[p] = i[j : maxSeq + j]
    #            fLabels[p] = i[maxSeq + j]

    #            fData[p + 1] = list(reversed(i[-maxSeq - j : -j]))
    #            fLabels[p + 1] = i[-maxSeq - j - 1]
    #            p += 2
    #    fLabels = to_categorical(fLabels.astype('int'), len(self.vocab))
    #    return (fData, fLabels)

    # for stateful RNNs
    def formatData(self, data):
        d1 = len(data)
        d2 = max([len(x) for x in data]) - 1
        d3 = len(self.vocab)
        fData =   np.zeros((d1, d2), dtype='int32')
        fLabels = np.zeros((d1, d2, d3), dtype='int32')
        for i, t in enumerate(data):
            fData[i, :len(t) - 1] = t[:-1]
            fLabels[i, :len(t) - 1, :] = to_categorical([[x] for x in t[1:]], d3)
        fData = np.reshape(fData.T, (d1 * d2, 1))
        fLabels = np.reshape(np.transpose(fLabels, (1, 0, 2)), (d1 * d2, d3))
        return (fData, fLabels)

    def genModel(self, batchShape):
        model = Sequential()
        model.add(Embedding(len(self.vocab), 32, mask_zero = True, batch_input_shape = batchShape))
        #model.add(LSTM(5, return_sequences = True, stateful = True))
        model.add(LSTM(32, stateful = True))
        for i in range(10):
            model.add(Highway( ))
        model.add(Dense(len(self.vocab), activation = 'softmax'))
        model.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])
        return model

    def rebatchModel(self, model, newBatch):
        struct = json.loads(model.to_json())
        for l in struct['config']:
            if 'batch_input_shape' in l['config']:
                l['config']['batch_input_shape'][0] = newBatch
        model2 = model_from_json(json.dumps(struct))
        return model2

#mk = MidiKeras(range(40))
#(b, c) = mk.formatData([range(30),range(4,34)])
#model = mk.genModel((2, 1))
#for i in range(100):
#    for j in range(len(b[0,:,0])):
#        model.train_on_batch(b[:,j,:], c[:,j,:])
#    print i
#    model.reset_states()
