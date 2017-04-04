import midiKeras as mk
import sys
from os import path, listdir, system, rename, urandom
from time import strftime
import pickle
import numpy as np
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import model_from_json
from keras.models import Sequential, Model
from keras.layers import Input, Embedding, LSTM, Dense, Activation, merge
#from keras.utils.visualize_util import plot
from keras.optimizers import RMSprop
import PIL
from random import random, randint, shuffle, seed
import math
from os.path import isdir, isfile

if __name__ == '__main__':

    global midiKeras
    midiKeras = mk.MidiKeras( )

    isTrainFile  =  True
    inputFiles   =  [ ]
    testFiles    =  [ ]
    trainDirs    =  [ ]
    model        =  None
    vocab        =  [ None, {} ]
    pathPrefix   =  path.join( 'keras_models', strftime( '%d-%b-%H:%M' ) )
    epoch        =  1

    # parse command line arguments
    i  =  1
    while i < len( sys.argv ):

        # switch on argument i
        if sys.argv[ i ] == 'model':
            pathPrefix = sys.argv[ i + 1 ]
            i += 1
            if isfile( pathPrefix + '-struct.json' ):
                with open( pathPrefix + '-struct.json' ) as f:
                    print 'loading model definition'
                    model = model_from_json( f.read( ) )
                if isfile( pathPrefix + '-weights.h5' ):
                    print 'loading model weights'
                    model.load_weights( pathPrefix + '-weights.h5' )
                rmsProp  =  RMSprop( lr = 0.0001 )
                model.compile( optimizer = rmsProp, loss = 'categorical_crossentropy', metrics = [ 'accuracy' ] )
            if isfile( pathPrefix + '-vocab.pickle' ):
                with open( pathPrefix + '-vocab.pickle' ) as f:
                    vocab = pickle.loads( f.read( ) )
                    midiKeras.setVocab( vocab )
                addToVocab = False
        elif sys.argv[ i ] == 'epoch':
            epoch = int( sys.argv[ i + 1 ] )
            i += 1
        elif sys.argv[ i ] == 'dir':
            isTrainFile    = False
            isTrainDir     = True
        elif isfile( sys.argv[ i ] ):
            if isTrainFile:
                inputFiles.append( sys.argv[ i ] )
            elif isTrainDir and isdir( sys.argv[i] ):
                trainDirs.append( sys.argv[ i ] )
            else:
                testFiles.append( sys.argv[ i ] )
        else:
            print 'Unknown:', sys.argv[ i ]
            quit( )

        i += 1

    for d in trainDirs:
        inputFiles.extend( scrapeDir( d ) )

    for a in range( 12 ):
        for b in range( 12 ):
            for c in range( 5 ):
                for d in range( 5 ):
                    e = { a: c, b: d }
                    if e not in midiKeras.vocab:
                        midiKeras.vocab.append( e )

    seed( 'random seed' )
    shuffle( inputFiles )
    seed( urandom( 64 ) )

    splitIdx  =  int( len( inputFiles ) * 0.9 )
    trainFiles  =  inputFiles[ :splitIdx ]
    testFiles   =  inputFiles[ splitIdx: ]

    metrics  =  np.array( [ 0, 0 ], dtype = np.float32 )
    n  =  0

    for f in testFiles:
        print f
        ( testX, testY )  =  midiKeras.oneStep( f )
        if len( testX )  !=  0:
            metrics  +=  model.test_on_batch( testX, testY )
            n  +=  1

    metrics  /=  n
    print metrics
