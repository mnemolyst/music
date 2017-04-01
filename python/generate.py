from os import path
from os.path import isfile
import sys
import pickle
import numpy as np
from keras.models import model_from_json, Sequential, Model
from keras.optimizers import RMSprop
import midiKeras as mk

if __name__ == '__main__':

    global model, vocab, midiKeras

    midiKeras  =  mk.MidiKeras( )
    for a in range( 12 ):
        for b in range( 12 ):
            for c in range( 5 ):
                for d in range( 5 ):
                    e = { a: c, b: d }
                    if e not in midiKeras.vocab:
                        midiKeras.vocab.append( e )

    numP  =  10

    # parse command line arguments
    i  =  1
    while i < len( sys.argv ):
        print i

        # switch on argument i
        if sys.argv[ i ]  ==  'model':

            pathPrefix  =  sys.argv[ i + 1 ]
            i  +=  1

            if isfile( pathPrefix + '-struct.json' ):

                print 'loading model definition'
                with open( pathPrefix + '-struct.json' ) as f:
                    model  =  model_from_json( f.read( ) )

                if isfile( pathPrefix + '-weights.h5' ):
                    print 'loading model weights'
                    model.load_weights( pathPrefix + '-weights.h5' )

                rmsProp  =  RMSprop( lr = 0.0001 )
                model.compile( optimizer = rmsProp, loss = 'categorical_crossentropy', metrics = [ 'accuracy' ] )

            if isfile( pathPrefix + '-vocab.pickle' ):

                print 'loading vocab'
                with open( pathPrefix + '-vocab.pickle' ) as f:
                    vocab  =  pickle.loads( f.read( ) )
                    midiKeras.setVocab( vocab )

        elif sys.argv[ i ]  ==  'input':

            inputFile  =  sys.argv[ i + 1 ]
            i  +=  1

            tracks  =  midiKeras.midiToEvents( inputFile )
            seq     =  tracks[ 0 ]
            print 'seq', seq

        elif sys.argv[ i ]  ==  'num':

            numP  =  sys.argv[ i + 1 ]
            i  +=  1

        i  +=  1

    t = 0
    while t  <  numP:
        zeroPitch  =  min( seq[ -1 ].keys( ) )
        seq        =  [ dict( [ ( p - zeroPitch, e[ p ] ) for p in e.keys( ) ] ) for e in seq ]
        i  =  np.array( [ midiKeras.vocab.index( e )  for  e in seq[ -48: ] ] ).reshape( 1, -1 )
        o  =  np.argmax( model.predict_on_batch( i ) )
        n  =  midiKeras.vocab[ o ]
        seq.append( n )
        print 'seq', seq
        t  +=  1
