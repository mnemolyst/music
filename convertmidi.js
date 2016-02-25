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
        var td = track.notes[a].t - track.notes[b].t;
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
        console.log('cluster', 'x', x, 'med', med);
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
        console.log('findmed', 'c', c);
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
            console.log('c', c);
            oldMed = med;
            med = findMed(c);
            console.log('med', med);
        } while (diffMed(oldMed, med));

        return c;
    }

    function minSilhouette(x, c) {
        var min = 1;
        for (var i = 0; i < x.length; i++) {
            var thisAvg, minOtherAvg = null;
            for (var j = 0; j < c.length; j++) {
                var sumD = 0;
                var isInThis = false;
                for (var k = 0; k < c[j].length; k++) {
                    if (i === c[j][k]) {
                        isInThis = true;
                        // dist() is zero
                    } else {
                        sumD += dist(i, c[j][k]);
                    }
                }
                var avgD = sumD / k;
                if (isInThis) {
                    thisAvg = avgD;
                } else if (minOtherAvg === null || avgD < minOtherAvg) {
                    minOtherAvg = avgD;
                }
            }
            var s = (minOtherAvg - thisAvg)/Math.max(thisAvg, minOtherAvg);
            if (s < min) {
                min = s;
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

    //c onsole.log(midifile.header);
    //c onsole.log(midifile.tracks);
    //c onsole.log(tracks[1].nbp);
    //c onsole.log(dbIn);

    //fs.writeFileSync('testdb', JSON.stringify(dbIn));

    var hScale = secondsPerTick * 20;
    var vScale = 3;
    var bpp = 3; // bytes per pixel
    var rows = 128 * vScale; // vScale sub-semitones per MIDI note
    var cols = Math.ceil(track.lastNoteEnd * hScale);
    var tpb = midifile.header.ticksPerBeat;
    var oneMeasure = tpb * tsNum / tsDen; // one measure's worth of ticks
    var silhouetteLimit1 = 0.5;
    var silhouetteLimit2 = 0.5;

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

        // TODO see how many melodic lines we can find within one beat of trainNote
        var testNotes = [], maxK = 2;
        //for (var i = 0; i < track.notes.length; i++) {
        //    if ((beforeT <= track.notes[i].t) && (track.notes[i].t < afterT)) {
        //        testNotes.push(i);
        //    }
        //}
        for (var i = Math.max(0, tni - 3 * maxK); i < Math.min(track.notes.length, tni + 3 * maxK); i++) {
            testNotes.push(i);
        }
        //do { TODO find best K / best s
            var tries = 1, c, s;
            do {
                c = kMed(testNotes, maxK);
                console.log(c);
            } while ((s = minSilhouette(testNotes, c)) < silhouetteLimit1 && tries++ < 10);
        //} while (s >= silhouetteLimit1 && maxK++ <= 4);

        if (s < silhouetteLimit1) {
            var trainType = 0;
        } else {
            //var trainType = Math.floor(Math.random() * 4); // 0: all notes before, 1: single melody before, 2: single melody before, some after, 3: all notes before and after except some same-melody
            var trainType = 1;
        }
        console.log(trainType);

        if (trainType !== 0) {
            var c2, cSeeds = [];
            do {
                testNotes = [], tries = 1;
                var firstC = Math.min(c[0][0], c[1][0]);
                var secondC = Math.max(c[0][0], c[1][0]);
                cSeeds = cSeeds.concat(firstC, secondC);
                for (var i = Math.max(0, firstC - 5 * maxK); i < secondC; i++) {
                    testNotes.push(i);
                }
                c2 = cluster(testNotes, [c[0][0], c[1][0]]);
                s = minSilhouette(testNotes, c2);
                if (s >= silhouetteLimit2) {
                    for (var i = 0; i < c2.length; i++) {
                        for (var j = c2[i].length - 1; j > 0; j--) {
                            if (c[i].indexOf(c2[i][j]) === -1) {
                                c[i].unshift(c2[i][j]);
                            }
                        }
                    }
                }
            } while (s >= silhouetteLimit2 && firstC > 5 * maxK);
        }

        // build training set
        //var trainMelody = null;
        //for (var i = 0; i < c.length; i++) {
        //    if (c[i].indexOf(tni) !== -1) {
        //        trainMelody = i;
        //        break;
        //    }
        //}
        //var trainStart = Math.random() * (trainNote.t - oneMeasure);
        //var trainStop = trainNote.t + oneMeasure + (Math.random() * (lastNoteEnd - trainNote.t - oneMeasure));
        //var trainGap = trainNote.t + Math.random() * 2 * oneMeasure;
        //var trainNotes = [];
        //for (var i = 0; i < track.notes.length; i++) {
        //    var note = track.notes[i];
        //    if (note.t < trainStart || trainStop < note.t) {
        //        continue;
        //    }
        //    if ((trainType == 0 || trainType == 2) && 
        //    trainNotes.push(note);
        //}

        var imageBuf = new Buffer(rows * cols * 3);
        imageBuf.fill(0);
        for (var i = 0; i < track.notes.length; i++) {
            var note = track.notes[i];
            for (var j = Math.round(note.t * hScale); j < Math.round((note.t + note.d) * hScale); j++) {
                // colors
                for (var k = 0; k < 3; k++) {
                    imageBuf[((rows - (note.n + 69) * vScale - 2) * cols + j) * bpp + k] = Math.floor(note.v * (255 / 127));

                    if (i === tni) {
                        imageBuf[((rows - (note.n + 69) * vScale - 2) * cols + j) * bpp + k] = colors[0][k];
                    //} else if (cSeeds.indexOf(i) !== -1) {
                    //    imageBuf[((rows - (note.n + 69) * vScale - 2) * cols + j) * bpp + k] = colors[3][k];
                    } else {
                        for (var l = 0; l < c.length; l++) {
                            if (c[l].indexOf(i) !== -1) {
                                imageBuf[((rows - (note.n + 69) * vScale - 2) * cols + j) * bpp + k] = colors[l+1][k];
                            }
                        }
                    }
                }
            }
        }
        var png = new Png(imageBuf, cols, rows, 'rgb');
        //var png = new Png(imageBuf, cols, rows, 'gray', 8);
        png.encode(function(image) {
            fs.writeFileSync(fileIn.replace(fileRE, '$1.train.' + '1'), image);
        });
    //}
});
