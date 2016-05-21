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
    rms = RMSprop(lr = 0.001)
    model.compile(optimizer = rms, loss = 'binary_crossentropy', metrics = ['accuracy'])
    with open(path.join(modelDir, '20-May-14:51-vocab.pickle')) as f:
        vocab = pickle.loads(f.read())
    # TODO reconcile not-seen music events with existing vocab
    data = json.loads(request.data)
    notes = [{'t': x['t'], 'd': x['d'], 'n': int(x['n']) + 69} for x in data['notes']]
    midiKeras = mk.MidiKeras(vocab)
    vData = midiKeras.vocabNotes(notes, 384 / 128, False)
    modelIn = np.array(vData).reshape((1, -1))
    print 'modelIn shape', modelIn.shape
    print 'modelIn', modelIn
    modelOut = model.predict(modelIn, batch_size = 1)
    print 'modelOut shape', modelOut.shape
    print 'modelOut', modelOut
    print 'predict', [i for i, x in enumerate(modelOut[0]) if x > 0.5]
    return 'hello'

if __name__ == '__main__':
    app.run(debug = True)
