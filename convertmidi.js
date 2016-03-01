var fs = require('fs');
var Png = require('png').Png;
var midiFile = require('./public/javascripts/lib/jasmid/midifile');
var childProcess = require('child_process');
//var p = require('promise-extended');
//var Promise = p.Promise;

var fileIn = process.argv[2];
var fileRE = /^(.*)\.mid$/;

fs.readFile(fileIn, function(err, data) {
    var timeDiv = 4;
    var tsNum = null;
    var tsDen = null;
    var tempo = 0.5;
    var tracks = [];
    var midifile = midiFile(data);

    for (var i = 0; i < midifile.tracks.length; i++) {
        tracks[i] = {
            name: 'Untitled',
            lastNoteEnd: 0,
        };
        var notes = [];
        var notesOn = {};
        var time = 0;
        //var noteStarted = false;
        for (var j = 0; j < midifile.tracks[i].length; j++) {
            var event = midifile.tracks[i][j];
            //var deltaBeat = event.deltaTime / midifile.header.ticksPerBeat;
            time += event.deltaTime;
            switch (event.subtype) {
                case 'noteOn':
                    //if (! noteStarted) {
                    //    time = 0;
                    //}
                    var key = event.channel + '-' + event.noteNumber;
                    notesOn[key] = time;
                    //noteStarted = true;
                    break;
                case 'noteOff':
                    var key = event.channel + '-' + event.noteNumber;
                    if (notesOn.hasOwnProperty(key)) {
                        notes.push({
                            t: notesOn[key],
                            d: time - notesOn[key],
                            n: event.noteNumber,
                            v: event.velocity,
                        });
                        if (time > tracks[i].lastNoteEnd) {
                            tracks[i].lastNoteEnd = time;
                        }
                    }
                    break;
                case 'trackName':
                    tracks[i].name = event.text;
                    break;
                case 'timeSignature':
                    tsNum = event.numerator;
                    tsDen = Math.pow(2, event.denominator - 2);
                    break;
                case 'setTempo':
                    tempo = event.microsecondsPerBeat * 0.000001; // seconds per beat
                    break;
            }
        }
        tracks[i].notes = notes;
    }

    var ticksPerBeat = midifile.header.ticksPerBeat;
    //var oneMeasure = ticksPerBeat * tsNum / tsDen; // one measure's worth of ticks
    var secondsPerTick = tempo / ticksPerBeat;
    var track = tracks[1];

    function dist(a, b) {
        var nd = track.notes[a].n - track.notes[b].n;
        var td = (track.notes[a].t + track.notes[a].d - track.notes[b].t - track.notes[b].d) * 0.5;
        return Math.abs(10000 * nd * nd * nd) + td * td;
    }

    function shuffleArray(array) {
        array = array.slice();
        for (var i = array.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var temp = array[i];
            array[i] = array[j];
            array[j] = temp;
        }
        return array;
    }

    function cluster(x, med) { // med is array of indices into x
        var c = []; // clusters
        for (var j = 0; j < med.length; j++) {
            c[j] = [];
        }
        for (var i = 0; i < x.length; i++) {
            var minD = null, minJ = 0;
            for (var j = 0; j < med.length; j++) {
                var d = dist(x[i], med[j]);
                if (minD === null || d < minD) {
                    minD = d;
                    minJ = j; // index into med
                }
            }
            if (minD !== null) {
                c[minJ].push(x[i]) // put index into x in cluster minJ
            }
        }
        return c;
    }

    function findMed(c) {
        var med = [];
        for (var i = 0; i < c.length; i++) { // for each cluster...
            var minD = null, minJ = 0;
            for (var j = 0; j < c[i].length; j++) { // for each potential medioid...
                var sumD = 0;
                for (var k = 0; k < c[i].length; k++) { // sum the distances to all other points
                    if (j !== k) {
                        sumD += dist(c[i][j], c[i][k]);
                    }
                }
                if (minD === null || sumD < minD) {
                    minD = sumD;
                    minJ = j; // c[i][j] is the best medioid so far for cluster i
                }
            }
            if (minD !== null) {
                med[i] = c[i][minJ];
            }
        }
        return med;
    }

    function diffMed(med1, med2) {
        if (med1.length !== med2.length) {
            return true;
        }
        for (var i = 0; i < med1.length; i++) {
            if (med1[i] !== med2[i]) {
                return true;
            }
        }
        return false;
    }

    function kMed(x, k) {
        var med = shuffleArray(x).slice(0, k);

        var c, oldMed;

        do {
            c = cluster(x, med);
            oldMed = med;
            med = findMed(c);
        } while (diffMed(oldMed, med));

        return c;
    }

    function minSilhouette(c) {
        var min = 1;
        for (var i = 0; i < c.length; i++) {
            for (var j = 0; j < c[i].length; j++) {
                var thisSum = 0;
                for (var k = 0; k < c[i].length; k++) {
                    if (j !== k) {
                        thisSum += dist(c[i][j], c[i][k]);
                    }
                }
                var thisAvg = thisSum / k, minOtherAvg = null;
                for (var l = 0; l < c.length; l++) {
                    if (i !== l) {
                        var oSum = 0;
                        for (var m = 0; m < c[l].length; m++) {
                            oSum += dist(c[i][j], c[l][m]);
                        }
                        var oAvg = oSum / m;
                        if (minOtherAvg === null || oAvg < minOtherAvg) {
                            minOtherAvg = oAvg;
                        }
                    }
                }
                var s = (minOtherAvg - thisAvg)/Math.max(thisAvg, minOtherAvg);
                if (s < min) {
                    min = s;
                }
            }
        }
        return min;
    }

    //var dbIn = {
    //    name: track.name,
    //    notes: track.notes,
    //    staff: {
    //        noteLines: [5, 3, 1, -1, -3, -7, -9, -11, -13, -15],
    //        keySig: [0, 0, 0, 0, 0, 0, 0],
    //        timeDiv: timeDiv,
    //    },
    //    ticksPerBeat: midifile.header.ticksPerBeat,
    //    tempo: tempo,
    //};
    //fs.writeFileSync('testdb', JSON.stringify(dbIn));

    var silhouetteLimit1 = 0.8;
    var silhouetteLimit2 = 0.4;

    var colors = [
        [0xff, 0xff, 0],
        [0xff, 0, 0],
        [0, 0, 0xff],
        [0, 0xff, 0],
        [0xff, 0, 0xff],
    ];

    var childProcesses = [];
    var noteData = [];
    var timeData = [];
    var durationData = [];
    var protocCount = 0;
    for (var n = 0; n < 1; n++) {
        var tni = Math.floor(Math.random() * track.notes.length);
        var trainNote = track.notes[tni];

        var testNotes = [], maxK = 2;
        for (var i = Math.max(0, tni - 3 * maxK); i < Math.min(track.notes.length, tni + 3 * maxK); i++) {
            testNotes.push(i);
        }
        //do { TODO find best K / best s
            var tries = 1, c, s;
            do {
                c = kMed(testNotes, maxK);
            } while ((s = minSilhouette(c)) < silhouetteLimit1 && tries++ < 10);
        //} while (s >= silhouetteLimit1 && maxK++ <= 4);

        if (s < silhouetteLimit1) {
            var trainType = 0;
        } else {
            var trainType = Math.floor(Math.random() * 5); // 0: all notes before; 1: all before, some after; 2: single melody before; 3: single melody before, some after; 4: all notes before and after except some same-melody
        }

        if (trainType === 0 || trainType === 1) { // if we are doing single-melody training
            c = [ [] ];
            for (var i = 0; i < track.notes.length; c[0].push(i++));
        } else {
            var c2, stepSize = 5;
            do { // backward
                testNotes = [], tries = 1;
                var firstC = Math.min(c[0][0], c[1][0]);
                var secondC = Math.max(c[0][0], c[1][0]);
                notes: for (var i = Math.max(0, firstC - stepSize * maxK); i < secondC; i++) {
                    for (var j = 0; j < c.length; j++) {
                        if (c[j].indexOf(i) !== -1) {
                            continue notes;
                        }
                    }
                    testNotes.push(i);
                }
                if (testNotes.length === 0) {
                    break;
                }
                c2 = cluster(testNotes, [c[0][0], c[1][0]]);
                s = minSilhouette(c2);
                if (s >= silhouetteLimit2) {
                    stepSize++;
                    for (var i = 0; i < c2.length; i++) {
                        for (var j = c2[i].length - 1; j >= 0; j--) {
                            if (c[i].indexOf(c2[i][j]) === -1) {
                                c[i].unshift(c2[i][j]);
                            }
                        }
                    }
                }
            } while ((s >= silhouetteLimit2 || --stepSize > 1) && firstC >= 0);
            stepSize = 5;
            do { // and forward
                testNotes = [], tries = 1;
                var lastC = Math.max(c[0][c[0].length-1], c[1][c[1].length-1]);
                var secondC = Math.min(c[0][c[0].length-1], c[1][c[1].length-1]);
                notes: for (var i = secondC; i < Math.min(lastC + stepSize * maxK, track.notes.length); i++) {
                    for (var j = 0; j < c.length; j++) {
                        if (c[j].indexOf(i) !== -1) {
                            continue notes;
                        }
                    }
                    testNotes.push(i);
                }
                if (testNotes.length === 0) {
                    break;
                }
                c2 = cluster(testNotes, [c[0][c[0].length-1], c[1][c[1].length-1]]);
                s = minSilhouette(c2);
                if (s >= silhouetteLimit2) {
                    stepSize++;
                    for (var i = 0; i < c2.length; i++) {
                        for (var j = c2[i].length - 1; j >= 0; j--) {
                            if (c[i].indexOf(c2[i][j]) === -1) {
                                c[i].push(c2[i][j]);
                            }
                        }
                    }
                }
            } while ((s >= silhouetteLimit2 || --stepSize > 1) && lastC < track.notes.length);
        }

        var trainNotes = [];
        var trainStart = Math.random() * (trainNote.t - 4 * ticksPerBeat);
        var trainStop = trainNote.t + trainNote.d + 4 * ticksPerBeat + (Math.random() * (track.lastNoteEnd - trainNote.t - trainNote.d - 4 * ticksPerBeat));
        var trainGapEnd = trainNote.t + Math.random() * (trainStop - trainNote.t);
        var trainMelody = null;
        for (var i = 0; i < c.length; i++) {
            if (c[i].indexOf(tni) !== -1) {
                trainMelody = i;
                break;
            }
        }

        //XXX
        //trainNote = {n: 71, t: 3 * ticksPerBeat, d: ticksPerBeat, v: 127};
        //track.notes = [
        //    {n: 69, t: ticksPerBeat, d: ticksPerBeat, v: 127},
        //    {n: 70, t: 2 * ticksPerBeat, d: ticksPerBeat, v: 127},
        //    trainNote,
        //];
        // build training set
        var firstT = trainNote.t;
        var lastT = trainNote.t + trainNote.d;
        var lowN = trainNote.n;
        var highN = trainNote.n;
        var lastBeforeTrainNote = 0;
        for (var i = 0; i < track.notes.length; i++) {
            var note = track.notes[i];
            if ( // 0: all notes before; 1: all before, some after; 2: single melody before; 3: single melody before, some after; 4: all notes before and after except some same-melody
                ! (note.t < trainStart || trainStop < note.t) // outside training range
                && ! ((trainType === 0 || trainType === 2) && trainNote.t < note.t) // training type excludes notes after training note
                && ! ((trainType === 2 || trainType === 3) && c[trainMelody].indexOf(i) === -1) // in wrong melody
                && ! ((trainType === 1 || trainType === 3 || (trainType === 4 && c[trainMelody].indexOf(i) !== -1)) && trainNote.t < note.t && note.t < trainGapEnd) // inside gap range
                && ! (tni === i) // and of course
            ) {
                trainNotes.push(i);

                firstT = note.t < firstT ? note.t : firstT;
                lastT = lastT < note.t + note.d ? note.t + note.d : lastT;
                lowN = note.n < lowN ? note.n : lowN;
                highN = highN < note.n ? note.n : highN;
                if (lastBeforeTrainNote < i && i < tni) {
                    lastBeforeTrainNote = i;
                }
            }
        }

        var padL = Math.floor(Math.random() * 32 * ticksPerBeat);
        var padR = Math.floor(Math.random() * 32 * ticksPerBeat);
        var padB = Math.floor(Math.random() * 24); // units of MIDI notes
        var padT = Math.floor(Math.random() * 24);
        var indicatorOffset = Math.round(Math.random() * (trainNote.t - track.notes[lastBeforeTrainNote].t + 4 * ticksPerBeat));
        //var indicatorOffset = Math.round(0 *             (trainNote.t - track.notes[lastBeforeTrainNote].t + 4 * ticksPerBeat));

        var hScale = secondsPerTick * 20;
        var vScale = 3;
        var rows = (highN - lowN + 1 + padB + padT) * vScale; // vScale sub-semitones per MIDI note
        var cols = Math.ceil((Math.max(lastT, track.notes[lastBeforeTrainNote].t + indicatorOffset) - firstT + padL + padR) * hScale);
        var bpp = 1; // bytes per pixel
        var imageBuf = new Buffer(rows * cols * bpp);
        imageBuf.fill(0);
        for (var i = 0; i < trainNotes.length; i++) {
            var note = track.notes[trainNotes[i]];
            var lc = Math.round((note.t - firstT + padL) * hScale);
            var uc = Math.round((note.t + note.d - firstT + padL) * hScale);
            for (var j = lc; j < uc; j++) {
                colors: for (var k = 0; k < bpp; k++) {
                    idx = ((rows - (note.n - lowN + padB) * vScale - 2) * cols + j) * bpp + k;

                    if (bpp === 3) {
                        if (trainNotes[i] === tni) {
                            imageBuf[idx] = colors[0][k];
                        } else if (trainNotes[i] === lastBeforeTrainNote) {
                            imageBuf[idx] = colors[1][k];
                        } else {
                            for (var l = 0; l < c.length; l++) {
                                if (c[l].indexOf(trainNotes[i]) !== -1) {
                                    imageBuf[idx] = colors[l+2][k];
                                    continue colors;
                                }
                            }
                        }
                    } else {
                        imageBuf[idx] = Math.floor(note.v * (255 / 127));
                    }
                }
            }
        }
        // training note indicator line
        for (var i = 0; i < rows; i++) {
            for (var k = 0; k < bpp; k++) {
                var idx = Math.round(i * cols + (track.notes[lastBeforeTrainNote].t + indicatorOffset - firstT + padL) * hScale) * bpp + k;
                imageBuf[idx] = 255;
            }
        }

        //console.log(trainNote);

        //childProcesses[n] = (function() {
        //    var protoc = childProcess.spawn('/usr/local/bin/protoc', ['--encode=caffe.Datum', 'caffe.proto'], {
        //        cwd: process.cwd() + '/protobuf',
        //    });
        //    var trainProtobuf = 'channels: 1\nheight: ' + rows + '\nwidth: ' + cols + '\ndata: "';
        //    for (var i = 0; i < imageBuf.length; i++) {
        //        trainProtobuf += '\\x' + Number(imageBuf[i]).toString(16);
        //    }
        //    trainProtobuf += '"';
        //    return {
        //        protoc: protoc,
        //        trainProtobuf: trainProtobuf,
        //        data: function(callback) {
        //            protoc.stdout.on('data', function(data) { callback(data) });
        //        },
        //        end: function(callback) {
        //            protoc.stdout.on('end', callback);
        //        },
        //    }
        //})();

        // TODO
        //noteData[n] = String(trainNote.n - lowN + padB);
        //timeData[n] = String(trainNote.t - firstT - indicatorOffset);
        //durationData[n] = String(trainNote.d);

        if (bpp === 3) {
            var png = new Png(imageBuf, cols, rows, 'rgb');
        } else {
            var png = new Png(imageBuf, cols, rows, 'gray', 8);
        }
        (function() {
            var fileName = fileIn.replace(fileRE, '$1.train.' + n + '.png');
            png.encode(function(image) {
                fs.writeFileSync(fileName, image);
            });
        })();
    }

    var dataOut = [];
    var protocCount = 0;
    for (var i = 0; i < childProcesses.length; i++) {
        var idx = i;
        protocCount++;
        dataOut[idx] = '';
        childProcesses[i].data(function(data) {
            var dataBuf = new Buffer(data);
            for (var i = 0; i < dataBuf.length; i++) {
                if (dataBuf[i] < 16) {
                    dataOut[idx] += '\\x0' + Number(dataBuf[i]).toString(16);
                } else {
                    dataOut[idx] += '\\x' + Number(dataBuf[i]).toString(16);
                }
            }
        });
        childProcesses[i].end(function() {
            protocCount--;
            if (protocCount === 0) {
                var dataFile = fileIn.replace(fileRE, '$1.import.py');
                fs.writeFileSync(dataFile, 'import lmdb\nenv=lmdb.open(\'midi/lmdb/data\')\ntr=env.begin(None,None,True)\n');
                fs.appendFileSync(dataFile, 'tr.put(\'' + String(idx) + '\',\'' + dataOut[idx] + '\')\ntr.commit()\n');
                fs.appendFileSync(dataFile, 'env.close()\nenv=lmdb.open(\'midi/lmdb/notes\')\ntr=env.begin(None,None,True)\n');
                fs.appendFileSync(dataFile, 'tr.put(\'' + String(idx) + '\',\'' + noteData[idx] + '\')\ntr.commit()\n');
                fs.appendFileSync(dataFile, 'env.close()\nenv=lmdb.open(\'midi/lmdb/times\')\ntr=env.begin(None,None,True)\n');
                fs.appendFileSync(dataFile, 'tr.put(\'' + String(idx) + '\',\'' + timeData[idx] + '\')\ntr.commit()\n');
                fs.appendFileSync(dataFile, 'env.close()\nenv=lmdb.open(\'midi/lmdb/durations\')\ntr=env.begin(None,None,True)\n');
                fs.appendFileSync(dataFile, 'tr.put(\'' + String(idx) + '\',\'' + durationData[idx] + '\')\ntr.commit()\n');
            }
        });
        childProcesses[i].protoc.stdin.end(childProcesses[i].trainProtobuf);
    }

    //var notesFile = fileIn.replace(fileRE, '$1/train/$2.notes');
    //fs.writeFileSync(notesFile, noteData);

    //var timesFile = fileIn.replace(fileRE, '$1/train/$2.times');
    //fs.writeFileSync(timesFile, timeData);

    //var durationsFile = fileIn.replace(fileRE, '$1/train/$2.durations');
    //fs.writeFileSync(durationsFile, durationData);
});
