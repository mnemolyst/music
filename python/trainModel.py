import midiKeras as mk
import sys
from sys import getsizeof as sizeof
from os import path, listdir
from os.path import isdir, isfile
from time import strftime
import pickle
import numpy as np
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import model_from_json
from keras.models import Sequential, Model
from keras.layers import Input, Embedding, LSTM, Dense, Activation, Highway
from keras.utils.np_utils import to_categorical
from keras import backend as K
from theano import function
#from keras.utils.visualize_util import plot
from keras.optimizers import RMSprop
import PIL
from random import random, randint, shuffle, seed
import math
import json
from pymongo import MongoClient
import re
from Tkinter import *

THIS_PATH = path.dirname( path.abspath( __file__ ) )

class Trainer:
    def __init__( self, model, trainData, testData = None ):
        global midiKeras

        self.model      =  model
        self.trainData  =  trainData
        self.testData   =  testData
        self.batchShape = ( len( self.trainData ), 1 )
        #self.batchShape = ( 16, 1 )

        ########################
        # fTrainData dimensions:
        # total-number-of-training-points  X  1
        #
        # fTrainLabels dimensions:
        # total-number-of-training-points  X  length-of-vocab
        (self.fTrainData, self.fTrainLabels) = midiKeras.formatData(self.trainData)

        if len(self.testData):
            (self.fTestData, self.fTestLabels) = midiKeras.formatData(self.testData)

    def imgTest( self, iterN ):
        self.model.reset_states()
        img = PIL.Image.new( 'RGB', ( max( len(x) for x in self.trainData ) + 1, 129 * len(self.trainData) ) )
        for i, track in enumerate(self.trainData):
            for j, k in enumerate(track):
                e = midiKeras.vocab[k]
                for n in e:
                    img.putpixel( (j, 129 * i + n), (255, 255, 255) )

        pred = self.model.predict_classes( self.fTrainData, batch_size = self.batchShape[0], verbose=0 )
        #print 'pred\tact'
        #for ( p, a ) in zip( pred, np.append( self.fTrainData[2:], [[0],[0]] ) ):
        #    print str(p) + '\t' + str(a)
        i = 1
        for batchIdx in range(0, len(pred), self.batchShape[0]):
            batch = pred[batchIdx : batchIdx + self.batchShape[0]]
            es = [midiKeras.vocab[x] for x in batch]
            for j, e in enumerate(es):
                if e is not None:
                    for n in e:
                        p = img.getpixel((i, 129 * j + n))
                        img.putpixel( (i, 129 * j + n), (255, p[1] / 2, p[2] / 2) )
            i += 1
        img.save(pathPrefix + '-i' + str(iterN) + '.png')

    def train( self, idx = None ):

        if len( self.testData ):
            earlyStopping = EarlyStopping( monitor = 'val_loss', patience = 1 )
            modelCheckpoint = ModelCheckpoint( pathPrefix + '-weights.h5', monitor = 'val_loss', verbose = 0, save_best_only = True )
            history = model.fit( fTrainData, fTrainLabels, nb_epoch = maxEpochs, batch_size = self.batchShape[ 0 ], shuffle = False, validation_data = ( self.fTestData, self.fTestLabels ), callbacks = [ earlyStopping, modelCheckpoint ] )

        lossHist = []
        i = 0

        while True:
            print '\ni:', i
            self.imgTest( i )
            metrics = np.zeros((len(self.model.metrics_names), ))

            self.model.reset_states()
            for j in range(0, len(self.fTrainData), self.batchShape[0]):
                batch = (self.fTrainData[j:j + self.batchShape[0]], self.fTrainLabels[j:j + self.batchShape[0]])
                metrics += self.model.train_on_batch(batch[0], batch[1])
            metrics /= len(self.fTrainData) / float(self.batchShape[0])
            lossHist = lossHist[-14:] + [metrics[self.model.metrics_names.index('loss')]]
            print zip(self.model.metrics_names, metrics)
            if len(lossHist) == 15:
                fit = np.polyfit(range(15), lossHist, 1)
                if fit[0] > 0:
                    #break
                    pass

            #################
            # image weights #
            #################
            #if idx is not None:
            #    for l in self.model.layers:
            #        weights = l.get_weights()
            #        for j, m in enumerate(weights):
            #            m = (m.astype(np.float32) - np.min(m)) / (np.max(m) - np.min(m)) * 256
            #            if len(m.shape) < 2:
            #                continue
            #                #m = np.reshape(m, (m.shape[0], -1))
            #            img = PIL.Image.fromarray(m, 'L')
            #            img.save(pathPrefix + '-' + str(idx) + '-i' + str(i) + '-layer-' + l.name + '-' + str(j) + '.png')
            i += 1
        return lossHist[-1]

    def saveModel( ):
        with open(pathPrefix + '-struct.json', 'w') as f:
            f.write(self.model.to_json())
        self.model.save_weights(pathPrefix + '-weights.h5')


