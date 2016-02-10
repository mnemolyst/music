define(['jquery', 'paper'], function($, paperJs) {
    paperJs.paper.install(this);

    var upperLeft = new Point(100, 100);
    var leftTime = 0;

    var keySignatures = {
        'cM':  [0, 0, 0, 0, 0, 0, 0],
        'gM':  [0, 0, 0, 0, 0, 1, 0],
        'dM':  [0, 0, 1, 0, 0, 1, 0],
        'aM':  [0, 0, 1, 0, 0, 1, 1],
        'eM':  [0, 0, 1, 1, 0, 1, 1],
        'bM':  [1, 0, 1, 1, 0, 1, 1],
        'f+M': [1, 0, 1, 1, 1, 1, 1],
        'c+M': [1, 1, 1, 1, 1, 1, 1],
        'fM':  [0, -1, 0, 0, 0, 0, 0],
        'b-M': [0, -1, 0, 0, -1, 0, 0],
        'e-M': [-1, -1, 0, 0, -1, 0, 0],
        'a-M': [-1, -1, 0, -1, -1, 0, 0],
        'd-M': [-1, -1, 0, -1, -1, 0, -1],
        'g-M': [-1, -1, -1, -1, -1, 0, -1],
        'c-M': [-1, -1, -1, -1, -1, -1, -1],
    };
    keySignatures['am'] = keySignatures['cM'];
    keySignatures['em'] = keySignatures['gM'];
    keySignatures['bm'] = keySignatures['dM'];
    keySignatures['f+m'] = keySignatures['aM'];
    keySignatures['c+m'] = keySignatures['eM'];
    keySignatures['g+m'] = keySignatures['bM'];
    keySignatures['d+m'] = keySignatures['f+M'];
    keySignatures['a+m'] = keySignatures['c+M'];
    keySignatures['dm'] = keySignatures['fM'];
    keySignatures['gm'] = keySignatures['b-M'];
    keySignatures['cm'] = keySignatures['e-M'];
    keySignatures['fm'] = keySignatures['a-M'];
    keySignatures['b-m'] = keySignatures['d-M'];
    keySignatures['e-m'] = keySignatures['g-M'];
    keySignatures['a-m'] = keySignatures['c-M'];

    sfSigns = {
        '-1': '\u266d', // flat
        '0': '\u266e', // natural
        '1': '\u266f', // sharp
    };

    var Staff = function(noteLines, sf) {
        this.nln = [0, 2, 3, 5, 7, 8, 10]; // note line notes A-G
        this.timeSpacing = 10;
        this.noteLineSpacing = 10;
        this.paths = [];
        for (var i = 0; i < noteLines.length; i++) {
            var path = new Path({
                strokeColor: '#aaaaaa',
            });
            var p = upperLeft.subtract([0, this.noteLineSpacing * (noteLines[i] - noteLines[0])]);
            path.add(p);
            p.x = view.viewSize.width - 100;
            path.add(p);
            this.paths.push(path);
        }
        this.noteLines = noteLines;
        this.sf = sf; // sharps & flats
    }
    Staff.prototype.noteInfo = function(note) {
        var i = 0, noteClass = ((note % 12) + 12) % 12, nlnl = this.nln.length;
        var octave = (note - noteClass) / 12;
        while (i < nlnl && Math.abs(noteClass - this.nln[(i+1)%nlnl] - this.sf[(i+1)%nlnl]) < Math.abs(noteClass - this.nln[i] - this.sf[i]))
            i++;
        i = i % nlnl;

        return {
            nl: i + octave * nlnl,
            sf: noteClass - this.nln[i] - this.sf[i],
            y: (this.noteLines[0] - i - octave * nlnl) * this.noteLineSpacing,
        }
    }
    Staff.prototype.lineToNote = function(line) {
        var lineClass = ((line % this.nln.length) + this.nln.length) % this.nln.length;
        var octave = (line - lineClass) / this.nln.length;
        return this.nln[lineClass] + this.sf[lineClass] + octave * 12;
    }
    Staff.prototype.noteToLine = function(note) {
        var i = 0, noteClass = ((note % 12) + 12) % 12, nlnl = this.nln.length;
        var octave = (note - noteClass) / 12;
        while (i < nlnl && Math.abs(noteClass - this.nln[(i+1)%nlnl] - this.sf[(i+1)%nlnl]) < Math.abs(noteClass - this.nln[i] - this.sf[i]))
            i++;
        i = i % nlnl;

        return i + octave * nlnl;
    }
    Staff.prototype.lineToY = function(line) {
        return (this.noteLines[0] - line) * this.noteLineSpacing;
    }
    Staff.prototype.noteToY = function(note) {
        var noteLine = this.noteToLine(note);
        return this.lineToY(noteLine);
    }

    var Note = function(t, d, note, staff) {
        this.t = t; // start time
        this.d = d; // duration
        this.note = note;

        var noteInfo = staff.noteInfo(this.note);
        this.path = new Path({
            strokeColor: 'blue',
            strokeWidth: 5,
            segments: [
                [upperLeft.x + staff.timeSpacing * (this.t - leftTime),                              upperLeft.y + noteInfo.y],
                [upperLeft.x + staff.timeSpacing * (this.t - leftTime) + staff.timeSpacing * this.d, upperLeft.y + noteInfo.y]
            ],
        });
        this.text = new PointText({
            strokeColor: 'darkblue',
            fontSize: 14,
            content: sfSigns[noteInfo.sf],
            point: this.path.lastSegment.point.clone(),
        });
        this.group = new Group({
            children: [this.path, this.text],
            pivot: this.path.firstSegment.point,
        });
    }
    Note.prototype.update = function(staff) {
        var noteInfo = staff.noteInfo(this.note);
        this.group.position.x = upperLeft.x + staff.timeSpacing * (this.t - leftTime);
        this.group.position.y = upperLeft.y + noteInfo.y;
        this.text.setContent(sfSigns[noteInfo.sf]);
    }

    var Cursor = function() {
        this.t = 0;
        this.noteLine = 5;
        this.note = 8;
        this.vPath = null;
        this.hPath = null;
        this.setNote = function(note, staff) {
            this.note = note;
            this.noteLine = staff.noteToLine(note);
        }
        this.setNoteLine = function(noteLine, staff) {
            this.noteLine = noteLine;
            this.note = staff.lineToNote(noteLine);
        }
        this.update = function(staff) {
            this.vPath.position.x = upperLeft.x + staff.timeSpacing * (this.t - leftTime);
            this.vPath.position.y = upperLeft.y;
            this.hPath.position.x = upperLeft.x - 5 + staff.timeSpacing * (this.t - leftTime);
            this.hPath.position.y = upperLeft.y + staff.lineToY(this.noteLine);
        }
    }

    function init() {
    }

    $(document).ready(function() {
        var canvas = document.getElementById('canvas');
        var $canvas = $(canvas);
        paper.setup(canvas);

        var cursor = new Cursor();

        var doubleStaff = new Staff(
            [5, 3, 1, -1, -3, -7, -9, -11, -13, -15],
            keySignatures['eM']
        );

        var notes = [];

        view.onFrame = function(event) {
        }

        var tool = new Tool();
        tool.onKeyDown = function(event) {
            switch (event.key) {
                case 'h':
                    cursor.t--;
                    cursor.update(doubleStaff);
                    break;
                case 'j':
                    if (event.modifiers.shift) {
                        cursor.setNote(cursor.note - 1, doubleStaff);
                    } else {
                        cursor.setNoteLine(cursor.noteLine - 1, doubleStaff);
                    }
                    cursor.update(doubleStaff);
                    break;
                case 'k':
                    if (event.modifiers.shift) {
                        cursor.setNote(cursor.note + 1, doubleStaff);
                    } else {
                        cursor.setNoteLine(cursor.noteLine + 1, doubleStaff);
                    }
                    cursor.update(doubleStaff);
                    break;
                case 'l':
                    cursor.t++;
                    cursor.update(doubleStaff);
                    break;
                case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8':
                    var note = new Note(cursor.t, Number(event.key), cursor.note, doubleStaff);
                    notes.push(note);
                    note.update(doubleStaff);
                    break;
                case '+':
                    
                    break;
            }
        };

        window.onresize = function() {
            view.viewSize = [window.innerWidth, window.innerHeight];
            for (var i = 0; i < doubleStaff.paths.length; i++) {
                if (doubleStaff.paths[i].segments.length > 0) {
                    doubleStaff.paths[i].removeSegments(1);
                }
                var p1 = doubleStaff.paths[i].firstSegment.point;
                var p2 = p1.clone();
                p2.x = view.viewSize.width - 100;
                doubleStaff.paths[i].add(p2);
            }
            view.fire('resize', view);
        }

        $(window).trigger('resize');

        //// Treble clef, i = 0: 698.46 Hz (F5)
        //for (var i = 0; i < 10; i += 2) {
        //    var path = new Path({
        //        strokeColor: '#aaaaaa',
        //    });
        //    var p = upperLeft.add([0, doubleStaff.noteLineSpacing * i]);
        //    path.add(p);
        //    p.x = view.viewSize.width - 100;
        //    path.add(p);
        //    noteLines.push(path);
        //}
        //// Bass clef, i = 12: 220 Hz (A3)
        //for (var i = 12; i < 22; i += 2) {
        //    var path = new Path({
        //        strokeColor: '#aaaaaa',
        //    });
        //    var p = upperLeft.add([0, doubleStaff.noteLineSpacing * i]);
        //    path.add(p);
        //    p.x = view.viewSize.width - 100;
        //    path.add(p);
        //    noteLines.push(path);
        //}

        cursor.vPath = new Path({
            strokeColor: 'red',
        });
        cursor.vPath.add(upperLeft);
        cursor.vPath.add(doubleStaff.paths[doubleStaff.paths.length - 1].firstSegment.point);
        cursor.vPath.pivot = upperLeft.clone();

        cursor.hPath = new Path({
            strokeColor: 'red',
        });
        cursor.hPath.add(upperLeft.add([0, 0]));
        cursor.hPath.add(upperLeft.add([-10, 0]));
    });

    return { };
});
