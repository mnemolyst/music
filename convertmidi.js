var fs = require('fs');
var Png = require('png').Png;
var midiFile = require('./public/javascripts/lib/jasmid/midifile');
var childProcess = require('child_process');
var path = require('path');
var Promise = require('bluebird');

var trainTest = 'test';
var genStart = 5;
var genEnd = null;
var genIter = 1;
var makeImages = true;
//var genStart = 200;
//var genEnd = 210;
//var genIter = 1;
//var makeImages = true;

var makeMongo = false;
var fullBright = true;
var bpp = 3; // bytes per pixel
var excludeTrainNote = false;
//var vScale = 1;
var rows = 128;//(highN - lowN + 1 + padB + padT) * vScale; // vScale sub-semitones per MIDI note
var cols = 512;
var idxOffset = genStart;

var fileIn = process.argv[2];
var melodyFile =   path.join(path.dirname(fileIn), path.basename(fileIn, '.mid') + '.melodies');
var dbFile =       path.join(__dirname, '/db/', path.basename(fileIn, '.mid') + '.db');
var imageFile =    path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.images.py');
var noteFile =     path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.notes.py');
var timeFile =     path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.times.py');
var durationFile = path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.durations.py');
var velocityFile = path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.velocities.py');
var dbIdx = 0;
fs.writeFileSync(imageFile,    'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/images\',     envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');
fs.writeFileSync(noteFile,     'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/notes\',      envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');
fs.writeFileSync(timeFile,     'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/times\',      envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');
fs.writeFileSync(durationFile, 'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/durations\',  envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');
fs.writeFileSync(velocityFile, 'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/velocities\', envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\nif c.last():\n\tlast=int(c.key())\nelse:\n\tlast=0\npre=((last-last%1000000000)/1000000000+1)*1000000000\n');

var silhouetteLimit1 = 0.8;
var silhouetteLimit2 = 0.4;

var colors = [
    [0xff, 0, 0],
    [0, 0xff, 0],
    [0xff, 0xff, 0],
    [0, 0, 0xff],
    [0xff, 0, 0xff],
    [0, 0xff, 0xff],
    [127, 127, 127],
];
var melodies;

