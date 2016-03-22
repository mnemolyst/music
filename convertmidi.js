var fs = require('fs');
var Png = require('png').Png;
var midiFile = require('./public/javascripts/lib/jasmid/midifile');
var childProcess = require('child_process');
var path = require('path');
var Promise = require('bluebird');

var trainTest = 'test';
var genStart = 5;
var genEnd = null;
var genIter = 2;
var makeImages = false;
//var genStart = 200;
//var genEnd = 210;
//var genIter = 1;
//var makeImages = true;

var makeMongo = false;
var bpp = 1; // bytes per pixel
var excludeTrainNote = true;
//var vScale = 1;
var rows = 128;//(highN - lowN + 1 + padB + padT) * vScale; // vScale sub-semitones per MIDI note
var cols = 512;
var idxOffset = genStart;

var fileIn = process.argv[2];
var melodyFile =   path.join(__dirname, '/midi/', path.basename(fileIn, '.mid') + '.melodies');
var dbFile =       path.join(__dirname, '/db/', path.basename(fileIn, '.mid') + '.db');
var imageFile =    path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.images.py');
var noteFile =     path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.notes.py');
var timeFile =     path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.times.py');
var durationFile = path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.durations.py');
var velocityFile = path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.velocities.py');
fs.writeFileSync(imageFile,    'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/images\',     envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');
fs.writeFileSync(noteFile,     'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/notes\',      envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');
fs.writeFileSync(timeFile,     'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/times\',      envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');
fs.writeFileSync(durationFile, 'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/durations\',  envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');
fs.writeFileSync(velocityFile, 'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/velocities\', envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');

var silhouetteLimit1 = 0.8;
var silhouetteLimit2 = 0.4;

var colors = [
    [0xff, 0xff, 0],
    [0xff, 0, 0],
    [0, 0, 0xff],
    [0, 0xff, 0],
    [0xff, 0, 0xff],
];
var melodies;

try {
    var stats = fs.statSync(melodyFile);
    if (stats.isFile()) {
        var read = fs.readFileSync(melodyFile);
        melodies = JSON.parse(read);
    }
} catch (err) {
}

