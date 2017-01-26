import midiKeras as mk
import sys
from os import path, listdir
from os.path import isdir, isfile
from time import strftime
import pickle
import numpy as np
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import model_from_json
from keras.models import Sequential, Model
from keras.layers import Input, Embedding, LSTM, Dense, Activation, Highway
from keras import backend as K
from theano import function
#from keras.utils.visualize_util import plot
#from keras.optimizers import RMSprop
import PIL
from random import random, randint, shuffle
import math
import json
from pymongo import MongoClient
import re

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
                if e != None:
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
            #if idx != None:
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

def trainAndTest( trainData, testData ):
    global model
    ( fTrainData, fTrainLabels ) = midiKeras.formatData( trainData )
    ( fTestData, fTestLabels ) = midiKeras.formatData( testData )

    trainMetrics = np.zeros( ( len( model.metrics_names ), ) )
    batchShape = ( len( self.trainData ), 1 )

    model.reset_states()
    for j in range( 0, len( fTrainData ), batchShape[0] ):
        batch = ( fTrainData[ j:j + batchShape[0] ], fTrainLabels[ j:j + batchShape[0] ] )
        trainMetrics += model.train_on_batch( batch[0], batch[1] )
    trainMetrics /= ( len( fTrainData ) / float( batchShape[0] ) )
    print zip( model.metrics_names, trainMetrics )

if __name__ == '__main__':

    global midiKeras
    midiKeras = mk.MidiKeras( )

    doRewrite = False
    visDebug = False
    isTrainFile = True
    trainFiles = [ ]
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
                trainFiles.append( sys.argv[i] )
            elif isTrainDir and isdir( sys.argv[i] ):
                trainDirs.append( sys.argv[i] )
            else:
                testFiles.append( sys.argv[i] )
        i += 1

    # recurse through a directory and prepare MIDI files inside for training
    for d in trainDirs:
        trainFiles.extend( scrapeDir( d ) )

    # read training files, add to vocab (if addToVocab), and generate training data
    trainData          =  []
    epochCnt           =  0
    maxTrainChunkSize  =  100
    trainChunkSize     =  0
    trainChunk         =  [ ]
    maxTestChunkSize   =  100
    testChunkSize      =  0
    testChunk          =  [ ]
    batchShape         =  ( 16, 1 )
    model              =  midiKeras.genModel( batchShape )

    # loop for number of training epochs
        # loop through every training file
            # fill trainChunk then testChunk until full
            # when full, train network once, test it, collect stats, empty chunks
    pauseForTraining = False
    while epochCnt < maxEpochs:
        for i, f in enumerate( trainFiles ):
            print f, str( i + 1 ) + '/' + str( len( trainFiles ) )
            try:
                fileData = midiKeras.oneStep( f )
            except Exception, e:
                print 'failed:', f
                continue
            print 'fileData', fileData

            fileDataSize = sum( len( x ) for x in fileData )

            trainChunkSize = sum( len( x ) for x in trainChunk )
            if trainChunkSize + fileDataSize  <  maxTrainChunkSize:
                trainChunk.extend( fileData )
            else:
                testChunkSize = sum( len( x ) for x in testChunk )
                if testChunkSize + fileDataSize  <  maxTestChunkSize:
                    testChunk.extend( fileData )
                else:
                    print 'trainAndTest('
                    print '\ttrainChunk', trainChunk
                    print '\ttestChunk', testChunk
                    print ')'
                    trainAndTest( trainChunk, testChunk )
                    trainChunk = [ ]
                    testChunk  = [ ]

        epochCnt += 1

    for i, f in enumerate( trainFiles ):
        print f
        print str(i) + '/' + str(len(trainFiles))
        try:
            #tracks = midiKeras.midiRip( f, visDebug = visDebug )
            trainData.extend( midiKeras.oneStep( f ) )
        except Exception, e:
            print 'failed:', f
            raise e
            continue

        #for track in tracks:
        #    if len(track) == 0:
        #        continue
        #    #snippets = midiKeras.sliceAndDice( track, visDebug = visDebug )

        #    #for snippet in snippets:
        #    vData = midiKeras.vocabularize( track, addNew = addToVocab, visDebug = visDebug ) 

        #    if {} in midiKeras.vocab:
        #        vData = midiKeras.stripSilence( vData, midiKeras.vocab.index( {} ) )
        #    trainData.append( vData )

        #    # print 'len vData', len( vData )
        #    if doRewrite:
        #        midiKeras.midiOut( vData, 'midi/rewrite/' + path.basename( f ), resolution )

    # read testing files, add to vocab (if addToVocab), and generate testing data
    testData = []
    for f in testFiles:
        print f
        try:
            tracks = midiKeras.midiRip( f )
        except:
            continue

        for track in tracks:
            vData = midiKeras.vocabularize( track, addNew = False )

            if {} in midiKeras.vocab:
                vData = midiKeras.stripSilence( vData, midiKeras.vocab.index( {} ) )
            testData.append( vData )

            print 'len vData', len( vData )
            if doRewrite:
                midiKeras.midiOut( vData, 'midi/rewrite/' + path.basename( f ), resolution )

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
        if model == None:
            model = midiKeras.genModel( batchShape )

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
        #    if lastLoss != None and lastLoss < loss:
        #        break

    elif False and len(testData):
        batchShape = (len(testData), 1)
        if model == None:
            model = midiKeras.genModel(batchShape)
            with open(pathPrefix + '-struct.json', 'w') as f:
                f.write(model.to_json())
        #else:
        #    model.layers[0].batch_input_shape = batchShape
        #    model.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])

        (fTestData, fTestLabels) = midiKeras.formatData(testData)

        print len(fTestData)
        a = model.evaluate(fTestData, fTestLabels, batch_size = batchShape[0])
        print a
