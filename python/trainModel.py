import midiKeras as mk
import sys
from sys import getsizeof as sizeof
from os import path, listdir, system, rename
from os.path import isdir, isfile
from shutil import copyfile
from time import strftime
import pickle
import numpy as np
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import model_from_json, Sequential, Model
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
import midi
from subprocess import Popen

THIS_PATH = path.dirname( path.abspath( __file__ ) )

def scrapeDir( dir ):
    ret = [ ]
    for f in listdir( dir ):
        full  =  path.join( dir, f )
        if isdir( full ):
            ret.extend( scrapeDir( full ) )
        elif re.match( '(.*)\.mid', full ):
            ret.append( full )
    return ret


def scrapeDir1Ch( dir ):
    ret = [ ]
    for f in listdir( dir ):
        full  =  path.join( dir, f )
        if isdir( full ):
            ret.extend( scrapeDir1Ch( full ) )
        elif re.match( '(.*)\.mid', full ):
            try:
                pattern  =  midi.read_midifile( full )
            except:
                continue
            whichC  =  None
            thisOne  =  True
            for track in pattern:
                for event in track:
                    if not hasattr( event, 'channel' ):
                        continue
                    if whichC is None  and  event.channel != 9:
                        whichC  =  event.channel
                    elif event.channel != whichC  or  event.channel == 9:
                        thisOne  =  False
                        break
            if thisOne:
                dst  =  path.join( THIS_PATH, 'midi/train/oneCh', path.basename( full ) )
                i  =  2
                while path.isfile( dst ):
                    dst  =  dst[ :-4 ] + "-p" + dst[ -4: ]
                copyfile( full, dst )
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


def dumpEmbeddingWeights( model, fileName ):

    w  =  model.layers[ 1 ].get_weights( )[ 0 ]
    img = PIL.Image.new( 'RGB', w.shape )

    for i in range( w.shape[ 0 ] ):
        for j in range( w.shape[ 1 ] ):
            v  =  int( 255 / ( 1.0 + np.exp( - w[ i, j ] ) ) )
            img.putpixel( (i, j), (0, 0, v) )

    img.save( path.join( THIS_PATH, 'vis_debug', fileName ) )


