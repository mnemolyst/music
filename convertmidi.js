var fs = require('fs');
var MidiFile = require('./public/javascripts/lib/jasmid/midifile');

fs.readFile('./midi/bwv772.mid', function(err, data) {
    var name = 'Untitled';
    var timeDiv = 4;
    var notesByPitch = {};
    var notes = [];
    var midifile = MidiFile(data);
    //console.log(midifile.header);
    //console.log(midifile.tracks);
    var tpb = midifile.header.ticksPerBeat;

    for (var i = 0; i < midifile.tracks.length; i++) {
        for (var j = 0; j < midifile.tracks[i].length; j++) {
            var event = midifile.tracks[i][j];
            switch (event.subtype) {
                case 'noteOn':
                    var num = event.noteNumber;
                    if (! notesByPitch.hasOwnProperty(num)) {
                        notesByPitch[num] = [];
                    }
                    notesByPitch[num].push([event.deltaTime, event.velocity]);
                    break;
                case 'noteOff':
                    var num = event.noteNumber;
                    if (! notesByPitch.hasOwnProperty(num)) {
                        notesByPitch[num] = [];
                    }
                    notesByPitch[num].push([event.deltaTime, 0]);
                    break;
                case 'trackName':
                    name = event.text;
                    break;
                case 'timeSignature':
                    var timeDiv = event.numerator;// / Math.pow(2, event.denominator);
                    break;
            }
        }
    }
    for (var num in notesByPitch) {
        notesByPitch[num].sort(function(a, b) {
            return a[0] - b[0]; // sort by time
        });

        var onAt = null;
        for (var i = 0; i < notesByPitch[num].length; i++) {
            if (notesByPitch[num][i][1] > 0 && onAt === null) {
                onAt = notesByPitch[num][i][0];
            } else if (notesByPitch[num][i][1] === 0 && onAt !== null) {
                notes.push({
                    t: onAt,
                    d: notesByPitch[num][i][0] - onAt,
                    n: num - 69,
                });
                onAt = null;
            }
        }
    }

    console.log({
        name: name,
        notes: notes,
        staff: {
            noteLines: [5, 3, 1, -1, -3, -7, -9, -11, -13, -15],
            keySig: [0, 0, 0, 0, 0, 0, 0],
            timeDiv: timeDiv,
        },
    });
});

//var n = parseInt(process.argv[2], 16).toString(2);
//console.log(n, n.length);
