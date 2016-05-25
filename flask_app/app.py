from os import path
import pickle
import json
import sys
sys.path.insert(1, '..')
import midiKeras as mk
import numpy as np
from keras.models import model_from_json
from keras.optimizers import RMSprop
from flask import Flask, render_template, request
from pymongo import MongoClient
from bson.objectid import ObjectId
app = Flask(__name__)

@app.route('/')
def index():
    client = MongoClient()
    db = client.music
    collection = db.composition
    return render_template('index.jinja', compositions = collection.find())

@app.route('/composition/<compositionId>', methods = ['GET'])
def getComposition(compositionId):
    client = MongoClient()
    db = client.music
    collection = db.composition
    composition = collection.find_one({'_id': ObjectId(compositionId)})
    del composition['_id']
    return json.dumps(composition)

@app.route('/composition', methods = ['POST'])
def newComposition():
    client = MongoClient()
    db = client.music
    collection = db.composition
    composition = json.loads(request.data)
    collection_id = collection.insert_one(composition).inserted_id
    return str(collection_id)

#@app.route('/composition/<compositionId>', methods = ['POST'])
#def postComposition(compositionId):
#    client = MongoClient()
#    db = client.music
#    collection = db.composition

@app.route('/suggest', methods = ['POST'])
def suggest():
    modelDir = path.join('..', 'keras_models')
    pathPrefix = path.join(modelDir, '25-May-17-32')
    with open(pathPrefix + '-struct.json') as f:
        model = model_from_json(f.read())
    model.load_weights(pathPrefix + '-weights.h5')
    model.compile(optimizer = RMSprop(), loss = 'categorical_crossentropy', metrics = ['accuracy'])
    with open(pathPrefix + '-vocab.pickle') as f:
        vocab = pickle.loads(f.read())
    midiKeras = mk.MidiKeras(vocab)

    data = json.loads(request.data)
    notes = [{'t': x['t'] * 24, 'd': x['d'] * 24, 'n': int(x['n']) + 69} for x in data['notes']]
    #print data['limits']
    limits = [data['limits'][0] * 24, data['limits'][1] * 24, data['limits'][2], data['limits'][3]]
    #print 'limits', limits
    noteDs = np.array([x['d'] for x in notes])
    res = np.round(np.mean(noteDs) - np.std(noteDs))
    #print 'mean', np.mean(noteDs), 'std', np.std(noteDs), 'res', res
        
    forwardNotes = [n for n in notes if n['t'] < limits[0]]
    vData = midiKeras.vocabularize(forwardNotes, int(res), limitTime = int(limits[0]), addNew = False)
    #print 'fwd vData', vData
    fwdProb = midiKeras.predictSequence(model, vData, int((limits[1] - limits[0]) / res))
    #print 'fwd prob', fwdProb.shape, fwdProb

    backwardNotes = [n for n in notes if limits[1] < n['t'] + n['d']]
    if backwardNotes:
        vData = midiKeras.vocabularize(backwardNotes, int(res), limitTime = int(limits[1]), addNew = False)
        vData = list(reversed(vData))
        #print 'bkwd vData', vData
        bkwdProb = midiKeras.predictSequence(model, vData, int((limits[1] - limits[0]) / res))
        bkwdProb = np.fliplr(bkwdProb)
        #print 'bkwd prob', bkwdProb.shape, bkwdProb
    else:
        bkwdProb = np.zeros(fwdProb.shape)

    prediction = []
    #for t in fwdProb:
    #    print 't', t.shape, t
    #    print 'fwd max', np.argmax(t)
    #for t in bkwdProb:
    #    print 't', t.shape, t
    #    print 'bkwd max', np.argmax(t)
    for t in fwdProb + bkwdProb:
        #print 't', t.shape, t
        #print 'max', np.argmax(t)
        prediction.append(np.argmax(t))
    print prediction

    newNotes = []
    notesOn = {}
    time = np.floor(limits[0] / res) * res
    for k in prediction:
        print 'time', time
        e = midiKeras.vocab[k]
        print 'e', e
        for n in e:
            for i, w in enumerate(e[n]):
                if w == mk.NOTE_ON or (w == mk.NOTE_HOLD and n not in notesOn):
                    notesOn[n] = time + (i * len(e[n]) / res)
                elif w == mk.NOTE_OFF:
                    if n in notesOn:
                        print 't', int(notesOn[n])
                        print 'd', int(time - notesOn[n])
                        print 'n', n
                        newNotes.append({
                            't': int(notesOn[n] / 24),
                            'd': int((time - notesOn[n]) / 24),
                            'n': n - 69,
                        })
                        del notesOn[n]
        time += res
    for n in notesOn:
        print 't', int(notesOn[n])
        print 'd', int(time - notesOn[n])
        print 'n', n
        newNotes.append({
            't': int(notesOn[n] / 24),
            'd': int((time - notesOn[n]) / 24),
            'n': n - 69,
        })

    return json.dumps(newNotes)

if __name__ == '__main__':
    app.run(debug = True)