class GUI:
    curSongIdx     =  0
    playSP         =  None
    ppc            =  64
    channelRects   =  { }
    channelBounds  =  { }

    def __init__( self, master, inputFiles ):
        self.master       =  master
        self.inputFiles   =  inputFiles

    def changeSong( self, e ):
        self.curSongIdx  =  self.songLB.curselection( )[ 0 ]
        tracks  =  midiKeras.midiToNotes( self.inputFiles[ self.curSongIdx ] )

        tracks  =  midiKeras.midiToNotes( self.inputFiles[ self.curSongIdx ] )

        self.channelRects   =  { }
        self.channelBounds  =  { }
        self.canvas.delete( ALL )

        trPCh  =  { }
        for i, track in enumerate( tracks ):
            for note in track:
                x1  =       3 * ( note[ 't' ] ) + 20
                x2  =  x1 + 3 * ( note[ 'd' ] )
                y   =  self.ppc - note[ 'n' ] * self.ppc / 128 + note[ 'c' ] * self.ppc
                self.canvas.create_rectangle( ( x1, y, x2, y ) )

                if note[ 'c' ] not in trPCh:
                    trPCh[ note[ 'c' ] ]  =  set( )

                trPCh[ note[ 'c' ] ].add( i )

        for c in range( 16 ):
            self.canvas.create_text( 0, self.ppc / 2 + c * self.ppc,      anchor = W, text = str( c ) )
            if c in trPCh:
                if len( trPCh[ c ] )  >  1:
                    text  =  '(' + str( len( trPCh[ c ] ) ) + ')'
                    self.canvas.create_text( 0, self.ppc / 2 + c * self.ppc + 11, anchor = W, text = text, fill = 'red' )

        self.canvas.config( scrollregion = self.canvas.bbox( ALL ) )

    def play( self ):
        outPath  =  path.join( '/tmp', path.basename( self.inputFiles[ self.curSongIdx ] ) )
        outPath  =  self._save( outPath )

        self.playSP  =  Popen( [ 'timidity', outPath ] )

    def stop( self ):
        if self.playSP:
            self.playSP.terminate( )
            self.playSP  =  None

    def _save( self, fileName ):
        pattern  =  midi.read_midifile( self.inputFiles[ self.curSongIdx ] )
        output  =  midi.Pattern( )
        output.resolution  =  pattern.resolution

        for track in pattern:
            time       =  0
            lostTime   =  0
            thisTrack  =  midi.Track( )
            for event in track:
                et  =  ( time + lostTime + event.tick ) / pattern.resolution
                if not hasattr( event, 'channel' )  or \
                        ( \
                            ( event.channel in self.channelBounds  and \
                            et  >  self.channelBounds[ event.channel ][ 0 ]  and \
                            et  <  self.channelBounds[ event.channel ][ 1 ] \
                        )  or \
                        self.channelBounds == { } ):
                    #if hasattr(event,'channel') and event.channel != 9:
                    #    print event
                    if lostTime  >  0:
                        event.tick  +=  lostTime
                        lostTime     =  0

                    thisTrack.append( event )

                    time  +=  event.tick
                else:
                    lostTime  +=  event.tick

            output.append( thisTrack )

        i  =  2
        while path.isfile( fileName ):
            fileName  =  fileName[ :-4 ] + "-p" + fileName[ -4: ]

        f  =  open( fileName, 'w')
        midi.write_midifile( f, output )
        f.close( )

        print 'Saved!', fileName

        return fileName

    def save( self ):
        outPath  =  path.join( THIS_PATH, 'midi', 'train', 'filtered', path.basename( self.inputFiles[ self.curSongIdx ] ) )
        self._save( outPath )

        #f  =  open( path.join( THIS_PATH, 'midi', 'program.txt' ), 'a' )
        #line  =  self.inputFiles[ self.curSongIdx ] + '\t' + str( self.channelSets ) + '\n'
        #f.write( line )
        #f.close( )

    def canvasClick( self, e ):
        #props = ['char', 'delta', 'height', 'keycode', 'keysym', 'keysym_num', 'num', 'send_event', 'serial', 'state', 'time', 'type', 'widget', 'width', 'x', 'x_root', 'y', 'y_root']
        canvas  =  e.widget
        canvas.focus( )

        x       =  canvas.canvasx( e.x )
        y       =  canvas.canvasy( e.y )

        self.dragStartTime  =  int( ( x - 20 ) / 3 )
        self.dragCIdx       =  int( y / self.ppc )

        if self.dragCIdx in self.channelRects and \
                self.channelRects[ self.dragCIdx ] is not None:
           canvas.delete( self.channelRects[ self.dragCIdx ] )
           self.channelRects[ self.dragCIdx ]  =  None

        self.dragWindow  =  self.channelRects[ self.dragCIdx ]  = \
                canvas.create_rectangle( ( x, self.dragCIdx * self.ppc, x, ( self.dragCIdx + 1 ) * self.ppc ) )

    def canvasDrag( self, e ):
        canvas  =  e.widget
        x       =  canvas.canvasx(e.x)
        y       =  canvas.canvasy(e.y)

        self.dragTime  =  int( ( x - 20 ) / 3 )

        curC  =  canvas.coords( self.dragWindow )
        canvas.coords( self.dragWindow, ( curC[0], curC[1], x, curC[3] ) )

    def canvasClack( self, e ):
        canvas  =  e.widget
        x       =  canvas.canvasx(e.x)
        y       =  canvas.canvasy(e.y)

        self.dragTime  =  int( ( x - 20 ) / 3 )

        canvas.itemconfig( self.dragWindow, outline = 'red' )

        self.channelBounds[ self.dragCIdx ]  =  ( self.dragStartTime, self.dragTime )

    def canvasKey( self, e ):
        if e.keysym == 'Up':
            self.canvas.yview_scroll( -1, 'units' )
        elif e.keysym == 'Down':
            self.canvas.yview_scroll( 1, 'units' )
        elif e.keysym == 'Left':
            self.canvas.xview_scroll( -1, 'units' )
        elif e.keysym == 'Right':
            self.canvas.xview_scroll( 1, 'units' )

    def start( self ):
        self.leftFrame  =  Frame( self.master )

        self.songFrame  =  Frame( self.leftFrame )
        self.songSB     =  Scrollbar( self.songFrame )
        self.songLB     =  Listbox( self.songFrame, yscrollcommand = self.songSB.set, width = 50, height = 50 )
        for i, f in enumerate( self.inputFiles ):
            self.songLB.insert( END, str( f ) )
        self.songLB.pack( side = LEFT, fill = BOTH )
        self.songLB.bind( "<Double-Button-1>", self.changeSong )
        self.songSB.pack( side = RIGHT, fill = Y )
        self.songSB.config( command = self.songLB.yview )
        self.songFrame.pack( side = TOP )

        self.playBtn  =  Button( self.leftFrame, text = 'Play', command = self.play )
        self.playBtn.pack( side = TOP )

        self.stopBtn  =  Button( self.leftFrame, text = 'Stop', command = self.stop )
        self.stopBtn.pack( side = TOP )

        self.saveBtn  =  Button( self.leftFrame, text = 'Save', command = self.save )
        self.saveBtn.pack( side = TOP )

        self.leftFrame.pack( side = LEFT )

        self.canvas  =  Canvas( self.master, width = 1600, height = 1200, background = 'white' )
        self.canvas.pack( side = LEFT )
        self.canvas.bind( "<Button-1>",  self.canvasClick )
        self.canvas.bind( "<B1-Motion>", self.canvasDrag )
        self.canvas.bind( "<ButtonRelease-1>", self.canvasClack )
        self.master.bind( "<Key>",       self.canvasKey )
        #self.master.bind( 'a', self.canvasKey )

        self.master.mainloop( )

