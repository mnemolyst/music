import midi
import glob
import sys
from os import path
import json

import keras
import numpy as np
from keras.models import Sequential, Model, model_from_json
from keras.layers import Input, Embedding, LSTM, Dense, Activation, Highway, Lambda
from keras.layers.wrappers import TimeDistributed
from keras.optimizers import RMSprop
from keras.utils.np_utils import to_categorical
import keras.backend as K

# graphics
from PIL import Image

NOTE_ON = 0
NOTE_HOLD = 1
NOTE_OFF = 2

OFF_ON     = 0
ON_ON      = 1
ON_OFF     = 2
ON_OFF_ON  = 3
OFF_ON_OFF = 4

THIS_PATH = path.dirname( path.abspath( __file__ ) )

class MidiKeras:
    def __init__(self, vocab = [None, {}]):
        self.vocab = vocab

    def setVocab(self, vocab):
        self.vocab = vocab

    def stripSilence(self, l, silence):
        startIdx = 0
        stopIdx = len(l)
        for i in range(len(l)):
            if l[i] != silence:
                startIdx = i
                break
        for i in reversed(range(len(l))):
            if l[i] != silence:
                stopIdx = i + 1
                break
        return l[startIdx:stopIdx]


    def visNotes( self, tracks, pathPrefix = 'tracks' ):
        imgWidth = max( x[-1]['t'] + x[-1]['d'] for x in tracks ) * 16
        imgHeight = 129 * len(tracks)
        img = Image.new( 'RGB', ( int(imgWidth), int(imgHeight) ) )
        for i, track in enumerate( tracks ):
            for note in track:
                start = int( note['t'] * 16 )
                end   = start + int( note['d'] * 16 )
                for k in range( start, end ):
                    img.putpixel( ( k, 129 * i + note['n'] ), ( 255, 255, 255 ) )
        img.save( pathPrefix + '.png' )

    def visVData( self, vData, res ):
        imgWidth = len( vData )
        imgHeight = 129
        img = Image.new( 'RGB', ( int(imgWidth), int(imgHeight) ) )
        for i, idx, in enumerate( vData ):
            e = self.vocab[ idx ]
            for n in e:
                if NOTE_ON in e[ n ]:
                    img.putpixel( ( i, n ), ( 255, 255, 255 ) )
        img.save( path.join( THIS_PATH, 'vis_debug', 'vdata' ) + '.png' )


    def updateEvent( self, event, pitch, isOn ):
        x = event.copy( )

        if isOn:
            if pitch not in x:
                x[ pitch ] = OFF_ON
            elif x[ pitch ] == ON_OFF:
                x[ pitch ] = ON_OFF_ON
            elif x[ pitch ] == ON_ON:
                x[ pitch ] = ON_OFF_ON
        else:
            if pitch not in x:
                pass
            elif x[ pitch ] == OFF_ON:
                x[ pitch ] = OFF_ON_OFF
            elif x[ pitch ] == ON_ON:
                x[ pitch ] = ON_OFF

        return x


    def oneStep( self, midiFile, returnTrainingData = False ):

        # the MIDI pattern
        pattern = midi.read_midifile( midiFile )

        # eventWidth = one sixteenth-note's worth of midi ticks
        eventWidth = float( pattern.resolution ) / 4.0

        # return values retX and retY
        seqLen = 16 * 3
        if returnTrainingData:
            retX = np.zeros( ( 0, seqLen ) )
            retY = np.zeros( ( 0, len( self.vocab ) ) )

        for i, track in enumerate( pattern ):
            events         =  [ ]
            timeIdx        =  None
            time           =  0
            notesOn        =  { }
            buildingEvent  =  { }

            for e in track:
                print e
                if isinstance( e, midi.NoteOffEvent ) or ( isinstance( e, midi.NoteOnEvent ) and e.velocity == 0 ):
                    isOn = False
                elif isinstance( e, midi.NoteOnEvent ):
                    isOn = True
                else:
                    continue

                # init buildingEvent
                if buildingEvent is None:
                    buildingEvent  =  { e.pitch: OFF_ON }

                lastNotesOn   =  notesOn.copy( )

                # use the notes that were on before this midi event to construct a fill
                # for time intervening between that midi event and this one
                fillEvent  =  dict( [ ( k[ 1 ], ON_ON ) for k in lastNotesOn ] )

                # update the set of notes currently on as of this midi event
                key  =  ( e.channel, e.pitch )
                if isOn:
                    notesOn[ key ]  =  time
                else:
                    if key in notesOn:
                        del notesOn[ key ]

                lastTime     =  time
                time        +=  e.tick
                lastTimeIdx  =  timeIdx
                timeIdx      =  int( float( time ) / eventWidth )

                # if we have moved on to another discretized time, vocab and append
                # the last one, fill intervening time, and start building a new
                # discretized vocab thing
                if lastTimeIdx != timeIdx  and  lastTimeIdx is not None:
                    events.append( buildingEvent.copy( ) )

                    while len( events )  <  timeIdx:
                        events.append( fillEvent.copy( ) )

                    buildingEvent  =  fillEvent.copy( )

                if isOn:
                    if e.pitch not in buildingEvent:
                        buildingEvent[ e.pitch ] = OFF_ON
                    elif buildingEvent[ e.pitch ] == ON_OFF:
                        buildingEvent[ e.pitch ] = ON_OFF_ON
                    elif buildingEvent[ e.pitch ] == ON_ON:
                        buildingEvent[ e.pitch ] = ON_OFF_ON
                else:
                    if e.pitch not in buildingEvent:
                        pass
                    elif buildingEvent[ e.pitch ] == OFF_ON:
                        buildingEvent[ e.pitch ] = OFF_ON_OFF
                    elif buildingEvent[ e.pitch ] == ON_ON:
                        buildingEvent[ e.pitch ] = ON_OFF

            # one more time after the loop of MIDI events
            if buildingEvent:
                events.append( buildingEvent.copy( ) )

            print 'events', events

            # break the events up into chunks
            startIdx        =  0
            makeMoreChunks  =  True
            while makeMoreChunks:
                diffCount     =  0
                numDiff       =  15 # arbitrary constant
                eList         =  [ ]
                vList         =  [ ]
                lastHappened  =  0
                eIdx          =  startIdx

                while diffCount < numDiff  and  len( eList ) < seqLen  and  eIdx < len( events ):
                    # skip initial empty events
                    if len( eList ) == 0  and  events[ eIdx ] == { }:
                        eIdx  +=  1
                        continue

                    # count number of times the event changes
                    if len( eList ) == 0  or  eList[ -1 ] != events[ eIdx ]:
                        diffCount  +=  1

                    eList.append( events[ eIdx ] )

                    if eList[ -1 ]  !=  { }:
                        lastHappened  =  len( eList )

                    eIdx += 1

                if eIdx  >=  len( events ):
                    makeMoreChunks  =  False

                startIdx += 4
                eList = eList[ : lastHappened ]

                # shift pitches so every chunk's penultimate event's lowest pitch is numbered zero
                # TODO use the last event with a pitch - now we only consider the last in the list
                if len( eList ) >= 2  and  eList[ -2 ].keys( ) != [ ]:
                    zeroPitch  =  min( eList[ -2 ].keys( ) )
                    eList  =  [ dict( [ ( p - zeroPitch, e[ p ] ) for p in e.keys( ) ] ) for e in eList ]
                    for e in eList:
                        if e not in self.vocab:
                            self.vocab.append( e )
                        eIdx  =  self.vocab.index( e )
                        vList.append( eIdx )

                    if returnTrainingData:
                        thisX  =  np.array( vList[ :-1 ] ).reshape(( 1, -1 ))
                        retX   =  np.vstack( ( retX, np.pad( thisX, ((0, 0), (0, seqLen - len( vList ) + 1)), 'constant' ) ) )
                        retY   =  np.vstack( ( retY, to_categorical( vList[ -1: ], len( self.vocab ) ) ) )

        if returnTrainingData:
            return ( retX, retY )
        else:
            return None


    def vocab2Midi( self, vData, noteShift = 64 ):
        pattern  =  midi.Pattern( )

        track  =  midi.Track( )
        track.append( midi.SetTempoEvent( tick = 0, data = [ 7, 161, 32 ] ) )
        track.append( midi.TimeSignatureEvent( tick = 0, data = [ 4, 2, 24, 8 ] ) )
        track.append( midi.EndOfTrackEvent( tick = 0 ) )
        pattern.append( track )

        track  =  midi.Track( )
        track.append( midi.ProgramChangeEvent( tick = 0, data = [ 0 ] ) )

        tpe       =  int( pattern.resolution / 4 )
        #print 'tpe', tpe
        nextTick  =  0

        for vIdx in vData:
            e  =  self.vocab[ vIdx ]
            #print '\ne', e

            immediately  =  [ ]
            justAfter    =  [ ]

            if e is not None:
                for note in e:
                    #print 'note', note
                    w      =  e[ note ]
                    #print 'w', w
                    note  +=  noteShift

                    if w == OFF_ON:
                        immediately.append( midi.NoteOnEvent( pitch = note, velocity = 100 ) )
                    elif w == ON_OFF:
                        immediately.append( midi.NoteOffEvent( pitch = note ) )
                    elif w == ON_OFF_ON:
                        immediately.append( midi.NoteOffEvent( pitch = note ) )
                        justAfter.append( midi.NoteOnEvent( pitch = note, velocity = 100 ) )
                    elif w == OFF_ON_OFF:
                        immediately.append( midi.NoteOnEvent( pitch = note, velocity = 100 ) )
                        justAfter.append( midi.NoteOffEvent( pitch = note ) )

            #print 'immediately'


            for i, event in enumerate( immediately ):
                if i == 0:
                    event.tick  =  nextTick
                else:
                    event.tick  =  0
                #print 'event', event
                track.append( event )

            if immediately != [ ]:
                nextTick  =  0
            #print 'justAfter'

            for i, event in enumerate( justAfter ):
                if i == 0:
                    event.tick  =  nextTick
                else:
                    event.tick  =  0
                #print 'event', event
                track.append( event )

            if justAfter != [ ]:
                nextTick  =  0

            nextTick  +=  tpe
            #print 'nextTick', nextTick


        track.append( midi.EndOfTrackEvent( tick = 0 ) )

        pattern.append( track )
        return pattern

    #############
    # TODO make custom Keras layer to put embedding mid-layerstack. Currently only allowed to use as first layer.
    def genModel( self, inputLength ):
        model = Sequential( )
        model.add( Embedding( len( self.vocab ), 25, mask_zero = True, input_length = inputLength, dropout = 0.5 ) )
        #model.add( LSTM( 100, return_sequences = True, stateful = False ) )
        model.add( LSTM( 100, stateful = False, dropout_W = 0.5, dropout_U = 0.5 ) )
        for i in range( 10 ):
            model.add( Highway( activation = 'relu' ) )
        model.add( Dense( len( self.vocab ), activation = 'softmax' ) )
        rmsProp  =  RMSprop( lr = 0.001 )
        model.compile( optimizer = rmsProp, loss = 'categorical_crossentropy', metrics = [ 'accuracy' ] )
        return model

    def genLayers( self, inputLength ):
        layers = [ ]
        layers.append( Input( shape = (inputLength,) ) )
        layers.append( Embedding( len( self.vocab ), 25, mask_zero = True ) )
        layers.append( LSTM( 100, stateful = False ) )
        for i in range( 10 ):
            layers.append( Highway( activation = 'relu' ) )
        layers.append( Dense( len( self.vocab ), activation = 'softmax' ) )
        return layers

    def genFuncModel( self, layers ):
        layer  =  inputs  =  layers[ 0 ]

        for l in layers[ 1: ]:
            layer  =  l( layer )

        model  =  Model( input = inputs, output = layer )
        rmsProp  =  RMSprop( lr = 0.0001 )
        model.compile( optimizer = rmsProp, loss = 'categorical_crossentropy', metrics = [ 'accuracy' ] )

        return model

    def genFuncModel2( self, layers ):
        layer  =  inputs  =  layers[ 0 ]

        for l in layers[ 1: ]:
            layer  =  l( layer )

        layer  =  Lambda( lambda x: K.argmax( x ), output_shape = (1, ) )( layer )

        if type( layers[ 1 ] ) == Embedding:
            layer  =  layers[ 1 ]( layer )

        model  =  Model( input = inputs, output = layer )
        rmsProp  =  RMSprop( lr = 0.001 )
        model.compile( optimizer = rmsProp, loss = 'mean_squared_error' )

        return model

    def convertLabels( self, labels, layer ):
        shape  =  ( labels.shape[ 0 ], 1, layer.output_shape[ -1 ] )
        ret    =  np.zeros( shape )

        for i, label in enumerate( labels ):
            ret[ i, 0, : ] = layer.call( np.array( np.argmax( label ) ) ).eval( )

        return ret

    #def genFuncModel( self, batchShape ):
    #    print 'genFuncModel ('
    #    print '\tbatchShape', batchShape
    #    print ')'

    #    inputs  =  Input( batch_shape = batchShape )
    #    embed   =  Embedding( len( self.vocab ), 25, mask_zero = True )( inputs )
    #    layer   =  LSTM( 25, stateful = True )( embed )
    #    for i in range( 10 ):
    #        layer  =  Highway( activation = 'relu' )( layer )
    #    predictions  =  Dense( len( self.vocab ), activation = 'softmax' )( layer )

    #    model    =  Model( input = inputs, output = predictions )
    #    rmsProp  =  RMSprop( lr = 0.002 )
    #    model.compile( optimizer = rmsProp, loss = 'categorical_crossentropy', metrics = [ 'accuracy' ] )

    #    return model


    #def genFuncModel2( self, model ):

    #    embedLayer  =  Embedding( len( self.vocab ), 25, mask_zero = True )

    #    inputs  =  Input( batch_shape = model.input_shape )
    #    embed  =  embedLayer( inputs )
    #    layer   =  LSTM( 25, stateful = True )( embed )
    #    for i in range( 10 ):
    #        layer  =  Highway( activation = 'relu' )( layer )
    #    predictions  =  Dense( len( self.vocab ), activation = 'softmax' )( layer )
    #    argmax  =  Lambda( lambda x: K.argmax( x ), output_shape = (1, ) )( predictions )
    #    embedOut  =  embedLayer( argmax )

    #    newModel  =  Model( input = inputs, output = embedOut )
    #    rmsProp  =  RMSprop( lr = 0.002 )
    #    newModel.compile( optimizer = rmsProp, loss = 'mean_squared_error', metrics = [ 'accuracy' ] )

    #    return newModel


    # for stateful RNNs
    def formatData(self, data):
        if not data:
            return ([], [])
        d1 = len(data)
        d2 = max([len(x) for x in data]) - 1
        d3 = len(self.vocab)
        print 'd1 d2 d3', d1, d2, d3

        fData =   np.zeros((d1, d2), dtype='int32')
        fLabels = np.zeros((d1, d2, d3), dtype='int32')

        for i, track in enumerate(data):
            fData[i, :len(track) - 1] = track[:-1]
            fLabels[i, :len(track) - 1, :] = to_categorical([[x] for x in track[1:]], d3)

        fData =   np.reshape( fData.T,                           (d1 * d2, 1 ))
        fLabels = np.reshape( np.transpose(fLabels, (1, 0, 2)),  (d1 * d2, d3))

        return (fData, fLabels)


    def midiRip( self, midiFile, visDebug = False ):
        global ec
        pattern = midi.read_midifile( midiFile )
        offset = 0

        tracks = [ ]
        for i, track in enumerate( pattern ):
            notes = [ ]
            time = 0
            notesOn = {}
            for e in track:
                time  +=  e.tick
                if isinstance( e, midi.NoteOnEvent ) and e.velocity > 0:
                    key = ( e.channel, e.pitch - offset )
                    notesOn[ key ] = time
                elif isinstance( e, midi.NoteOffEvent ) or ( isinstance( e, midi.NoteOnEvent ) and e.velocity == 0 ):
                    key = ( e.channel, e.pitch - offset )
                    if key in notesOn:
                        notes.append( {
                            't': notesOn[ key ] / float( pattern.resolution ),
                            'd': ( time - notesOn[ key ] ) / float( pattern.resolution ),
                            'n': e.pitch - offset,
                            'c': e.channel,
                        } )
            tracks.append( notes )

        if visDebug:
            self.visNotes( [ track for track in tracks if len(track) > 0 ], path.join( THIS_PATH, 'vis_debug', path.basename( midiFile ) ) )

        return tracks

    def notesLimits( self, notes ):
        firstTime = None
        lastTime = None
        for note in notes:
            if firstTime == None or note['t'] < firstTime:
                firstTime = note['t']
            if lastTime == None or lastTime < note['t'] + note['d']:
                lastTime = note['t'] + note['d']
        return ( firstTime, lastTime )

    def vocabDiff( self, v, e ):
        d1 = len( set( v.keys() ) - set( e.keys() ) )
        d2 = len( set( e.keys() ) - set( v.keys() ) )
        d3 = sum( [ v[i] != e[i] for i in set( v.keys() ).intersection( set( e.keys() ) ) ] )
        return ( d1 + d2 ) * 100 + d1 * 10 + d3

    ###############
    #
    # returns array of indices into self.vocab
    #
    ###############
    def vocabularize( self, notes, addNew = True, missed = None, visDebug = False ):

        # tuple - units of quarter notes
        ( firstTime, lastTime ) = self.notesLimits( notes )

        smallestBad = None
        largestGood = None
        goodEData = None
        res = 0.25 # quarter notes per event point
        while True:
            eData = []
            # print 'res', res

            # init eData with blanks
            for i in range( int( ( lastTime - firstTime ) / res ) + 1 ):
                eData.append({})

            for note in notes:
                startIdx = int( ( note['t'] - firstTime ) / res )
                stopIdx = int( ( note['t'] + note['d'] - firstTime ) / res )

                n = note['n']

                if n not in eData[startIdx]:
                    eData[ startIdx ][ n ] = []
                e = ( NOTE_ON, note['t'] - firstTime - int( startIdx * res ) )
                if e not in eData[ startIdx ][ n ]:
                    eData[ startIdx ][ n ].append( e )

                for i in range(startIdx + 1, stopIdx):
                    if n not in eData[ i ]:
                        eData[ i ][ n ] = []
                    e = (NOTE_HOLD, 0)
                    if e not in eData[ i ][ n ]:
                        eData[ i ][ n ].append( e )

                if n not in eData[ stopIdx ]:
                    eData[ stopIdx ][ n ] = []
                e = ( NOTE_OFF, note['t'] + note['d'] - firstTime - int( stopIdx * res ) )
                if e not in eData[ stopIdx ][ n ]:
                    eData[ stopIdx ][ n ].append( e )

            lens = {}
            for e in eData:
                for n in e:
                    l = len(e[n])
                    if l not in lens:
                        lens[l] = 0
                    lens[l] += 1

            r1 = float( sum( [lens[x] for x in lens if x > 1] ) ) / sum( [lens[x] for x in lens] )
            r2 = float( sum( [lens[x] for x in lens if x > 2] ) ) / sum( [lens[x] for x in lens] )
            if ( r1 > 0.05 or r2 > 0.01 ):
                if smallestBad == None or res < smallestBad:
                    smallestBad = res
                res /= 2.0
            else:
                if largestGood == None or res > largestGood:
                    largestGood = res
                res *= 2.0
                goodEData = eData

            if smallestBad and largestGood and goodEData and smallestBad == largestGood * 2.0:
                eData = goodEData
                res = largestGood
                break

        vData = []
        idx = 0
        for e in eData:
            for n in e:
                e[n] = [ x[0] for x in sorted( e[n], key = lambda y: y[1] ) ]

            if e in self.vocab:
                k = self.vocab.index(e)
            elif addNew:
                self.vocab.append( e.copy() )
                k = len(self.vocab) - 1
            else:
                a = [ ( i, self.vocabDiff( x, e ) ) for i, x in enumerate( self.vocab ) if i > 0 ]
                a.sort( key = lambda x: x[1] )
                k = a[0][0]
                if missed != None:
                    missed[0] += 1
                #print 'unknown, maybe', [(x[0], self.vocab[x[0]]) for x in a[:3]]
                #print 'idx', idx, 'e', e, 'vocab[k]', self.vocab[k]
            idx += 1
            vData.append( k )

        if visDebug:
            self.visVData( vData, res )

        #print 'res:', res
        return vData

    def predictSequence(self, model, data, num = 1):
        inSeq = data[:]
        out = []
        # todo: different check for length of out?
        while len(out) < num:
            modelIn = np.array(inSeq).reshape((1, -1))
            modelOut = model.predict(modelIn, batch_size = 1)
            inSeq.append(np.argmax(modelOut, 1))
            if out == []:
                out = modelOut
            else:
                out = np.append(out, modelOut, 0)
        return out

    def midiOut(self, vData, fileName, resolution):
        outPattern = midi.Pattern()
        outPattern.resolution = resolution
        track = midi.Track()
        track.append(midi.TrackNameEvent(tick=0, text='JOSH'))
        track.append(midi.SetTempoEvent(tick=0, bpm=120))
        tick = 0
        for k in tData:
            e = self.vocab[k]
            tick += res
            l = max([len(e[x]) for x in e])
            for t in range(l):
                if tick == 0:
                    tick = res / l
                for f in e:
                    if t < len(e[f]):
                        if e[f][t] == NOTE_ON:
                            track.append(midi.NoteOnEvent(pitch = f, tick = tick, velocity = 127))
                            tick = 0
                        elif e[f][t] == NOTE_OFF:
                            track.append(midi.NoteOffEvent(pitch = f, tick = tick, velocity = 127))
                            tick = 0
        track.append(midi.EndOfTrackEvent(tick = 0))
        outPattern.append(track)
        midi.write_midifile(fileName, outPattern)

    # for non-stateful RNNs
    #def formatData(self, data, minSeq, maxSeq):
    #    nData = sum([(min(maxSeq + 1, len(x)) - minSeq) + (len(x) - maxSeq - 1) for x in data]) * 2
    #    fData = np.zeros((nData, maxSeq))
    #    fLabels = np.zeros((nData, 1))
    #    p = 0
    #    for i in data:
    #        for j in range(minSeq, min(maxSeq + 1, len(i))):
    #            fData[p, :j] = i[:j]
    #            fLabels[p] = i[j]

    #            fData[p + 1, :j] = list(reversed(i[-j:]))
    #            fLabels[p + 1] = i[-j - 1]
    #            p += 2
    #        for j in range(1, len(i) - maxSeq):
    #            fData[p] = i[j : maxSeq + j]
    #            fLabels[p] = i[maxSeq + j]

    #            fData[p + 1] = list(reversed(i[-maxSeq - j : -j]))
    #            fLabels[p + 1] = i[-maxSeq - j - 1]
    #            p += 2
    #    fLabels = to_categorical(fLabels.astype('int'), len(self.vocab))
    #    return (fData, fLabels)

    # iter-10
    #def genModel(self, batchShape):
    #    input = Input(batch_shape = batchShape, dtype = 'int32', name = 'input')
    #    xs = Embedding(len(self.vocab), 32, mask_zero = True, batch_input_shape = batchShape)(input)
    #    xs = LSTM(32, return_sequences = True, stateful = True)(xs)
    #    x = LSTM(32, stateful = True)(xs)
    #    for i in range(10):
    #        x = Highway(activation = 'relu')(x)
    #    aux_out1 = Dense(len(self.vocab), activation = 'softmax', name = 'aux_out1')(x)
    #    xs = LSTM(32, return_sequences = True, stateful = True)(xs)
    #    x = LSTM(32, stateful = True)(xs)
    #    for i in range(10):
    #        x = Highway(activation = 'relu')(x)
    #    aux_out2 = Dense(len(self.vocab), activation = 'softmax', name = 'aux_out2')(x)
    #    xs = LSTM(32, return_sequences = True, stateful = True)(xs)
    #    x = LSTM(32, stateful = True)(xs)
    #    for i in range(10):
    #        x = Highway(activation = 'relu')(x)
    #    main_out = Dense(len(self.vocab), activation = 'softmax', name = 'main_out')(x)
    #    model = Model(input = input, output = [aux_out1, aux_out2, main_out])
    #    model.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'], loss_weights = {'aux_out1': 0.2, 'aux_out2': 0.2, 'main_out': 1})
    #    return model

    #def genModel(self, batchShape):
    #    input = Input(batch_shape = batchShape, dtype = 'int32', name = 'input')
    #    x = Embedding(len(self.vocab), 32, mask_zero = True, batch_input_shape = batchShape)(input)
    #    x = LSTM(32, return_sequences = True, stateful = True)(x)
    #    for i in range(10):
    #        x = TimeDistributed(Highway(activation = 'relu'))(x)
    #    aux_out1 = TimeDistributed(Dense(len(self.vocab), activation = 'softmax'), name = 'aux_out1')(x)
    #    x = LSTM(32, return_sequences = True, stateful = True)(x)
    #    for i in range(10):
    #        x = TimeDistributed(Highway(activation = 'relu'))(x)
    #    main_out = TimeDistributed(Dense(len(self.vocab), activation = 'softmax'), name = 'main_out')(x)
    #    model = Model(input = input, output = [aux_out1, main_out])
    #    model.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'], loss_weights = {'aux_out1': 0.2, 'main_out': 1})
    #    return model

    def rebatchModel(self, model, newBatch):
        struct = json.loads(model.to_json())
        for l in struct['config']:
            if 'batch_input_shape' in l['config']:
                l['config']['batch_input_shape'][0] = newBatch
        model2 = model_from_json(json.dumps(struct))
        return model2

#mk = MidiKeras(range(40))
#(b, c) = mk.formatData([range(30),range(4,34)])
#model = mk.genModel((2, 1))
#for i in range(100):
#    for j in range(len(b[0,:,0])):
#        model.train_on_batch(b[:,j,:], c[:,j,:])
#    print i
#    model.reset_states()