try {
    var stats = fs.statSync(melodyFile);
    if (stats.isFile()) {
        var read = fs.readFileSync(melodyFile);
        melodies = JSON.parse(read);
    }
} catch (err) {
    console.log('MELODY FILE NOT FOUND:', melodyFile);
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
    var secondsPerTick = tempo / ticksPerBeat;
    var minResScale = secondsPerTick * 16; // horiz scale to make 1/16 sec (1/32 note at 120 bpm) occupy 1 pixel
    tracks.sort(function(a, b) { return a.notes.length > b.notes.length ? -1 : a.notes.length < b.notes.length ? 1 : 0 });
    var track = tracks[0];

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

    function generateTrainingPoints(leftLimitT, rightLimitT) {
        var c = melodies;

        // build training set
        var trainType = Math.floor(Math.random() * 2);
        var resScale = minResScale * (1 + Math.random());
        var timeWidth = cols / resScale;
        if (trainType === 0) {
            var leftImgT = leftLimitT - (Math.random() * 0.6 + 0.2) * (timeWidth - rightLimitT + leftLimitT);
        } else {
            var leftImgT = leftLimitT - (Math.random() * 0.3 + 0.5) * (timeWidth - rightLimitT + leftLimitT);
        }
        var rightImgT = leftImgT + timeWidth;
        var incompleteMelodies = [];
        for (var i = 0; i < c.length; i++) {
            incompleteMelodies.push(i);
        }
        var incompleteMelodies = shuffleArray(incompleteMelodies).slice(0, Math.round(Math.random() * (incompleteMelodies.length - 1) + 1));

        var trainNotes = [];
        var withheldNotes = [];
        var lowN = 127;
        var highN = 0;
        for (var i = 0; i < track.notes.length; i++) {
            var note = track.notes[i];
            var noteMelody = null;
            for (var j = 0; j < c.length; j++) {
                if (c[j].indexOf(i) !== -1) {
                    noteMelody = j;
                }
            }
            if (
                (leftImgT < note.t && note.t + note.d < rightImgT) // inside image
                && (trainType === 0 || note.t < rightLimitT)
            ) {
                if ( // random exclusion
                    incompleteMelodies.indexOf(noteMelody) === -1 // in complete melody
                    || note.t < leftLimitT // outside training time range
                    || rightLimitT < note.t + note.d
                    || (withheldNotes.length > 0 && Math.random() < 0.5) // lucky
                ) {
                    trainNotes.push(i);
                } else {
                    trainNotes.push(i);// XXX
                    withheldNotes.push(i);
                    lowN = note.n < lowN ? note.n : lowN;
                    highN = highN < note.n ? note.n : highN;
                }
            }
        }
        lowN -= Math.round(Math.random() * 3 + 2);
        highN += Math.round(Math.random() * 3 + 2);

        function drawNote(i, buf) {
            var note = track.notes[i];
            var lc = Math.round((note.t - leftImgT) * resScale);
            var uc = Math.round((note.t + note.d - leftImgT) * resScale);
            // TODO beforeLc, beforeUc compare to see if these are necessary
            lc = Math.max(0, Math.min(lc, cols));
            uc = Math.max(0, Math.min(uc, cols));
            if (bpp === 3) {
                for (var j = lc; j < uc; j++) {
                    for (var k = 0; k < bpp; k++) {
                        idx = ((rows - note.n - 1) * cols + j) * bpp + k;

                        if (withheldNotes.indexOf(i) !== -1) {
                            buf[idx] = colors[6][k];
                        } else {
                            for (var l = 0; l < c.length; l++) {
                                if (c[l].indexOf(i) !== -1) {
                                    buf[idx] = colors[l+1][k];
                                }
                            }
                        }
                    }
                }
            } else {
                for (var j = lc; j < uc; j++) {
                    for (var k = 0; k < bpp; k++) {
                        idx = ((rows - note.n - 1) * cols + j) * bpp + k;

                        if (fullBright) {
                            buf[idx] = 255;
                        } else {
                            buf[idx] = Math.floor(note.v * (255 / 127));
                        }
                    }
                }
            }
        }

        var imageBuf = new Buffer(rows * cols * bpp);
        imageBuf.fill(0);
        for (var i = 0; i < trainNotes.length; i++) {
            drawNote(trainNotes[i], imageBuf);
        }
        // training box
        var lc = Math.round((leftLimitT - leftImgT) * resScale);
        var uc = Math.round((rightLimitT - leftImgT) * resScale);
        for (var i = lowN; i <= highN; i++) {
            for (var k = 0; k < bpp; k++) {
                imageBuf[Math.round((rows - i - 1) * cols + lc) * bpp + k] = 255;
                imageBuf[Math.round((rows - i - 1) * cols + uc) * bpp + k] = 255;
            }
        }
        for (var i = lc; i < uc; i++) {
            for (var k = 0; k < bpp; k++) {
                imageBuf[Math.round((rows - lowN - 1) * cols + i) * bpp + k] = 255;
                imageBuf[Math.round((rows - highN - 1) * cols + i) * bpp + k] = 255;
            }
        }

        var trainPoints = [];
        while (i = withheldNotes.shift()) {
            var note = track.notes[i];
            var thisBuf = new Buffer(imageBuf);
            trainPoints.push({
                image: thisBuf,
                note: note.n,
                time: (note.t - leftLimitT) * resScale,
                duration: note.d * resScale,
                velocity: Math.floor(note.v / 8),
                rows: rows,
                cols: cols,
                bpp: bpp,
            });
            drawNote(i, imageBuf);
        }

        return trainPoints;
    }

    var childProto = {
        children: [],
        data: ['', '', '', '', ''],
        spawn: function() {
            var self = this;
            var trainPoint = self.trainPoint;
            return new Promise(function(resolve, reject) {
                var imageProto = '';
                for (var i = 0; i < trainPoint.image.length; i++) {
                    imageProto += '\\x' + Number(trainPoint.image[i]).toString(16); // google protobuf escaped hex
                }

                var prototxt = [];
                prototxt.push('channels: 1\nheight: ' + trainPoint.rows + '\nwidth: ' + trainPoint.cols + '\ndata: "' + imageProto + '"');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.note) + '"');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.time) + '"');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.duration) + '"');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.velocity) + '"');

                for (var i = 0; i < prototxt.length; i++) {
                    self.children.push(new Promise(function(resolve, reject) {
                        var idx = i;
                        var child = childProcess.spawn(
                            '/usr/local/bin/protoc',
                            ['--encode=caffe.Datum', 'caffe.proto'],
                            { cwd: path.join(__dirname, '../caffe/src/caffe/proto') }
                        );
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

    var scheduler = function(trainPoints) {
        this.trainPoints = trainPoints;
        this.go = function() {
            var self = this;
            var trainPoint = self.trainPoints.shift();
            if (trainPoint === undefined) {
                fs.appendFile(imageFile,    'tr.commit()\nenv.close()');
                fs.appendFile(noteFile,     'tr.commit()\nenv.close()');
                fs.appendFile(timeFile,     'tr.commit()\nenv.close()');
                fs.appendFile(durationFile, 'tr.commit()\nenv.close()');
                fs.appendFile(velocityFile, 'tr.commit()\nenv.close()');
                return;
            }
            var task = Object.create(childProto, {
                trainPoint: {
                    writable: true, configurable: true, value: trainPoint,
                },
            });
            task.spawn().then(function(data) {
                new Promise(function(resolve, reject) {
                    var tasks = [
                        new Promise(function(resolve, reject) {
                            fs.appendFile(imageFile,    'tr.put(str(pre + ' + dbIdx + '),\'' + data[0] + '\')\n', resolve);
                            ////////////////////////
                            // generate png image //
                            ////////////////////////
                            if (makeImages) {
                                if (task.trainPoint.bpp === 3) {
                                    var png = new Png(task.trainPoint.image, task.trainPoint.cols, task.trainPoint.rows, 'rgb');
                                } else {
                                    var png = new Png(task.trainPoint.image, task.trainPoint.cols, task.trainPoint.rows, 'gray', 8);
                                }
                                (function() {
                                    var fileName = path.join(__dirname, '/images/', path.basename(fileIn, '.mid') + '.' + dbIdx + '.png');
                                    png.encode(function(image) {
                                        fs.writeFileSync(fileName, image);
                                    });
                                })();
                            }
                            ////////////////////////
                        }),
                        new Promise(function(resolve, reject) {
                            fs.appendFile(noteFile,     'tr.put(str(pre + ' + dbIdx + '),\'' + data[1] + '\')\n', resolve);
                        }),
                        new Promise(function(resolve, reject) {
                            fs.appendFile(timeFile,     'tr.put(str(pre + ' + dbIdx + '),\'' + data[2] + '\')\n', resolve);
                        }),
                        new Promise(function(resolve, reject) {
                            fs.appendFile(durationFile, 'tr.put(str(pre + ' + dbIdx + '),\'' + data[3] + '\')\n', resolve);
                        }),
                        new Promise(function(resolve, reject) {
                            fs.appendFile(velocityFile, 'tr.put(str(pre + ' + dbIdx + '),\'' + data[4] + '\')\n', resolve);
                        }),
                    ];
                    Promise.all(tasks).then(function() {
                        console.log(dbIdx++);
                        resolve();
                    });
                }).then(function() {
                    self.go();
                });
            });
        }
    }

    var trainPoints = generateTrainingPoints(track.notes[200].t, track.notes[220].t);
    var scheduler = new scheduler(trainPoints);
    scheduler.go();

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