if __name__ == '__main__':

    global midiKeras
    midiKeras = mk.MidiKeras( )

    doRewrite    =  False
    visDebug     =  False
    isTrainFile  =  True
    inputFiles   =  [ ]
    testFiles    =  [ ]
    testFrag     =  None
    trainDirs    =  [ ]
    model        =  None
    vocab        =  [None, {}]
    addToVocab   =  True
    pathPrefix   =   path.join('keras_models', strftime('%d-%b-%H:%M'))
    maxEpochs    =  1

    # parse command line arguments
    i  =  1
    while i < len( sys.argv ):

        # switch on argument i
        if sys.argv[ i ] == 'train':
            isTrainDir  = False
            isTrainFile = True
        elif sys.argv[ i ] == 'test':
            isTrainDir  = False
            isTrainFile = False
        elif sys.argv[ i ] == 'rewrite':
            doRewrite = True
        elif sys.argv[ i ] == 'vis':
            visDebug = True
        elif sys.argv[ i ] == 'model':
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
        elif sys.argv[ i ] == 'epochs':
            maxEpochs = int( sys.argv[ i + 1 ] )
            i += 1
        elif sys.argv[ i ] == 'dir':
            isTrainFile    = False
            isTrainDir     = True
            isTrainDir1Ch  =  False
        elif sys.argv[ i ] == 'dirOneCh':
            inputFiles.extend( scrapeDir1Ch( sys.argv[ i + 1 ] ) )
            i += 1
        elif sys.argv[ i ] == 'test-frag':
            testFrag = float( sys.argv[ i + 1 ] )
            i += 1
        elif sys.argv[ i ] == 'dump':
            p = midi.read_midifile( inputFiles[ -1 ] )
            print 'format', p.format
            for t in p:
                print 'track'
                for e in t:
                    print e
            quit( )
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

    # recurse through a directory and gather MIDI files
    for d in trainDirs:
        inputFiles.extend( scrapeDir( d ) )

    #################
    #f = open('vocab.lteTwo')
    #midiKeras.vocab  =  pickle.loads( f.read( ) )
    #f.close( )
    #f = open('fileList.lteTwo')
    #inputFiles  =  pickle.loads( f.read( ) )
    #f.close( )
    #################

    print 'len inputFiles', len( inputFiles )

    # sift through files
    #master  =  Tk( )
    #gui     =  GUI( master, inputFiles )
    #gui.start( )
    #quit( )

    # initialize midiKeras.vocab
    filtered  =  [ ]
    for a in range( 12 ):
        for b in range( 12 ):
            for c in range( 5 ):
                for d in range( 5 ):
                    e = { a: c, b: d }
                    if e not in midiKeras.vocab:
                        midiKeras.vocab.append( e )

    #print len( midiKeras.vocab ), sizeof( midiKeras.vocab )
    for i, f in enumerate( inputFiles ):
        try:
            print str( i + 1 ) + ' / ' + str( len( inputFiles ) ) + '  ( ' + f + ' )'
            e  =  midiKeras.midiToEvents( f )
            data  =  midiKeras.oneStep( f, returnTrainingData = True )
            print 'e', e
            print 'data', data

        except Exception, e:
            continue

    quit( )

    #print 'vocab:'
    #for i, v in enumerate( midiKeras.vocab ):
    #    print i, v

    inputLength  =  16 * 3
    memMax       =  50 * 1024 * 1024 # 50 megabytes
    thisTrainX   =  [ ]
    thisTrainY   =  [ ]
    thisTestX    =  [ ]
    thisTestY    =  [ ]
    if not model:
        layers  =  midiKeras.genLayers( inputLength )
        model   =  midiKeras.genFuncModel( layers )
        with open( pathPrefix + '-struct.json', 'w' ) as f:
            f.write( model.to_json( ) )

    # always use the same files for training and for testing
    seed( 'random seed' )
    shuffle( inputFiles )
    splitIdx  =  int( len( inputFiles ) * 0.9 )
    trainFiles  =  inputFiles[ :splitIdx ]
    testFiles   =  inputFiles[ splitIdx: ]

    iter  =  0
    while True:
        iter  +=  1
        print 'iter', iter

        shuffle( trainFiles )
        shuffle( testFiles )

        ( trainX, trainY )  =  ( np.zeros(( 0, inputLength )), np.zeros(( 0, len( midiKeras.vocab ) )) )
        ( testX, testY )    =  ( np.zeros(( 0, inputLength )), np.zeros(( 0, len( midiKeras.vocab ) )) )

        trainI  =  0

        while trainI  <  len( trainFiles ):

            testI  =  min( int( trainI * 0.1 ), len( testFiles ) - 1 )

            if len( thisTrainX ) == 0:
                try:

                    trainF  =  trainFiles[ trainI ]
                    ( thisTrainX, thisTrainY )  =  midiKeras.oneStep( trainF, returnTrainingData = True )

                    testF  =  testFiles[ testI ]
                    ( thisTestX, thisTestY )  =  midiKeras.oneStep( testF, returnTrainingData = True )

                    trainI  +=  1
                except:
                    continue

            trainIdx  =  range( len( thisTrainX ) )
            testIdx   =  range( len( thisTestX ) )
            shuffle( trainIdx )
            shuffle( testIdx )

            trainMem  =  sizeof( trainX )  +  sizeof( trainY )
            testMem   =  sizeof( testX )   +  sizeof( testY )

            thisTrainMem   =  sizeof( thisTrainX )  +  sizeof( thisTrainY )
            ppb            =  len( thisTrainX ) / float( thisTrainMem )
            neededNb       =  max( 0, memMax - trainMem - testMem ) * ppb
            trainNb        =  int( neededNb * 0.9 )
            testNb         =  int( neededNb - trainNb )

            trainX  =  np.vstack( ( trainX, thisTrainX[ trainIdx[ :trainNb ] ] ) )
            trainY  =  np.vstack( ( trainY, thisTrainY[ trainIdx[ :trainNb ] ] ) )
            testX   =  np.vstack( ( testX, thisTestX[ testIdx[ :testNb ] ] ) )
            testY   =  np.vstack( ( testY, thisTestY[ testIdx[ :testNb ] ] ) )

            thisTrainX  =  thisTrainX[ trainIdx[ trainNb: ] ]
            thisTrainY  =  thisTrainY[ trainIdx[ trainNb: ] ]
            thisTestX   =  thisTestX[ testIdx[ testNb: ] ]
            thisTestY   =  thisTestY[ testIdx[ testNb: ] ]


            if len( thisTrainX ) > 0  or  trainI == len( trainFiles ) - 1:

                percentage  =  trainI * 100 / len( trainFiles )
                weightPrefix  =  pathPrefix + '-iter_' + str( iter ) + '-' + str( percentage ) + '_prcnt'
                if percentage % 20 == 0  and  not isfile( weightPrefix + '-weights.h5' ):
                    model.save_weights( weightPrefix + '-weights.h5' )
                    #dumpEmbeddingWeights( model, weightPrefix + '-embedding.png' )

                trainMetrics  =  model.train_on_batch( trainX, trainY )
                testMetrics   =  model.test_on_batch( testX, testY )

                print str( percentage ) + '%', '\ttrain\t', trainMetrics[0], trainMetrics[1], '\ttest\t', testMetrics[0], testMetrics[1]

                ( trainX, trainY )  =  ( np.zeros(( 0, inputLength )), np.zeros(( 0, len( midiKeras.vocab ) )) )
                ( testX, testY )    =  ( np.zeros(( 0, inputLength )), np.zeros(( 0, len( midiKeras.vocab ) )) )

    quit( )

    # if we have no training data, generate some random data
    #if not len( trainData ):
    #    for note in range(40, 70):
    #        midiKeras.vocab.append( {note: [mk.NOTE_ON]} )
    #        midiKeras.vocab.append( {note: [mk.NOTE_HOLD]} )
    #        midiKeras.vocab.append( {note: [mk.NOTE_OFF]} )
    #    for i in range(16):
    #        vData = [ ]
    #        for j in range(64):
    #            vData.append( randint(1, len( midiKeras.vocab ) - 1) )
    #        trainData.append(vData)

    # if we still have no training data, load all the data from the current mongo db
    #if not len( trainData ):
    #    client = MongoClient()
    #    db = client.music
    #    compositions = db.composition.find()
    #    for composition in compositions:
    #        vData = midiKeras.vocabularize( composition['notes'] )
    #        trainData.append( vData )

    #if not len( testData ) and testFrag:
    #    shuffle( trainData )
    #    testIdx = ( int( len( trainData ) * testFrag ) * 16 ) / 16
    #    endIdx  = ( len( trainData ) * 16 ) / 16
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
