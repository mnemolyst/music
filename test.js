    var Staff = function() {
        this.timeSpacing = 10;
        this.noteSpacing = 10;
        this.drawnLines = [];
        this.nln = []; // note line notes
        this.sf = []; // sharps & flats
    }
    Staff.prototype.noteToLine = function(note) {
        var i = 0, noteClass = ((note % 12) + 12) % 12, nlnl = this.nln.length;
        var octave = (note - noteClass) / 12;
        while (i < nlnl && Math.abs(noteClass - this.nln[(i+1)%nlnl] - this.sf[(i+1)%nlnl]) < Math.abs(noteClass - this.nln[i] - this.sf[i]))
            i++;
        i = i % nlnl;

        return {
            nl: i + octave * nlnl,
            sf: noteClass - this.nln[i] - this.sf[i],
        }
    }
    Staff.prototype.lineToNote = function(line) {
        var lineClass = ((line % this.nln.length) + this.nln.length) % this.nln.length;
        return this.nln[lineClass] + this.sf[lineClass];
    }

    var doubleStaff = new Staff();
    doubleStaff.drawnLines = [5, 3, 1, -1, -3, -7, -9, -11, -13];
    doubleStaff.nln = [0, 2, 3, 5, 7, 8, 10];
    doubleStaff.sf = [0, 0, 0, 0, 0, 0, 0];
for (var i = 0; i < 24; i++)
    console.log(i,doubleStaff.noteToLine(i));
//for (var i = -24; i < 24; i++) {
//    var noteClass = ((i % 12) + 12) % 12;
//    var octave = (i - noteClass) / 12;
//    console.log('i: ' + i + ' nc: ' + noteClass + ' o: ' + octave);
//    }
