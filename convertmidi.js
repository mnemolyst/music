var fs = require('fs');
var MidiFile = require('./public/javascripts/lib/jasmid/midifile');

fs.readFile('./midi/bwv772.mid', function(err, data) {
    var midifile = MidiFile(data);
    console.log(midifile.header);
});

//var n = parseInt(process.argv[2], 16).toString(2);
//console.log(n, n.length);
