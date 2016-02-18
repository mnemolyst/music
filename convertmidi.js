var fs = require('fs');
var MidiFile = require('./public/javascripts/lib/jasmid/midifile');

fs.readFile('./midi/bwv772.mid', function(err, data) {
    var tracks = [];
    var midifile = MidiFile(data);

    for (var i = 0; i < midifile.tracks.length; i++) {
        tracks[i] = {
            name: 'Untitled',
            timeDiv: 4,
        };
        var notes = [];
        var notesOn = {};
        var time = 0;
        for (var j = 0; j < midifile.tracks[i].length; j++) {
            var event = midifile.tracks[i][j];
            var deltaTime = event.deltaTime / midifile.header.ticksPerBeat;
            time += deltaTime;
            switch (event.subtype) {
                case 'noteOn':
                    var key = event.channel + '-' + event.noteNumber;
                    notesOn[key] = time;
                    break;
                case 'noteOff':
                    var key = event.channel + '-' + event.noteNumber;
                    if (notesOn.hasOwnProperty(key)) {
                        notes.push({
                            t: notesOn[key],
                            d: time - notesOn[key],
                            n: event.noteNumber - 69,
                        });
                    }
                    break;
                case 'trackName':
                    tracks[i].name = event.text;
                    break;
                case 'timeSignature':
                    tracks[i].timeDiv = event.numerator;// / Math.pow(2, event.denominator);
                    break;
            }
        }
        tracks[i].notes = notes;
    }

    //for (var i = 0; i < tracks.length; i++) {
    //    var onAt = {};
    //    for (var num in tracks[i].nbp) {
    //        tracks[i].nbp[num].sort(function(a, b) {
    //            return a[0] - b[0]; // sort by time
    //        });

    //        for (var j = 0; j < tracks[i].nbp[num].length; j++) {
    //            var nEvt = tracks[i].nbp[num][j];
    //            if (! onAt.hasOwnProperty(nEvt[2])) {
    //                onAt[nEvt[2]] = null;
    //            }
    //            if (nEvt[1] > 0 && onAt[nEvt[2]] === null) {
    //                onAt[nEvt[2]] = nEvt[0];
    //            } else if (nEvt[1] === 0 && onAt[nEvt[2]] !== null) {
    //                tracks[i].notes.push({
    //                    t: onAt[nEvt[2]],
    //                    d: nEvt[0] - onAt[nEvt[2]],
    //                    n: num - 69,
    //                });
    //                onAt[nEvt[2]] = null;
    //            }
    //            //console.log(onAt);
    //        }
    //    }
    //}

    var i = 1;
    var dbIn = {
        name: tracks[i].name,
        notes: tracks[i].notes,
        staff: {
            noteLines: [5, 3, 1, -1, -3, -7, -9, -11, -13, -15],
            keySig: [0, 0, 0, 0, 0, 0, 0],
            timeDiv: tracks[i].timeDiv,
        },
    };

    //console.log(midifile.header);
    //console.log(midifile.tracks);
    //console.log(tracks[1].nbp);
    //console.log(dbIn);

    fs.writeFileSync('testdb', JSON.stringify(dbIn));
});

//var n = parseInt(process.argv[2], 16).toString(2);
//console.log(n, n.length);