def scrapeDir( dir ):
    ret = [ ]
    for f in listdir( dir ):
        full  =  path.join( dir, f )
        if isdir( full ):
            ret.extend( scrapeDir( full ) )
        elif re.match( '(.*)\.mid', full ):
            ret.append( full )
    return ret


def trainAndTest( batchLen, fTrainData, fTrainLabels, fTestData = [ ], fTestLabels = [ ] ):
    global model

    #print 'trainAndTest ('
    #print '\tfTrainData', fTrainData
    #print '\tfTrainLabels', fTrainLabels
    #print '\tfTestData', fTestData
    #print '\tfTestLabels', fTestLabels
    #print '\tbatchLen', batchLen
    #print ')'

    trainMetrics = np.zeros( ( len( model.metrics_names ), ) )

    model.reset_states()
    leadIn = 8
    for j in range( 0, len( fTrainData ), batchLen ):

        batchX  =  fTrainData[ j:j + batchLen ]

        if leadIn > 0:
            model.predict_on_batch( batchX )
            leadIn -= 1
        else:
            batchY  =  fTrainLabels[ j:j + batchLen ]
            trainMetrics += model.train_on_batch( batchX, batchY )

    trainMetrics /= ( len( fTrainData ) / float( batchLen ) )
    print zip( model.metrics_names, trainMetrics )


def dumpEmbeddingWeights( fileName ):
    global model, pathPrefix

    w  =  model.layers[ 1 ].get_weights( )[ 0 ]
    img = PIL.Image.new( 'RGB', w.shape )

    for i in range( w.shape[ 0 ] ):
        for j in range( w.shape[ 1 ] ):
            v  =  int( 255 / ( 1.0 + np.exp( - w[ i, j ] ) ) )
            img.putpixel( (i, j), (0, 0, v) )

    img.save( path.join( THIS_PATH, 'vis_debug', fileName + '.png' ) )


def doIt( a, b ):
    for i in range( a, b ):
        trainAndTest(1, fTrainData, fTrainLabels)
        dumpEmbeddingWeights( 'test' + str(i) )

