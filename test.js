var fs = require('fs');

//var readStream = fs.createReadStream('./midi/bwv772.mid')
//
//readStream.on('data', function(chunk) {
//    console.log(chunk.length);
//});

var n = parseInt(process.argv[2], 16).toString(2);
console.log(n, n.length);
