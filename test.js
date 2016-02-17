var fs = require('fs');
var MidiFile = require('./public/javascripts/lib/jasmid/midifile');

fs.readFile('./midi/bwv772.mid.test', 'utf8', function(err, data) {
						var ff = [];
						var scc= String.fromCharCode;
						for (var z = 0; z < data.length; z++) {
							ff[z] = scc(data.charCodeAt(z) & 255);
						}
                        f = ff.join('');
    //console.log(f);
    var midifile = MidiFile(f);
    console.log(midifile.header);
});
