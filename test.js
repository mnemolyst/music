var fs = require('fs');
var Png = require('png').Png;
fs.readFile('protobuf/test.out', function(err, data) {
    var dataBuf = new Buffer(data);
    var imageBuf = new Buffer(1620 * 128);
    var n;
    var j = 0;
    for (var i = 0; i < dataBuf.length; i+=4) {
        n = parseInt(dataBuf.slice(i+1, i+4), 8);
        imageBuf[j++] = n;
    }
    var png = new Png(imageBuf, 1620, 128, 'gray', 8);
    (function() {
        var fileName = 'protobuf/imagetest.png';
        png.encode(function(image) {
            fs.writeFileSync(fileName, image);
        });
    })();
});
