var fs = require('fs');
var Png = require('png').Png;
var midiFile = require('./public/javascripts/lib/jasmid/midifile');
var childProcess = require('child_process');
var path = require('path');
var Promise = require('bluebird');

var trainTest = 'train';
var makeLmdb = true;
var makeImages = false;
var printPoints = false;
var makeMongo = false;
var bpp = 1; // bytes per pixel
var fullBright = true;
var rows = 128;
var cols = 512;

var fileIn = process.argv[2];
var maxPoints = process.argv[3] || 1;
var melodyFile =   path.join(path.dirname(fileIn), path.basename(fileIn, '.mid') + '.melodies');
var dbFile =       path.join(__dirname, '/db/', path.basename(fileIn, '.mid') + '.db');
var dbIdx = 0;
var imageFile =    path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.images.py');
var noteFile =     path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.notes.py');
var timeFile =     path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.times.py');
var durationFile = path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.durations.py');
var velocityFile = path.join(__dirname, '../caffe/music/lmdb/', trainTest, path.basename(fileIn, '.mid') + '.velocities.py');
if (makeLmdb) {
    fs.writeFileSync(imageFile,    'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/images\',     envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\npre=env.stat()[\'entries\']\n');
    fs.writeFileSync(noteFile,     'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/notes\',      envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\npre=env.stat()[\'entries\']\n');
    fs.writeFileSync(timeFile,     'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/times\',      envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\npre=env.stat()[\'entries\']\n');
    fs.writeFileSync(durationFile, 'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/durations\',  envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\npre=env.stat()[\'entries\']\n');
    fs.writeFileSync(velocityFile, 'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/velocities\', envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\npre=env.stat()[\'entries\']\n');
}