class GUI:
    def __init__( self, master, inputFiles ):
        self.master       =  master
        self.inputFiles   =  inputFiles
        self.curSongIdx   =  0
        self.curTrackIdx  =  0

    def changeSong( self, e ):
        self.curSongIdx  =  self.songLB.curselection( )[ 0 ]
        print self.inputFiles[ self.curSongIdx ]
        tracks  =  midiKeras.midiRip( self.inputFiles[ self.curSongIdx ] )
        self.trackLB.delete( 0, END )
        for i, track in enumerate( tracks ):
            self.trackLB.insert( END, 'Track ' + str( i ) )

    def changeTrack( self, e ):
        tracks            =  midiKeras.midiRip( self.inputFiles[ self.curSongIdx ] )
        self.curTrackIdx  =  self.trackLB.curselection( )[ 0 ]

        self.canvas.delete( ALL )
        for note in tracks[ self.curTrackIdx ]:
            x1  =       3 * ( note[ 't' ] ) + 20
            x2  =  x1 + 3 * ( note[ 'd' ] )
            y   =  0.5 * ( 128 - note[ 'n' ] + note[ 'c' ] * 128 )
            self.canvas.create_rectangle( ( x1, y, x2, y ) )

        for c in range( 16 ):
            self.canvas.create_text( 0, 0.5 * ( 64 + c * 128 ), anchor = W, text = str( c + 1 ) )

    def start( self ):
        self.leftFrame  =  Frame( self.master )

        self.songFrame  =  Frame( self.leftFrame )
        self.songSB  =  Scrollbar( self.songFrame )
        self.songSB.pack( side = RIGHT, fill = Y )
        self.songLB  =  Listbox( self.songFrame, yscrollcommand = self.songSB.set )
        for i, f in enumerate( self.inputFiles ):
            self.songLB.insert( END, str( f ) )
        self.songLB.pack( side = LEFT, fill = BOTH )
        self.songLB.bind( "<Double-Button-1>", self.changeSong )
        self.songSB.config( command = self.songLB.yview )
        self.songFrame.pack( side = TOP )

        self.trackFrame  =  Frame( self.leftFrame )
        self.trackSB  =  Scrollbar( self.trackFrame )
        self.trackSB.pack( side = RIGHT, fill = Y )
        self.trackLB  =  Listbox( self.trackFrame, yscrollcommand = self.trackSB.set )
        self.trackLB.pack( side = LEFT, fill = BOTH )
        self.trackLB.bind( "<Double-Button-1>", self.changeTrack )
        self.trackSB.config( command = self.trackLB.yview )
        self.trackFrame.pack( side = TOP )

        self.channelLB  =  Listbox( self.leftFrame, selectmode = MULTIPLE )
        for c in range( 16 ):
            self.channelLB.insert( END, str( c + 1 ) )
        self.channelLB.pack( side = TOP )

        self.leftFrame.pack( side = LEFT )

        self.canvasSB  =  Scrollbar( self.master )
        self.canvas  =  Canvas( self.master, width = 1200, height = 1200, background = 'white', yscrollcommand = self.canvasSB.set )
        self.canvasSB.config( command = self.canvas.yview )
        self.canvasSB.pack( side = RIGHT, fill = Y )
        self.canvas.pack( side = LEFT )

        self.master.mainloop( )

