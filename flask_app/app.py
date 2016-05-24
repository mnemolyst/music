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
    with open(path.join(modelDir, '20-May-17-10-struct.json')) as f:
        model = model_from_json(f.read())
    model.load_weights(path.join(modelDir, '20-May-17-10-weights.h5'))
    model.compile(optimizer = RMSprop(), loss = 'binary_crossentropy', metrics = ['accuracy'])
    with open(path.join(modelDir, '20-May-14:51-vocab.pickle')) as f:
        vocab = pickle.loads(f.read())
    midiKeras = mk.MidiKeras(vocab)

    data = json.loads(request.data)
    notes = [{'t': x['t'] * 24, 'd': x['d'] * 24, 'n': int(x['n']) + 69} for x in data['notes']]
    print data['limits']
    limits = [data['limits'][0] * 24, data['limits'][1] * 24, data['limits'][2], data['limits'][3]]
    print limits
    noteDs = np.array([x['d'] for x in notes])
    res = np.round(np.mean(noteDs) - np.std(noteDs))
    #print 'mean', np.mean(noteDs), 'std', np.std(noteDs), 'res', res
        
    forwardNotes = [n for n in notes if n['t'] < limits[0]]
    vData = midiKeras.vocabularize(forwardNotes, res, limitTime = limits[0], addNew = False)

    modelIn = np.array(vData).reshape((1, -1))
    #print 'modelIn shape', modelIn.shape
    #print 'modelIn', [midiKeras.vocab[x] for x in modelIn[0]]
    modelOut = model.predict(modelIn, batch_size = 1)
    #print 'modelOut', modelOut
    #bestOut = np.argmax(modelOut, 1)
    #print 'best', bestOut, modelOut[0][bestOut]
    prediction = [i for i, x in enumerate(modelOut[0]) if x > 0.5]
    print 'prediction', prediction
    return json.dumps(prediction)

if __name__ == '__main__':
    app.run(debug = True)
