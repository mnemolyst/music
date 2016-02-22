var fs = require('fs');
var Png = require('png').Png;
var MidiFile = require('./public/javascripts/lib/jasmid/midifile');

var fileIn = process.argv[2];
var fileRE = /(.*)\.mid$/;

function cluster(x, med) { // med is array of indices into x
    var c = []; // clusters
    for (var j = 0; j < med.length; j++) {
        c[j] = [];
    }
    for (var i = 0; i < x.length; i++) {
        var minD = null, minJ = 0;
        for (var j = 0; j < med.length; j++) {
            var nd = x[i].n - x[med[j]].n; // note dist
            var td = x[i].t - x[med[j]].t; // time dist
            //var td = (x[i].t + x[i].d * 0.5) - (x[med[j]].t + x[med[j]].d * 0.5); // avg time dist
            var d = nd * nd + td * td;
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
                    var nd = x[c[i][j]].n - x[c[i][k]].n;
                    var td = x[c[i][j]].t - x[c[i][k]].t;
                    sumD += nd * nd + td * td;
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
        med.push(Math.floor(Math.random() * x.length));
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

fs.readFile(fileIn, function(err, data) {
    var timeDiv = 4;
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
                    timeDiv = event.numerator * Math.pow(2, event.denominator - 2);
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

    var rows = 128 * 12; // 12 sub-semitones per MIDI note
    for (var n = 0; n < 10; n++) {
        var tni = Math.floor(Math.random() * track.notes.length);
        var testNote = track.notes[tni];
        var leadIn = Math.random() * tni.t;

        var cols = Math.ceil(track.lastNoteEnd);
        var imageBuf = new Buffer(rows * cols);
        imageBuf.fill(0);
        for (var i = 0; i < track.notes.length; i++) {
            var note = track.notes[i];
            for (var j = note.t; j < (note.t + note.d); j++) {
                //imageBuf[(rows - (note.n + 69) * 3 - 1) * cols + Math.floor(j)] = Math.floor(note.v * (255 / 127) * 0.5);
                imageBuf[(rows - (note.n + 69) * 3 - 2) * cols + Math.floor(j)] = Math.floor(note.v * (255 / 127));
                //imageBuf[(rows - (note.n + 69) * 3 - 3) * cols + Math.floor(j)] = Math.floor(note.v * (255 / 127) * 0.5);
            }
        }
        var png = new Png(imageBuf, cols, rows, 'gray', 8);
        png.encode(function(image) {
            fs.writeFileSync(fileIn.replace(fileRE, '$1.train.' + n), image);
        });
    }
});