fs.readFile(fileIn, function(err, data) {
    console.log(fileIn);
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
    var minResScale = secondsPerTick * 16; // horiz scale to make 1/16 sec (1/64 note at 120 bpm) occupy 1 pixel
    var timeWidth = cols / minResScale;
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

    function generateTrainingPoint(tni) {
        var trainNote = track.notes[tni];

        if (melodies) {
            var c = melodies;
            if (c.length === 1) {
                var trainType = Math.floor(Math.random() * 2);
            } else {
                var trainType = Math.floor(Math.random() * 5); // 0: all notes before; 1: all before, some after; 2: single melody before; 3: single melody before, some after; 4: all notes before and after except some same-melody
            }
        } else {
            // TODO find best K / best s
            var testNotes = [], maxK = 2;
            for (var i = Math.max(0, tni - 3 * maxK); i < Math.min(track.notes.length, tni + 3 * maxK); i++) {
                testNotes.push(i);
            }
            //do {
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
        }

        // build training set
        // trainType 0: all notes before; 1: all before, some after; 2: single melody before; 3: single melody before, some after
        // 4: all notes before and after except some same-melody
        var trainNotes = [];
        if (trainType === 0 || trainType === 2) {
            var trainNoteColT = (Math.random() * 0.4 + 0.5) * timeWidth;
        } else {
            var trainNoteColT = (Math.random() * 0.8 + 0.1) * timeWidth;
        }
        var trainStart = trainNote.t - (Math.random() * 0.9 + 0.1) * trainNoteColT;
        var trainGapEnd = trainNote.t + (Math.random() * 0.8 + 0.2) * (timeWidth - trainNoteColT) * 0.5;
        var trainStop = trainGapEnd + (Math.random() * 0.8 + 0.2) * (timeWidth - trainNoteColT) * 0.5;
        var trainMelody = null;
        for (var i = 0; i < c.length; i++) {
            if (c[i].indexOf(tni) !== -1) {
                trainMelody = i;
                break;
            }
        }

        var firstT = trainNote.t;
        var lastT = trainNote.t + trainNote.d;
        //var lowN = 0;//trainNote.n;
        //var highN = 127;//trainNote.n;
        var lastInMelodyBefore = 0;
        for (var i = 0; i < track.notes.length; i++) {
            var note = track.notes[i];
            if (
                ! (note.t < trainStart || trainStop < note.t) // outside training range
                && ! ((trainType === 0 || trainType === 2) && trainNote.t < note.t) // training type excludes notes after training note
                && ! ((trainType === 2 || trainType === 3) && c[trainMelody].indexOf(i) === -1) // in wrong melody
                && ! ((trainType === 1 || trainType === 3 || (trainType === 4 && c[trainMelody].indexOf(i) !== -1)) && trainNote.t < note.t && note.t < trainGapEnd) // inside gap range
                && ! (excludeTrainNote && tni === i) // and of course
            ) {
                trainNotes.push(i);

                firstT = note.t < firstT ? note.t : firstT;
                lastT = lastT < note.t + note.d ? note.t + note.d : lastT;
                //lowN = note.n < lowN ? note.n : lowN;
                //highN = highN < note.n ? note.n : highN;
                if (lastInMelodyBefore < i && i < tni && c[trainMelody].indexOf(i) !== -1) {
                    lastInMelodyBefore = i;
                }
            }
        }
        var indicatorSixtyfourthsOffset = Math.floor(Math.random() * 64) - 32; // introduce randomness in indicator line for training generalization
        var minISFO = Math.ceil((track.notes[lastInMelodyBefore].t - trainNote.t) * 16 / ticksPerBeat);
        var maxISFO = Math.floor((trainGapEnd - trainNote.t) * 0.5 * 16 / ticksPerBeat);
        indicatorSixtyfourthsOffset = Math.max(minISFO, Math.min(indicatorSixtyfourthsOffset, maxISFO));
        var indicatorT = trainNote.t + indicatorSixtyfourthsOffset * ticksPerBeat / 16;
        var padL = trainStart - (trainNote.t - trainNoteColT); // trainNote.t - trainNoteColT is the amount of time before the left edge of the image

        var lowestAbove = 128;
        var highestBelow = 0;
        for (var i = 0; i < trainNotes.length; i++) {
            if (
                track.notes[trainNotes[i]].t - ticksPerBeat < trainNote.t
                && trainNote.t < track.notes[trainNotes[i]].t + track.notes[trainNotes[i]].d + ticksPerBeat
                && c[trainMelody].indexOf(trainNotes[i]) === -1
            ) {
                if (track.notes[trainNotes[i]].n < lowestAbove && trainNote.n < track.notes[trainNotes[i]].n) {
                    lowestAbove = track.notes[trainNotes[i]].n;
                }
                if (highestBelow < track.notes[trainNotes[i]].n && track.notes[trainNotes[i]].n < trainNote.n) {
                    highestBelow = track.notes[trainNotes[i]].n;
                }
            }
        }
        var indicatorTop = 128 - Math.round((lowestAbove + trainNote.n) * 0.5);
        var indicatorBottom = 128 - Math.round((highestBelow + trainNote.n) * 0.5);

        ////////////////
        // draw image //
        ////////////////

        var imageBuf = new Buffer(rows * cols * bpp);
        imageBuf.fill(0);
        for (var i = 0; i < trainNotes.length; i++) {
            var note = track.notes[trainNotes[i]];
            var lc = Math.round((note.t - firstT + padL) * minResScale);
            var uc = Math.round((note.t + note.d - firstT + padL) * minResScale);
            lc = Math.max(0, Math.min(lc, cols));
            uc = Math.max(0, Math.min(uc, cols));
            for (var j = lc; j < uc; j++) {
                colors: for (var k = 0; k < bpp; k++) {
                    //idx = ((rows - (note.n - lowN + padB) * vScale - 2) * cols + j) * bpp + k;
                    idx = ((rows - note.n - 1) * cols + j) * bpp + k;

                    if (bpp === 3) {
                        if (trainNotes[i] === tni) {
                            imageBuf[idx] = colors[0][k];
                        } else if (trainNotes[i] === lastInMelodyBefore) {
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
        for (var i = indicatorTop; i < indicatorBottom; i++) {
            for (var k = 0; k < bpp; k++) {
                var idx = Math.round(i * cols + (indicatorT - firstT + padL) * minResScale) * bpp + k;
                imageBuf[idx] = 255;
            }
        }

        return {
            image: imageBuf,
            note: trainNote.n,
            time: indicatorSixtyfourthsOffset + 32,
            duration: Math.min(Math.round(trainNote.d / ticksPerBeat * 16), 64),
            velocity: Math.floor(trainNote.v / 8),
            rows: rows,
            cols: cols,
            bpp: bpp,
        };
    }

    var childProto = {
        exe: '/usr/local/bin/protoc',
        args: ['--encode=caffe.Datum', 'caffe.proto'],
        opts: { cwd: path.join(__dirname, '../caffe/src/caffe/proto') },
        spawn: function() {
            var self = this;
            return new Promise(function(resolve, reject) {
                var trainPoint = generateTrainingPoint(self.tni);
                self.trainPoint = trainPoint;

                var imageProto = '';
                for (var i = 0; i < trainPoint.image.length; i++) {
                    imageProto += '\\x' + Number(trainPoint.image[i]).toString(16); // google protobuf escaped hex
                }

                //var noteProto = '';
                //for (var i = 0; i < 128; i++) {
                //    noteProto += trainPoint.note === i ? '\\x01' : '\\x00';
                //}

                var prototxt = [];
                prototxt.push('channels: 1\nheight: ' + trainPoint.rows + '\nwidth: ' + trainPoint.cols + '\ndata: "' + imageProto + '"');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.note) + '"');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.time) + '"');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.duration) + '"');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.velocity) + '"');

                for (var i = 0; i < prototxt.length; i++) {
                    self.children.push(new Promise(function(resolve, reject) {
                        var idx = i;
                        var child = childProcess.spawn(self.exe, self.args, self.opts);
                        child.stdout.on('data', function(data) {
                            var dataBuf = new Buffer(data);
                            for (var j = 0; j < dataBuf.length; j++) {
                                if (dataBuf[j] < 16) {
                                    self.data[idx] += '\\x0' + Number(dataBuf[j]).toString(16); // python escaped hex
                                } else {
                                    self.data[idx] += '\\x' + Number(dataBuf[j]).toString(16);
                                }
                            }
                        });
                        child.stdout.on('end', function() {
                            resolve();
                        });
                        child.stdin.end(prototxt[idx]);
                    }));
                }

                Promise.all(self.children).then(function() {
                    resolve(self.data);
                });
            });
        },
    }

    var scheduler = {
        task: null,
        make: function(tni, max, iter) {
            this.task = Object.create(childProto, {
                tni: {
                    writable: true, configurable: true, value: tni,
                },
                children: {
                    writable: true, configurable: true, value: [],
                },
                data: {
                    writable: true, configurable: true, value: ['', '', '', '', ''],
                },
            });
            this.max = max;
            this.iter = iter;
            return this;
        },
        go: function(i) {
            var self = this;
            var i = i || 0;
            if (self.task.tni < self.max) {
                self.task.spawn().then(function(data) {
                    new Promise(function(resolve, reject) {
                        var idx = String((self.task.tni - idxOffset) * self.iter + i);
                        var tasks = [
                            new Promise(function(resolve, reject) {
                                fs.appendFile(imageFile,    'tr.put(str(pre + ' + idx + '),\'' + data[0] + '\')\n', resolve);
                                ////////////////////////
                                // generate png image //
                                ////////////////////////
                                if (makeImages) {
                                    if (self.task.trainPoint.bpp === 3) {
                                        var png = new Png(self.task.trainPoint.image, self.task.trainPoint.cols, self.task.trainPoint.rows, 'rgb');
                                    } else {
                                        var png = new Png(self.task.trainPoint.image, self.task.trainPoint.cols, self.task.trainPoint.rows, 'gray', 8);
                                    }
                                    (function() {
                                        var fileName = path.join(__dirname, '/images/', path.basename(fileIn, '.mid') + '.' + idx + '.png');
                                        png.encode(function(image) {
                                            fs.writeFileSync(fileName, image);
                                        });
                                    })();
                                }
                                ////////////////////////
                            }),
                            new Promise(function(resolve, reject) {
                                fs.appendFile(noteFile,     'tr.put(str(pre + ' + idx + '),\'' + data[1] + '\')\n', resolve);
                            }),
                            new Promise(function(resolve, reject) {
                                fs.appendFile(timeFile,     'tr.put(str(pre + ' + idx + '),\'' + data[2] + '\')\n', resolve);
                            }),
                            new Promise(function(resolve, reject) {
                                fs.appendFile(durationFile, 'tr.put(str(pre + ' + idx + '),\'' + data[3] + '\')\n', resolve);
                            }),
                            new Promise(function(resolve, reject) {
                                fs.appendFile(velocityFile, 'tr.put(str(pre + ' + idx + '),\'' + data[4] + '\')\n', resolve);
                            }),
                        ];
                        Promise.all(tasks).then(resolve);
                    }).then(function() {
                        if (i + 1 < self.iter) {
                            self.make(self.task.tni, self.max, self.iter).go(i + 1);
                        } else {
                            console.log(self.task.tni);
                            self.make(self.task.tni + 1, self.max, self.iter).go(0);
                        }
                    });
                });
            } else {
                fs.appendFile(imageFile,    'tr.commit()\nenv.close()');
                fs.appendFile(noteFile,     'tr.commit()\nenv.close()');
                fs.appendFile(timeFile,     'tr.commit()\nenv.close()');
                fs.appendFile(durationFile, 'tr.commit()\nenv.close()');
                fs.appendFile(velocityFile, 'tr.commit()\nenv.close()');
            }
        },
    }

    scheduler.make(genStart, genEnd === null ? track.notes.length - 1 : genEnd, genIter).go();

    if (makeMongo) {
        var dbIn = {
            name: path.basename(fileIn, '.mid'),
            notes: track.notes.map(function(el) { el.n -= 69; el.t *= minResScale * 0.25; el.d *= minResScale * 0.25; return el }),
            staff: {
                noteLines: [5, 3, 1, -1, -3, -7, -9, -11, -13, -15],
                keySig: [0, 0, 0, 0, 0, 0, 0],
                timeDiv: timeDiv,
            },
            ticksPerBeat: midifile.header.ticksPerBeat,
            tempo: tempo,
        };
        fs.writeFileSync(dbFile, JSON.stringify(dbIn));
    }
});
