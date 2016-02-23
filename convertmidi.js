var fs = require('fs');
var Png = require('png').Png;
var MidiFile = require('./public/javascripts/lib/jasmid/midifile');

var fileIn = process.argv[2];
var fileRE = /(.*)\.mid$/;

function dist(a, b) {
    var nd = a.n - b.n;
    var td = a.t - b.t;
    return Math.abs(10000 * nd * nd * nd) + td * td;
}

function cluster(x, med) { // med is array of indices into x
    var c = []; // clusters
    for (var j = 0; j < med.length; j++) {
        c[j] = [];
    }
    for (var i = 0; i < x.length; i++) {
        var minD = null, minJ = 0;
        for (var j = 0; j < med.length; j++) {
            var d = dist(x[i], x[med[j]]);
            if (minD === null || d < minD) {
                minD = d;
                minJ = j; // index into med
            }
        }
        c[minJ].push(i) // put index into x in cluster minJ
    }
    return c;
}

function findMed(x, c) { // c in array of arrays of indices into x
    var med = [];
    for (var i = 0; i < c.length; i++) { // for each cluster...
        var minD = null, minJ = 0;
        for (var j = 0; j < c[i].length; j++) { // for each potential medioid...
            var sumD = 0;
            for (var k = 0; k < c[i].length; k++) { // sum the distances to all other points
                if (j !== k) {
                    sumD += dist(x[c[i][j]], x[c[i][k]]);
                }
            }
            if (minD === null || sumD < minD) {
                minD = sumD;
                minJ = j; // c[i][j] is the best medioid so far for cluster i
            }
        }
        med[i] = c[i][minJ];
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
    var med = [], newMed, c;
    for (var i = 0; i < k; i++) {
        do {
            var ri = Math.floor(Math.random() * x.length);
        } while (med.indexOf(ri) !== -1);
        med.push(ri);
        if (med.length === x.length) { // more categories than elements
            return med.map(function(el) { return [el] });
        }
    }

    var keepGoing = true;
    while (keepGoing) {
        c = cluster(x, med);
        newMed = findMed(x, c);
        if (diffMed(med, newMed)) {
            med = newMed;
        } else {
            keepGoing = false;
        }
    }

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
                } else {
                    sumD += dist(x[i], x[c[j][k]]);
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

fs.readFile(fileIn, function(err, data) {
    var timeDiv = 4;
    var tsNum = null;
    var tsDen = null;
    var tempo = 500000;
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
                    tempo = event.microsecondsPerBeat;
                    break;
            }
        }
        tracks[i].notes = notes;
    }

    var secondsPerTick = 0.000001 * tempo / midifile.header.ticksPerBeat
    var track = tracks[1];

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

    //console.log(midifile.header);
    //console.log(midifile.tracks);
    //console.log(tracks[1].nbp);
    //console.log(dbIn);

    //fs.writeFileSync('testdb', JSON.stringify(dbIn));

    var hScale = secondsPerTick * 20;
    var vScale = 3;
    var bpp = 3; // bytes per pixel
    var rows = 128 * vScale; // vScale sub-semitones per MIDI note
    var cols = Math.ceil(track.lastNoteEnd * hScale);
    var tpb = midifile.header.ticksPerBeat;
    var oneMeasure = tpb * tsNum / tsDen; // one measure's worth of ticks
    var silhouetteLimit = 0.4;

    //for (var n = 0; n < 10; n++) {
        var tni = Math.floor(Math.random() * track.notes.length);
        var trainNote = track.notes[tni];
        var trainRange = [];
        var leadIn = Math.random() * (trainNote.t - tpb) + tpb;

        // see how many melodic lines we can find within one beat of trainNote
        var testNotes = [];
        for (var i = 0; i < track.notes.length; i++) {
            if ((trainNote.t - tpb <= track.notes[i].t) && (track.notes[i].t <= trainNote.t + tpb)) {
                testNotes.push({oi: i, n: track.notes[i].n, t: track.notes[i].t});
            }
        }
        var maxK = 2;
        //do {
            var tries = 1, s;
            do {
                var c = kMed(testNotes, maxK);
            } while ((s = minSilhouette(testNotes, c)) < silhouetteLimit && tries++ < 20);
        //} while (s >= silhouetteLimit && maxK++ <= 4);
        console.log(s);

        // now see how far we can extend the melodic lines
        var beforeMul = 0, afterMul = 0, iter = 0, bestC;
        var beforeV = 1, afterV = 1, lastS;
        do {
            bestC = c.map(function(el) {
                return el.map(function(el) {
                    return testNotes[el].oi;
                });
            });

            var testNotes = [];
            for (var i = 0; i < track.notes.length; i++) {
                if ((trainNote.t - tpb * beforeMul <= track.notes[i].t) && (track.notes[i].t <= trainNote.t + tpb * afterMul)) {
                    testNotes.push({oi: i, n: track.notes[i].n, t: track.notes[i].t});
                }
            }

            // try to separate testNotes into maxK categories
            var tries = 1;
            do {
                var c = kMed(testNotes, maxK);
            } while ((s = minSilhouette(testNotes, c)) < silhouetteLimit && tries++ < 10);

        console.log('maybe reverse', beforeMul, afterMul, s);
            // stop expanding if we go too far for good results
            if (s < silhouetteLimit) {
                if (iter % 2) {
                    beforeV = 0;
                    beforeMul--;
                } else {
                    afterV = 0;
                    afterMul--;
                }
            }
        console.log('after reverse', beforeMul, afterMul);

            // expand the window
            if (++iter % 2) {
                beforeMul += beforeV;
            } else {
                afterMul += afterV;
            }
        console.log('after expand', beforeMul, afterMul);
        //} while (beforeMul + afterMul < 8 || (s >= silhouetteLimit && beforeMul + afterMul < 24));
        } while ((beforeV || afterV) && beforeMul + afterMul < 24);
        console.log(s);

        var imageBuf = new Buffer(rows * cols * 3);
        imageBuf.fill(0);
        for (var i = 0; i < track.notes.length; i++) {
            var note = track.notes[i];
            for (var j = Math.round(note.t * hScale); j < Math.round((note.t + note.d) * hScale); j++) {
                // colors
                for (var k = 0; k < 3; k++) {
                    imageBuf[((rows - (note.n + 69) * vScale - 2) * cols + j) * bpp + k] = Math.floor(note.v * (255 / 127));

                    if (k === 0 && bestC[0].indexOf(i) !== -1 && i !== tni) {
                        imageBuf[((rows - (note.n + 69) * vScale - 2) * cols + j) * bpp + k] = 0;
                    }
                    if (k === 1 && bestC[1].indexOf(i) !== -1 && i !== tni) {
                        imageBuf[((rows - (note.n + 69) * vScale - 2) * cols + j) * bpp + k] = 0;
                    }
                    if (k === 2 && i === tni) {
                        imageBuf[((rows - (note.n + 69) * vScale - 2) * cols + j) * bpp + k] = 0;
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
