define(['jquery', 'paper'], function($, paperJs) {
    paperJs.paper.install(this);

    var upperLeft = new Point(100, 100);
    var leftTime = 0;
    var topNoteLine = 8; // 698.46 Hz (F5)
    var timeSpacing = 10;
    var noteSpacing = 10;
    var noteLines = [];
    var staff = {
        noteLines = [
            { name: 'f5', note: 8, },
            { name: 'e5', note: 7, },
            { name: 'd5', note: 5, },
            { name: 'c5', note: 3, },
            { name: 'b4', note: 2, },
            { name: 'a4', note: 0, },
            { name: 'g4', note: -2, },
            { name: 'f4', note: -4, },
            { name: 'e4', note: -5, },

            { name: 'a3', note: -12, },
            { name: 'g3', note: -14, },
            { name: 'f3', note: -16, },
            { name: 'e3', note: -17, },
            { name: 'd3', note: -19, },
            { name: 'c3', note: -21, },
            { name: 'b2', note: -22, },
            { name: 'a2', note: -24, },
            { name: 'g2', note: -26, },
        ],
    }
    no = [0, 2, 3, 5, 7, 8, 10];
    note = 1;
    for (var i = 0, mn = note % 12; mn < no[i]; i++);

    var cursor = {
        t: 0,
        noteLine: 8,
        vPath: null,
        hPath: null,
        update: function() {
            this.vPath.position.x = upperLeft.x + timeSpacing * (this.t - leftTime);
            this.vPath.position.y = upperLeft.y;
            this.hPath.position.x = upperLeft.x - 5 + timeSpacing * (this.t - leftTime);
            this.hPath.position.y = frequency.noteToY(this.note);
        }
    }

    var Note = function(t, d, note) {
        this.t = t;
        this.d = d;
        this.note = note;
        this.path = new Path({
            strokeColor: 'blue',
            strokeWidth: 5,
        });
        var p = new Point(upperLeft.x + timeSpacing * (this.t - leftTime), frequency.noteToY(this.note));
        this.path.add(p);
        p.x += timeSpacing * this.d;
        this.path.add(p);
    }
    Note.prototype.update = function() {
        this.path.position.x = upperLeft.x + timeSpacing * (this.t - leftTime);
        this.path.position.y = frequency.noteToY(this.note);
    }

    var notes = [];
    var scale = [3, 5, 7, 8, 10, 12, 14]; // C Maj

    var frequency = {
        noteToFreq: function(note) {
            var bf = 440; // Hz (note A1)
            if (note < 0) {
                for (var i = 0; i > note; i--) {
                    bf *= 0.9438743126816934; // inverse of twelfth root of 2
                }
            } else if (note > 0) {
                for (var i = 0; i < note; i++) {
                    bf *= 1.0594630943592953; // twelfth root of 2
                }
            }
            return bf;
        },
        noteToY: function(note) {
            return upperLeft.y + noteSpacing * (topNoteLine - note);
        },
        noteLineToNote: function(noteLine) {
            return 
        },
    }

    function init() {
    }

    $(document).ready(function() {
        var canvas = document.getElementById('canvas');
        var $canvas = $(canvas);
        paper.setup(canvas);

        view.onFrame = function(event) {
        }

        var tool = new Tool();
        tool.onKeyDown = function(event) {
            switch (event.key) {
                case 'h':
                    cursor.t--;
                    cursor.update();
                    break;
                case 'j':
                    cursor.note--;
                    cursor.update();
                    break;
                case 'k':
                    cursor.note++;
                    cursor.update();
                    break;
                case 'l':
                    cursor.t++;
                    cursor.update();
                    break;
                case '1':
                    notes.push(new Note(cursor.t, 1, cursor.note));
                    break;
            }
        };

        window.onresize = function() {
            view.viewSize = [window.innerWidth, window.innerHeight];
            for (var i = 0; i < noteLines.length; i++) {
                if (noteLines[i].segments.length > 0) {
                    noteLines[i].removeSegments(1);
                }
                var p1 = noteLines[i].firstSegment.point;
                var p2 = p1.clone();
                p2.x = view.viewSize.width - 100;
                noteLines[i].add(p2);
            }
            view.fire('resize', view);
        }

        view.viewSize = [window.innerWidth, window.innerHeight];

        // Treble clef, i = 0: 698.46 Hz (F5)
        for (var i = 0; i < 10; i += 2) {
            var path = new Path({
                strokeColor: '#aaaaaa',
            });
            var p = upperLeft.add([0, noteSpacing * i]);
            path.add(p);
            p.x = view.viewSize.width - 100;
            path.add(p);
            noteLines.push(path);
        }
        // Bass clef, i = 12: 220 Hz (A3)
        for (var i = 12; i < 22; i += 2) {
            var path = new Path({
                strokeColor: '#aaaaaa',
            });
            var p = upperLeft.add([0, noteSpacing * i]);
            path.add(p);
            p.x = view.viewSize.width - 100;
            path.add(p);
            noteLines.push(path);
        }

        cursor.vPath = new Path({
            strokeColor: 'red',
        });
        cursor.vPath.add(upperLeft);
        cursor.vPath.add(noteLines[noteLines.length - 1].firstSegment.point);
        cursor.vPath.pivot = upperLeft.clone();

        cursor.hPath = new Path({
            strokeColor: 'red',
        });
        cursor.hPath.add(upperLeft.add([0, 0]));
        cursor.hPath.add(upperLeft.add([-10, 0]));
    });

    return { };
});
