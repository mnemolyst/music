var fs = require('fs');
var Png = require('png').Png;
var MidiFile = require('./public/javascripts/lib/jasmid/midifile');

var fileIn = process.argv[2];
var fileRE = /(.*)\.mid$/;

fs.readFile(fileIn, function(err, data) {
    var timeDiv = 4;
    var tsNum = null;
    var tsDen = null;
    var tempo = 0.5;
    var tracks = [];
    var midifile = MidiFile(data);

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
                            n: event.noteNumber - 69,
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
                    tempo = event.microsecondsPerBeat * 0.000001;
                    break;
            }
        }
        tracks[i].notes = notes;
    }

    var secondsPerTick = tempo / midifile.header.ticksPerBeat
    var track = tracks[1];

    function dist(a, b) {
        var nd = track.notes[a].n - track.notes[b].n;
        var td = (track.notes[a].t + track.notes[a].d) * 0.5 - (track.notes[b].t + track.notes[b].d) * 0.5;
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

    var dbIn = {
        name: track.name,
        notes: track.notes,
        staff: {
            noteLines: [5, 3, 1, -1, -3, -7, -9, -11, -13, -15],
            keySig: [0, 0, 0, 0, 0, 0, 0],
            timeDiv: timeDiv,
        },
        ticksPerBeat: midifile.header.ticksPerBeat,
        tempo: tempo,
    };

    //fs.writeFileSync('testdb', JSON.stringify(dbIn));

    var tpb = midifile.header.ticksPerBeat;
    var oneMeasure = tpb * tsNum / tsDen; // one measure's worth of ticks
    var silhouetteLimit1 = 0.8;
    var silhouetteLimit2 = 0.4;

    var colors = [
        [0xff, 0xff, 0],
        [0xff, 0, 0],
        [0, 0, 0xff],
        [0, 0xff, 0],
        [0xff, 0, 0xff],
    ];

    //for (var n = 0; n < 10; n++) {
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
            //var trainType = 0;
        } else {
            //var trainType = Math.floor(Math.random() * 4); // 0: all notes before; 1: all before, some after; 2: single melody before; 3: single melody before, some after; 4: all notes before and after except some same-melody
        }
            var trainType = 4;

        if (trainType === 0 || trainType === 1) { // if we are doing single-melody training
            c = [ [] ];
            for (var i = 0; i < track.notes.length; c[0].push(i++));
        } else {
            var c2, stepSize = 5;
            do {
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
            do {
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

        // build training set
        var trainNotes = [];
        var trainStart = Math.random() * (trainNote.t - oneMeasure);
        var trainStop = trainNote.t + trainNote.d + oneMeasure + (Math.random() * (track.lastNoteEnd - trainNote.t - trainNote.d - oneMeasure));
        var trainGapEnd = trainNote.t + Math.random() * (trainStop - trainNote.t);
        var trainMelody = null;
        for (var i = 0; i < c.length; i++) {
            if (c[i].indexOf(tni) !== -1) {
                trainMelody = i;
                break;
            }
        }

        // 0: all notes before; 1: all before, some after; 2: single melody before; 3: single melody before, some after; 4: all notes before and after except some same-melody

        var firstT = trainNote.t;
        var lastT = trainNote.t + trainNote.d;
        for (var i = 0; i < track.notes.length; i++) {
            var note = track.notes[i];
            if (
                ! (note.t < trainStart || trainStop < note.t) // outside training range
                && ! ((trainType === 0 || trainType === 2) && trainNote.t < note.t) // training type excludes notes after training note
                && ! ((trainType === 2 || trainType === 3) && c[trainMelody].indexOf(i) === -1) // in wrong melody
                && ! ((trainType === 1 || trainType === 3 || (trainType === 4 && c[trainMelody].indexOf(i) !== -1)) && trainNote.t < note.t && note.t < trainGapEnd) // inside gap range
                && ! (tni === i) // and of course
            ) {
                trainNotes.push(i);

                if (note.t < firstT) {
                    firstT = note.t;
                }
                if (lastT < note.t + note.d) {
                    lastT = note.t + note.d;
                }
            }
        }
        console.log('trainType', trainType);
        console.log('firstT', firstT);
        console.log('trainT', trainNote.t);
        console.log('lastT', lastT);

        var hScale = secondsPerTick * 20;
        var vScale = 3;
        var bpp = 1; // bytes per pixel
        var rows = 128 * vScale; // vScale sub-semitones per MIDI note
        var cols = Math.ceil((lastT - firstT) * hScale);
        //var cols = Math.ceil(track.lastNoteEnd * hScale);
        var imageBuf = new Buffer(rows * cols * bpp);
        imageBuf.fill(0);
        for (var i = 0; i < trainNotes.length; i++) {
            var note = track.notes[trainNotes[i]];
            var lc = Math.round((note.t - firstT) * hScale);
            var uc = Math.round((note.t + note.d - firstT) * hScale);
            for (var j = lc; j < uc; j++) {
                colors: for (var k = 0; k < bpp; k++) {
                    idx = ((rows - (note.n + 69) * vScale - 2) * cols + j) * bpp + k;

                    //if (trainNotes[i] === tni) {
                    //    imageBuf[idx] = colors[0][k];
                    //    continue colors;
                    //} else {
                    //    for (var l = 0; l < c.length; l++) {
                    //        if (c[l].indexOf(trainNotes[i]) !== -1) {
                    //            imageBuf[idx] = colors[l+1][k];
                    //            continue colors;
                    //        }
                    //    }
                    //}
                    imageBuf[idx] = Math.floor(note.v * (255 / 127));
                }
            }
        }
        // training note indicator line
        for (var i = 0; i < rows; i++) {
            imageBuf[Math.round(i * cols + (trainNote.t - firstT) * hScale)] = 255;
        }
        //var png = new Png(imageBuf, cols, rows, 'rgb');
        var png = new Png(imageBuf, cols, rows, 'gray', 8);
        png.encode(function(image) {
            fs.writeFileSync(fileIn.replace(fileRE, '$1.train.' + '1'), image);
        });
    //}
});
