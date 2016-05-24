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
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.jinja')

@app.route('/suggest', methods = ['POST'])
def suggest():
    modelDir = path.join('..', 'keras_models')
    with open(path.join(modelDir, '24-May-12:21-struct.json')) as f:
        model = model_from_json(f.read())
    model.load_weights(path.join(modelDir, '24-May-12:21-weights.h5'))
    model.compile(optimizer = RMSprop(), loss = 'categorical_crossentropy', metrics = ['accuracy'])
    with open(path.join(modelDir, '24-May-12:21-vocab.pickle')) as f:
        vocab = pickle.loads(f.read())
    midiKeras = mk.MidiKeras(vocab)

    data = json.loads(request.data)
    notes = [{'t': x['t'] * 24, 'd': x['d'] * 24, 'n': int(x['n']) + 69} for x in data['notes']]
    print data['limits']
    limits = [data['limits'][0] * 24, data['limits'][1] * 24, data['limits'][2], data['limits'][3]]
    print 'limits', limits
    noteDs = np.array([x['d'] for x in notes])
    res = np.round(np.mean(noteDs) - np.std(noteDs))
    #print 'mean', np.mean(noteDs), 'std', np.std(noteDs), 'res', res
        
    forwardNotes = [n for n in notes if n['t'] < limits[0]]
    vData = midiKeras.vocabularize(forwardNotes, int(res), limitTime = int(limits[0]), addNew = False)
    print 'fwd vData', vData
    fwdProb = midiKeras.predictSequence(model, vData, (limits[1] - limits[0]) / int(res))
    print 'fwd prob', fwdProb.shape, fwdProb

    backwardNotes = [n for n in notes if limits[1] < n['t'] + n['d']]
    vData = midiKeras.vocabularize(backwardNotes, int(res), limitTime = int(limits[1]), addNew = False)
    vData = list(reversed(vData))
    print 'bkwd vData', vData
    bkwdProb = midiKeras.predictSequence(model, vData, (limits[1] - limits[0]) / int(res))
    print 'bkwd prob', bkwdProb.shape, bkwdProb

    prediction = []
    for t in fwdProb:
        print 't', t.shape, t
        print 'fwd max', np.argmax(t)
    for t in bkwdProb:
        print 't', t.shape, t
        print 'bkwd max', np.argmax(t)
    for t in fwdProb + bkwdProb:
        print 't', t.shape, t
        print 'max', np.argmax(t)
        prediction.append(np.argmax(t))

    return json.dumps(prediction)

if __name__ == '__main__':
    app.run(debug = True)
