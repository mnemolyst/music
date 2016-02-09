define(['jquery', 'paper'], function($, paperJs) {
    paperJs.paper.install(this);

    var upperLeft = new Point(100, 100);
    var leftTime = 0;

    var Staff = function(linesAt, nln, sf) {
        this.timeSpacing = 10;
        this.noteSpacing = 10;
        this.drawnLines = [];
        for (var i = 0; i < linesAt.length; i++) {
            var path = new Path({
                strokeColor: '#aaaaaa',
            });
            var p = upperLeft.subtract([0, this.noteSpacing * (linesAt[i] - linesAt[0])]);
            path.add(p);
            p.x = view.viewSize.width - 100;
            path.add(p);
            this.drawnLines.push(path);
        }
        this.nln = nln; // note line notes
        this.sf = sf; // sharps & flats
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
        var octave = (line - lineClass) / this.nln.length;
        return this.nln[lineClass] + this.sf[lineClass];
    }
    Staff.prototype.noteToY = function(note) {
        var noteLine = this.noteToLine(note);
        return (this.drawnLines[0] - noteLine.nl) * this.noteSpacing;
    }

    var Note = function(t, d, note) {
        this.t = t; // start time
        this.d = d; // duration
        this.note = note;
        this.path = new Path({
            strokeColor: 'blue',
            strokeWidth: 5,
        });
    }
    Note.prototype.update = function(staff) {
        if (this.path.isEmpty()) {
            var p = new Point(upperLeft.x + staff.timeSpacing * (this.t - leftTime), staff.noteToY(this.note));
            this.path.add(p);
            p.x += staff.timeSpacing * this.d;
            this.path.add(p);
        }
        this.path.position.x = upperLeft.x + staff.timeSpacing * (this.t - leftTime);
        this.path.position.y = staff.noteToY(this.note);
    }

    var cursor = {
        t: 0,
        note: 8,
        vPath: null,
        hPath: null,
        update: function() {
            this.vPath.position.x = upperLeft.x + doubleStaff.timeSpacing * (this.t - leftTime);
            this.vPath.position.y = upperLeft.y;
            this.hPath.position.x = upperLeft.x - 5 + doubleStaff.timeSpacing * (this.t - leftTime);
            this.hPath.position.y = doubleStaff.noteToY(this.note);
        }
    }

    function init() {
    }

    $(document).ready(function() {
        var canvas = document.getElementById('canvas');
        var $canvas = $(canvas);
        paper.setup(canvas);

        var doubleStaff = new Staff( [5, 3, 1, -1, -3, -7, -9, -11, -13, -15], [0, 2, 3, 5, 7, 8, 10], [0, 0, 0, 0, 0, 0, 0] );

        view.onFrame = function(event) {
        }

        //var tool = new Tool();
        //tool.onKeyDown = function(event) {
        //    switch (event.key) {
        //        case 'h':
        //            cursor.t--;
        //            cursor.update();
        //            break;
        //        case 'j':
        //            cursor.note--;
        //            cursor.update();
        //            break;
        //        case 'k':
        //            cursor.note++;
        //            cursor.update();
        //            break;
        //        case 'l':
        //            cursor.t++;
        //            cursor.update();
        //            break;
        //        case '1':
        //            notes.push(new Note(cursor.t, 1, cursor.note));
        //            break;
        //    }
        //};

        window.onresize = function() {
            view.viewSize = [window.innerWidth, window.innerHeight];
            for (var i = 0; i < doubleStaff.drawnLines.length; i++) {
                if (doubleStaff.drawnLines[i].segments.length > 0) {
                    doubleStaff.drawnLines[i].removeSegments(1);
                }
                var p1 = doubleStaff.drawnLines[i].firstSegment.point;
                var p2 = p1.clone();
                p2.x = view.viewSize.width - 100;
                doubleStaff.drawnLines[i].add(p2);
            }
            view.fire('resize', view);
        }

        $(window).trigger('resize');

        //// Treble clef, i = 0: 698.46 Hz (F5)
        //for (var i = 0; i < 10; i += 2) {
        //    var path = new Path({
        //        strokeColor: '#aaaaaa',
        //    });
        //    var p = upperLeft.add([0, doubleStaff.noteSpacing * i]);
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
        //    var p = upperLeft.add([0, doubleStaff.noteSpacing * i]);
        //    path.add(p);
        //    p.x = view.viewSize.width - 100;
        //    path.add(p);
        //    noteLines.push(path);
        //}

        //cursor.vPath = new Path({
        //    strokeColor: 'red',
        //});
        //cursor.vPath.add(upperLeft);
        //cursor.vPath.add(doubleStaff.drawnLines[doubleStaff.drawnLines.length - 1].firstSegment.point);
        //cursor.vPath.pivot = upperLeft.clone();

        //cursor.hPath = new Path({
        //    strokeColor: 'red',
        //});
        //cursor.hPath.add(upperLeft.add([0, 0]));
        //cursor.hPath.add(upperLeft.add([-10, 0]));
    });

    return { };
});
