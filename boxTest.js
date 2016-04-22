var fs = require('fs');
var Png = require('png').Png;
var childProcess = require('child_process');
var path = require('path');
var Promise = require('bluebird');

var trainTest = 'test';
var makeLmdb = true;
var makeImages = false;
var printPoints = false;
var bpp = 1; // bytes per pixel
var fullBright = true;
var rows = 256;
var cols = 256;

var maxPoints = 1000;
var dbIdx = 0;
var imageFile =    path.join(__dirname, '../caffe/music/lmdb/', trainTest, 'boxTest.images.py');
var noteFile =     path.join(__dirname, '../caffe/music/lmdb/', trainTest, 'boxTest.notes.py');
var timeFile =     path.join(__dirname, '../caffe/music/lmdb/', trainTest, 'boxTest.times.py');
if (makeLmdb) {
    fs.writeFileSync(imageFile,    'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/images\',     envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\npre=env.stat()[\'entries\']\n');
    fs.writeFileSync(noteFile,     'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/notes\',      envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\npre=env.stat()[\'entries\']\n');
    fs.writeFileSync(timeFile,     'import lmdb\nimport sys\nenvSize=1024*1024*1024*1024\nenv=lmdb.open(sys.path[0] + \'/times\',      envSize)\ntr=env.begin(None,None,True)\nc=tr.cursor()\npre=env.stat()[\'entries\']\n');
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

function generateTrainingPoint() {
    // new image
    var imageBuf = new Buffer(rows * cols * bpp);
    imageBuf.fill(0);

    // limit box
    var width = Math.round((Math.random() * 0.4 + 0.1) * cols);
    var lc = Math.round(Math.random() * (cols - width));
    var uc = lc + width;
    var height = Math.round((Math.random() * 0.4 + 0.1) * rows);
    var lowN = Math.round(Math.random() * (rows - height));
    var highN = lowN + height;
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

    var px = Math.round(Math.random() * (uc - lc - 2) + lc + 1);
    var py = Math.round(Math.random() * (highN - lowN - 2) + lowN + 1);
    for (var k = 0; k < bpp; k++) {
        imageBuf[((rows - 1 - py) * cols + px) * bpp + k] = 255;
    }

    return {
        image: imageBuf,
        note: py - lowN,
        time: px - lc,
    };
}

var ProtobufChild = function(trainPoint) {
    this.trainPoint = trainPoint;
    this.children = [];
    this.data = ['', '', ''];
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
        var thisPoints = generateTrainingPoint(maxPoints - trainPoints.length);
        trainPoints.push(thisPoints);
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
            var fileName = path.join(__dirname, '/images/', 'boxTest.' + i + '.png');
            png.encode(function(image) {
                fs.writeFileSync(fileName, image);
            });
        })();
    }
}
if (printPoints) {
    for (var i = 0; i < trainPoints.length; i++) {
        console.log(i);
        console.log('x', trainPoints[i].time);
        console.log('y', trainPoints[i].note);
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
        }
    }
    scheduleNext();
}