var colors = [
    [0xff, 0, 0],
    [0, 0xff, 0],
    [0, 0, 0xff],
    [0xff, 0xff, 0],
    [0xff, 0, 0xff],
    [0, 0xff, 0xff],
    [64, 64, 64],
    [128, 128, 128],
    [0xff, 0x88, 0],
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

    function generateTrainingPoints(leftLimitT, rightLimitT, genMax) {
        var c = melodies;

        // build training set
        var resScale = minResScale * (1 + Math.random());
        var timeWidth = cols / resScale;
        var leftImgT = leftLimitT - (Math.random() * 0.6 + 0.2) * (timeWidth - rightLimitT + leftLimitT);
        var rightImgT = leftImgT + timeWidth;
        var incompleteMelodies = [];
        for (var i = 0; i < c.length; i++) {
            incompleteMelodies.push(i);
        }
        incompleteMelodies = shuffleArray(incompleteMelodies).slice(0, Math.round(Math.random() * (incompleteMelodies.length - 1) + 1));
        var withheldNotes = [];
        var removedNotes = [];
        for (var i = 0; i < incompleteMelodies.length; i++) {
            var melody = c[incompleteMelodies[i]];
            var someWithheld = [];
            var trimmedLeft = Math.random() < 1/3;
            var trimmedRight = (! trimmedLeft) && Math.random() < 1/2;
            for (var j = 0; j < melody.length; j++) {
                var note = track.notes[melody[j]];
                if (
                    (trimmedLeft && note.t < leftLimitT)
                    || (trimmedRight && rightLimitT < note.t + note.d)
                ) {
                    removedNotes.push(melody[j]);
                } else if (leftLimitT <= note.t && note.t + note.d <= rightLimitT && withheldNotes.indexOf(melody[j]) === -1) {
                    someWithheld.push(melody[j]);
                }
            }
            //if (Math.random() < 0.5) {
            //    someWithheld = shuffleArray(someWithheld);
            //} else {
            //    someWithheld = someWithheld.slice(Math.round((Math.random() * someWithheld.length / 3)));
            //}
            var sliceStart = Math.round(Math.random() * 0.25 * someWithheld.length);
            var sliceEnd = Math.round((Math.random() * 0.25 + 0.75) * someWithheld.length);
            Array.prototype.push.apply(withheldNotes, someWithheld.slice(sliceStart, sliceEnd));
        }
        // earlier notes first, then higher pitched notes first
        withheldNotes.sort(function(a, b) {
            var noteA = track.notes[a];
            var noteB = track.notes[b];
            if (noteA.t < noteB.t) {
                return -1;
            } else if (noteB.t < noteA.t) {
                return 1;
            } else {
                if (noteA.n < noteB.n) {
                    return 1;
                } else if (noteB.n < noteA.n) {
                    return -1;
                } else {
                    return 0;
                }
            }
        });

        var trainNotes = [];
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
                leftImgT < note.t && note.t + note.d < rightImgT // inside image
                && withheldNotes.indexOf(i) === -1
                && removedNotes.indexOf(i) === -1
            ) {
                trainNotes.push(i);
            } else if (withheldNotes.indexOf(i) !== -1) {
                if (bpp === 3) { // XXX for debugging
                    trainNotes.push(i);
                }
                lowN = note.n < lowN ? note.n : lowN;
                highN = highN < note.n ? note.n : highN;
            }
        }
        // TODO fidget with these numbers
        lowN -= Math.round(Math.random() * 6 + 2);
        highN += Math.round(Math.random() * 6 + 2);

        function drawNote(i, buf) {
            var note = track.notes[i];
            var lc = Math.round((note.t - leftImgT) * resScale);
            var uc = Math.round((note.t + note.d - leftImgT) * resScale);
            lc = Math.max(0, Math.min(lc, cols));
            uc = Math.max(0, Math.min(uc, cols));
            if (bpp === 3) {
                if (removedNotes.indexOf(i) !== -1) {
                    var color = [64, 64, 64];
                } else if (withheldNotes.indexOf(i) !== -1) {
                    var color = [128, 128, 128];
                } else {
                    for (var l = 0; l < c.length; l++) {
                        if (c[l].indexOf(i) !== -1) {
                            var color = colors[l];
                        }
                    }
                }
                for (var j = lc; j < uc; j++) {
                    for (var k = 0; k < bpp; k++) {
                        idx = ((rows - 1 - note.n) * cols + j) * bpp + k;
                        buf[idx] = color[k];
                    }
                }
            } else {
                for (var j = lc; j < uc; j++) {
                    for (var k = 0; k < bpp; k++) {
                        idx = ((rows - 1 - note.n) * cols + j) * bpp + k;

                        if (fullBright) {
                            buf[idx] = 255;
                        } else {
                            buf[idx] = Math.floor(note.v + 128);
                        }
                    }
                }
            }
        }

        // new image
        var imageBuf = new Buffer(rows * cols * bpp);
        imageBuf.fill(0);

        // notes
        for (var i = 0; i < trainNotes.length; i++) {
            drawNote(trainNotes[i], imageBuf);
        }

        // grid
        for (var i = 12; i < 128; i+=12) {
            for (var j = 0; j < cols; j+=2) {
                for (var k = 0; k < bpp; k++) {
                    idx = ((rows - 1 - i) * cols + j) * bpp + k;
                    imageBuf[idx] = Math.min(imageBuf[idx] + 32, 255);
                }
            }
        }

        // limit box
        var lc = Math.round((leftLimitT - leftImgT) * resScale);
        var uc = Math.round((rightLimitT - leftImgT) * resScale);
        for (var i = lowN; i <= highN; i++) {
            for (var k = 0; k < bpp; k++) {
                var idx1 = Math.round((rows - 1 - i) * cols + lc) * bpp + k;
                var idx2 = Math.round((rows - 1 - i) * cols + uc) * bpp + k;
                imageBuf[idx1] = Math.min(imageBuf[idx1] + 64, 255);
                imageBuf[idx2] = Math.min(imageBuf[idx2] + 64, 255);
            }
        }
        for (var i = lc + 1; i < uc; i++) {
            var zigZag = (i-lc)%2 ? 0 : (i-lc)%4 ? -1 : 1;
            for (var k = 0; k < bpp; k++) {
                var idx1 = Math.round((rows - 1 - lowN - zigZag) * cols + i) * bpp + k;
                var idx2 = Math.round((rows - 1 - highN - zigZag) * cols + i) * bpp + k;
                imageBuf[idx1] = Math.min(imageBuf[idx1] + 64, 255);
                imageBuf[idx2] = Math.min(imageBuf[idx2] + 64, 255);
            }
        }

        var trainPoints = [];
        while ((i = withheldNotes.shift()) && trainPoints.length < genMax) {
            var note = track.notes[i];
            (function() {
                var thisBuf = new Buffer(imageBuf);
                trainPoints.push({
                    image: thisBuf,
                    note: note.n,
                    //time: (note.t - leftLimitT) * resScale,
                    //duration: note.d * resScale,
                    time: Math.round((note.t - leftImgT) * resScale) - Math.round((leftLimitT - leftImgT) * resScale),
                    duration: Math.round((note.t + note.d - leftImgT) * resScale) - Math.round((note.t - leftImgT) * resScale),
                    velocity: Math.floor(note.v / 8),
                });
            })();
            drawNote(i, imageBuf);
        }

        return trainPoints;
    }

    var ProtobufChild = function(trainPoint) {
        this.trainPoint = trainPoint;
        this.children = [];
        this.data = ['', '', '', '', ''];
        this.spawn = function() {
            var self = this;
            var trainPoint = self.trainPoint;
            return new Promise(function(resolve, reject) {
                var imageProto = '';
                for (var i = 0; i < trainPoint.image.length; i++) {
                    imageProto += '\\x' + Number(trainPoint.image[i]).toString(16); // google protobuf escaped hex
                }

                var prototxt = [];
                prototxt.push('channels: 1\nheight: ' + rows + '\nwidth: ' + cols + '\ndata: "' + imageProto + '"');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\nfloat_data: ' + trainPoint.note + '');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\nfloat_data: ' + trainPoint.time + '');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\nfloat_data: ' + trainPoint.duration + '');
                prototxt.push('channels: 1\nheight: 1\nwidth: 1\nfloat_data: ' + trainPoint.velocity + '');

                for (var i = 0; i < prototxt.length; i++) {
                    self.children.push(new Promise(function(resolve, reject) {
                        var idx = i;
                        var child = childProcess.spawn(
                            'protoc',
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
        };
    }

    var Scheduler = function(trainPoints) {
        this.trainPoints = trainPoints;
        this.next = function() {
            var trainPoint = this.trainPoints.shift();
            if (trainPoint === undefined) {
                return false;
            } else {
                this.child = new ProtobufChild(trainPoint);
                return true;
            }
        }
        this.go = function(callback) {
            this.child.spawn().then(function(data) {
                new Promise(function(resolve, reject) {
                    var tasks = [
                        new Promise(function(resolve, reject) {
                            fs.appendFile(imageFile,    'tr.put(str(pre + ' + dbIdx + '),\'' + data[0] + '\')\n', resolve);
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
                        dbIdx++;
                        if (dbIdx % 100 === 0) {
                            //console.log(dbIdx);
                        }
                        resolve();
                    });
                }).then(function() {
                    callback();
                });
            });
        }
    }

    // generate training points
    if (makeImages || printPoints || makeLmdb) {
        var trainPoints = [];
        while (trainPoints.length < maxPoints) {
            var widthT = ticksPerBeat * Math.floor(Math.random() * 12 + 4);
            var leftLimitT = Math.floor(Math.random() * (track.lastNoteEnd - widthT));
            var thisPoints = generateTrainingPoints(leftLimitT, leftLimitT + widthT, maxPoints - trainPoints.length);
            Array.prototype.push.apply(trainPoints, thisPoints);
        }
    }

    if (makeImages) {
        for (var i = 0; i < trainPoints.length; i++) {
            if (bpp === 3) {
                var png = new Png(trainPoints[i].image, cols, rows, 'rgb');
            } else {
                var png = new Png(trainPoints[i].image, cols, rows, 'gray', 8);
            }
            (function() {
                var fileName = path.join(__dirname, '/images/', path.basename(fileIn, '.mid') + '.' + i + '.png');
                png.encode(function(image) {
                    fs.writeFileSync(fileName, image);
                });
            })();
        }
    }
    if (printPoints) {
        for (var i = 0; i < trainPoints.length; i++) {
            console.log(i);
            console.log('note', trainPoints[i].note);
            console.log('time', trainPoints[i].time);
            console.log('duration', trainPoints[i].duration);
            //console.log('velocity', trainPoints[i].velocity);
        }
    }
    if (makeLmdb) {
        var scheduler = new Scheduler(trainPoints);
        function scheduleNext() {
            if (scheduler.next()) {
                scheduler.go(scheduleNext);
            } else {
                fs.appendFile(imageFile,    'tr.commit()\nenv.close()');
                fs.appendFile(noteFile,     'tr.commit()\nenv.close()');
                fs.appendFile(timeFile,     'tr.commit()\nenv.close()');
                fs.appendFile(durationFile, 'tr.commit()\nenv.close()');
                fs.appendFile(velocityFile, 'tr.commit()\nenv.close()');
            }
        }
        scheduleNext();
    }
    if (makeMongo) {
        var dbIn = {
            name: path.basename(fileIn, '.mid'),
            notes: track.notes.map(function(el) { el.n -= 69; el.t *= minResScale * 0.25; el.d *= minResScale * 0.25; return el }),
            ticksPerBeat: midifile.header.ticksPerBeat,
            tempo: tempo,
        };
        fs.writeFileSync(dbFile, JSON.stringify(dbIn));
    }
});
