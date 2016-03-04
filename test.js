var Promise = require('bluebird');
var path = require('path');
var fs = require('fs');
var childProcess = require('child_process');
//var fs = require('fs');
//var Png = require('png').Png;
//fs.readFile('protobuf/imagetest.out', function(err, data) {
//    var dataBuf = new Buffer(data);
//    var imageBuf = new Buffer(673 * 156);
//    var n;
//    var j = 0;
//    for (var i = 0; i < dataBuf.length; i+=4) {
//        n = parseInt(dataBuf.slice(i+1, i+4), 8);
//        imageBuf[j++] = n;
//    }
//    var png = new Png(imageBuf, 673, 156, 'gray', 8);
//    (function() {
//        var fileName = 'protobuf/imagetest.png';
//        png.encode(function(image) {
//            fs.writeFileSync(fileName, image);
//        });
//    })();
//});

var objProto = {
    child: null,
    data: '',
    spawn: function() {
        var self = this;
        return new Promise(function(resolve, reject) {
            self.child = childProcess.spawn('ls', ['/home/joshua']);
            self.child.stderr.on('data', console.log);
            self.child.stdout.on('data', function(data) {
                self.data += data;
            });
            self.child.stdout.on('end', function() {
                resolve(self.idx + '\n' + self.data);
            });
        });
    }
}

scheduler = {
    tasks: [],
    makeNew: function(idx) {
        var task = Object.create(objProto, {
            idx: {
                writable: true, configurable: true, value: idx
            }
        });
        this.tasks.push(task);
        return this;
    },
    go: function() {
        var self = this;
        var task = self.tasks[self.tasks.length - 1];
        var taskP = task.spawn();
        taskP.then(function(data) {
            var fsP = new Promise(function(resolve, reject) {
                fs.appendFile('/home/joshua/temp/test.out', data, resolve);
            });
            fsP.then(function() {
                if (task.idx < 10) {
                    self.makeNew(task.idx + 1).go();
                }
            });
        });
    },
}

scheduler.makeNew(1).go();
