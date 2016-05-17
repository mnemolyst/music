from os import path
import pickle
import json
import sys
sys.path.insert(1, '..')
import midiKeras as mk
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
    with open(path.join(modelDir, 'model_def.json')) as f:
        model = model_from_json(f.read())
    model.load_weights(path.join(modelDir, '15-may-2021.h5'))
    rms = RMSprop(lr = 0.001)
    model.compile(optimizer = rms, loss = 'categorical_crossentropy', metrics = ['accuracy'])
    with open(path.join(modelDir, 'vocab')) as f:
        vocab = pickle.loads(f.read())
    # TODO reconcile not-seen music events with existing vocab
    data = json.loads(request.data)
    notes = data['notes']
    midiKeras = mk.MidiKeras(384 / 16)
    print len(vocab)
    (vData, vocab) = midiKeras.vocabNotes(notes, vocab)
    print len(vocab)
    print vData
    modelOut = model.predict(vData, batch_size = 32)
    print modelOut
    return 'hello'

if __name__ == '__main__':
    app.run(debug = True)