if __name__ == '__main__':

    global midiKeras
    midiKeras = mk.MidiKeras( )

    doRewrite = False
    visDebug = False
    isTrainFile = True
    inputFiles = [ ]
    testFiles  = [ ]
    testFrag = None
    trainDirs  = [ ]
    model = None
    vocab = [None, {}]
    addToVocab = True
    pathPrefix = path.join('keras_models', strftime('%d-%b-%H:%M'))
    maxEpochs = 1
    i = 1

    # parse command line arguments
    while i < len(sys.argv):

        # switch on argument i
        if sys.argv[i] == 'train':
            isTrainDir  = False
            isTrainFile = True
        elif sys.argv[i] == 'test':
            isTrainDir  = False
            isTrainFile = False
        elif sys.argv[i] == 'rewrite':
            doRewrite = True
        elif sys.argv[i] == 'vis':
            visDebug = True
        elif sys.argv[i] == 'model':
            pathPrefix = sys.argv[i + 1]
            i += 1
            if path.exists( pathPrefix + '-struct.json' ):
                with open( pathPrefix + '-struct.json' ) as f:
                    model = model_from_json( f.read( ) )
                if path.exists( pathPrefix + '-weights.h5' ):
                    model.load_weights( pathPrefix + '-weights.h5' )
                model.compile( optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'] )
            if path.exists( pathPrefix + '-vocab.pickle' ):
                with open( pathPrefix + '-vocab.pickle' ) as f:
                    vocab = pickle.loads( f.read( ) )
                    midiKeras.setVocab( vocab )
                addToVocab = False
        elif sys.argv[i] == 'epochs':
            maxEpochs = int( sys.argv[i + 1] )
            i += 1
        elif sys.argv[i] == 'dir':
            isTrainFile = False
            isTrainDir  = True
        elif sys.argv[i] == 'test-frag':
            testFrag = float( sys.argv[i + 1] )
            i += 1
        elif path.exists( sys.argv[i] ):
            if isTrainFile:
                inputFiles.append( sys.argv[i] )
            elif isTrainDir and isdir( sys.argv[i] ):
                trainDirs.append( sys.argv[i] )
            else:
                testFiles.append( sys.argv[i] )
        i += 1

    # recurse through a directory and gather MIDI files
    for d in trainDirs:
        inputFiles.extend( scrapeDir( d ) )

    # sift through files
    master  =  Tk( )
    gui     =  GUI( master, inputFiles )
    gui.start( )
    quit( )

    #master.mainloop( )
    #quit( )

    # initialize midiKeras.vocab
    # print 'initializing vocab'
    for i, f in enumerate( inputFiles ):
        try:
            print str( i + 1 ) + ' / ' + str( len(inputFiles) ) + ' ( ' + f + ' )'
            midiKeras.oneStep( f, returnTrainingData = False )
        except Exception, e:
            continue

    #print 'vocab:'
    #for i, v in enumerate( midiKeras.vocab ):
    #    print i, v

    batchSize    =  1
    trainChunk   =  [ ]
    inputLength  =  16 * 3
    layers       =  midiKeras.genLayers( inputLength )
    model        =  midiKeras.genFuncModel( layers )
    memMax       =  25 * 1024 * 1024 # 25 megabytes
    thisX        =  None
    thisY        =  None

    iter = 0
    while True:
        iter += 1
        print 'iter', iter

        ( x, y )  =  ( np.zeros(( 0, inputLength )), np.zeros(( 0, len(midiKeras.vocab) )) )
        shuffle( inputFiles )
        for i, f in enumerate( inputFiles ):
            if thisX is None and thisY is None:
                ( thisX, thisY )  =  midiKeras.oneStep( f, returnTrainingData = True )

            thisMem  =  sizeof( thisX ) + sizeof( thisY ) + sizeof( x ) + sizeof( y )

            if thisMem  <  memMax:
                idx  =  range( len(thisX) )
                seed( f )
                shuffle( idx )
                for j in idx:
                    x  =  np.vstack( ( x, thisX[ j ] ) )
                    y  =  np.vstack( ( y, thisY[ j ] ) )
                thisX = thisY = None

            if thisMem  >  memMax:

                trainX = x[ : int( len(x) * 0.9 ) ]
                trainY = y[ : int( len(y) * 0.9 ) ]
                testX  = x[ int( len(x) * 0.9 ) : ]
                testY  = y[ int( len(y) * 0.9 ) : ]

                model.fit( trainX, trainY, validation_data = ( testX, testY ), nb_epoch = 10, shuffle = True )

                ( x, y )  =  ( np.zeros(( 0, inputLength )), np.zeros(( 0, len(midiKeras.vocab) )) )

            if i == len(inputFiles) - 1:

                trainX  =  x[ : int( len(x) * 0.9 ) ]
                trainY  =  y[ : int( len(y) * 0.9 ) ]
                testX   =  x[ int( len(x) * 0.9 ) : ]
                testY   =  y[ int( len(y) * 0.9 ) : ]

                #earlyStopping    =  EarlyStopping( monitor = 'val_loss', patience = 20 )
                #modelCheckpoint  =  ModelCheckpoint( pathPrefix + '-weights.h5', monitor = 'val_loss', verbose = 0, save_best_only = True )

                model.fit( trainX, trainY, validation_data = ( testX, testY ), nb_epoch = 10000, shuffle = True )
                quit( )

    quit( )

    while True:
        ( x, y )  =  ( np.zeros(( 0, inputLength )), np.zeros(( 0, len(midiKeras.vocab) )) )
        keepGoing  =  True
        while keepGoing:
            for f in inputFiles:
                if thisX is None and thisY is None:
                    ( thisX, thisY )  =  midiKeras.oneStep( f, returnTrainingData = True )
                    seed( f )

                if sizeof( thisX ) + sizeof( thisY ) + sizeof( x ) + sizeof( y )  <  memMax:
                    x  =  np.vstack( ( x, thisX ) )
                    y  =  np.vstack( ( y, thisY ) )
                    thisX = thisY = None
                else:
                    keepGoing = False
                    break
        model.fit( x, y, validation_split = 0.1 )

        #for i, f in enumerate( inputFiles ):
        #    # print str( i + 1 ) + ' / ' + str( len(inputFiles) ) + ' ( ' + f + ' )'
        #    ( x, y )  =  midiKeras.oneStep( f, returnTrainingData = True )
        #    iterCnt    =  0
        #    while iterCnt < 10:
        #        iterCnt += 1
        #        metrics  =  model.train_on_batch( x, y )
        #        loss     =  float( metrics[ 0 ] )
        #        acc      =  float( metrics[ 1 ] )
        #        print 'iterCnt: ' + str( iterCnt ) + '\tloss: ' + str( loss ) + '\tacc: ' + str( acc )

    quit( )

    epochCnt  =  0
    # loop for number of training epochs
    #     loop through every training file
    #         fill trainChunk, then testChunk, until both are full
    #         when full, train network once, test it, collect stats, empty chunks
    while epochCnt < maxEpochs:
        print 'epochCnt', epochCnt
        for i, f in enumerate( inputFiles ):
            print f, '( ' + str( i + 1 ) + '/' + str( len( inputFiles ) ) + ' )'
            try:
                if fileData is None:
                    fileData = midiKeras.oneStep( f, returnTrainingData = True )
            except Exception, e:
                print 'failed:', f
                continue
            print 'fileData', fileData

            trainChunksNeeded  =  inputLength - len( trainChunk )
            trainChunk.extend( fileData[ :trainChunksNeeded ] )
            if trainChunksNeeded < len(fileData):
                pass#testChunksNeeded  =  

            if trainChunkSize + fileDataSize  <  maxTrainChunkSize:
                trainChunk.extend( fileData )
                fileData = None
            else:
                testChunkSize = sum( len( x ) for x in testChunk )
                print 'testChunkSize', testChunkSize
                if testChunkSize + fileDataSize  <  maxTestChunkSize:
                    testChunk.extend( fileData )
                    fileData = None
                elif trainChunkSize > 0:
                    ( fTrainData, fTrainLabels ) = midiKeras.formatData( trainChunk )
                    ( fTestData, fTestLabels ) = midiKeras.formatData( testChunk )
                    trainAndTest( inputLength, fTrainData, fTrainLabels, fTestData, fTestLabels )
                    trainChunk = [ ]
                    testChunk  = [ ]

        epochCnt += 1


    ( fTrainData, fTrainLabels ) = midiKeras.formatData( fileData )

    ################
    #model = midiKeras.genFuncModel2(layers)
    #fTrainLabels = midiKeras.convertLabels(fTrainLabels,layers[1])
    ################

    quit()

    # if we have no training data, generate some random data
    #if not len(trainData):
    #    for note in range(40, 70):
    #        midiKeras.vocab.append( {note: [mk.NOTE_ON]} )
    #        midiKeras.vocab.append( {note: [mk.NOTE_HOLD]} )
    #        midiKeras.vocab.append( {note: [mk.NOTE_OFF]} )
    #    for i in range(16):
    #        vData = [ ]
    #        for j in range(64):
    #            vData.append( randint(1, len(midiKeras.vocab) - 1) )
    #        trainData.append(vData)

    # if we still have no training data, load all the data from the current mongo db
    #if not len(trainData):
    #    client = MongoClient()
    #    db = client.music
    #    compositions = db.composition.find()
    #    for composition in compositions:
    #        vData = midiKeras.vocabularize( composition['notes'] )
    #        trainData.append( vData )

    #if not len(testData) and testFrag:
    #    shuffle( trainData )
    #    testIdx = ( int( len(trainData) * testFrag ) * 16 ) / 16
    #    endIdx  = ( len(trainData) * 16 ) / 16
    #    print testIdx, endIdx
    #    testData = trainData[:testIdx]
    #    trainData = trainData[testIdx:endIdx]

    # if we didn't read in a vocab file, save the current vocab
    if addToVocab:
        with open( pathPrefix + '-vocab.pickle', 'w' ) as f:
            f.write( pickle.dumps( midiKeras.vocab ) )

    # vocab complexity
    #for seq in trainData:
    #    lens = { }
    #    for k in seq:
    #        e = midiKeras.vocab[k]
    #        for n in e:
    #            l = len(e[n])
    #            if l not in lens:
    #                lens[l] = 0
    #            lens[l] += 1
    #    print 'note lens', lens
    #lens = { }
    #for e in midiKeras.vocab[1:]:
    #    for n in e:
    #        l = len(e[n])
    #        if l not in lens:
    #            lens[l] = 0
    #        lens[l] += 1
    #print 'vocab lens', lens

    # Start working!
    if len( trainData ) and not doRewrite:
        # ( number-of-tracks, 1 )
        batchShape = ( len( trainData ), 1 )

        # if we didn't load a model, make a new one
        if model is None:
            model = midiKeras.genFuncModel( batchShape )

        # train the model
        print 'trainData:', trainData
        print 'vocab:'
        for i, v in enumerate( midiKeras.vocab ):
            print i, v
        trainer  =  Trainer( model, trainData, testData )
        #print 'fTrainData:', trainer.fTrainData
        #print 'fTrainLabels:', trainer.fTrainLabels
        quit()
        trainer.train( )

        #loss = None
        #while True:
        #    defn = json.loads(model.to_json())
        #    defn['config'] = defn['config'][:-1] + defn['config'][-2:-1] + defn['config'][-1:]
        #    newModel = model_from_json(json.dumps(defn))
        #    for l in defn['config'][:-2]:
        #        #l.trainable = False
        #        newModel.add(l)
        #    newModel.add(LSTM(64, return_sequences = True, stateful = True))
        #    newModel.add(LSTM(64, stateful = True))
        #    newModel.add(Dense(len(midiKeras.vocab), activation = 'softmax'))
        #    newModel.layers[-3].set_weights(model.layers[-2].get_weights())
        #    newModel.layers[-1].set_weights(model.layers[-1].get_weights())
        #    newModel.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])
        #    print len(newModel.layers), 'layers'
        #    #train(newModel)

        #    #for l in newModel.layers:
        #    #    l.trainable = True
        #    #print 'fine tuning'
        #    #newModel.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])
        #    lastLoss = loss
        #    loss = train(newModel)
        #    model = newModel
        #    if lastLoss is not None and lastLoss < loss:
        #        break

    elif False and len(testData):
        batchShape = (len(testData), 1)
        if model is None:
            model = midiKeras.genFuncModel(batchShape)
            with open(pathPrefix + '-struct.json', 'w') as f:
                f.write(model.to_json())
        #else:
        #    model.layers[0].batch_input_shape = batchShape
        #    model.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])

        (fTestData, fTestLabels) = midiKeras.formatData(testData)

        print len(fTestData)
        a = model.evaluate(fTestData, fTestLabels, batch_size = batchShape[0])
        print a
