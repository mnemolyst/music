define(['jquery', 'paper'], function($, paperJs) {
    paperJs.paper.install(this);

    var upperLeft = new Point(100, 100);
    var leftTime = 0;
    var topNote = 48; // 880Hz (A5)
    var timeSpacing = 20;
    var noteSpacing = 20;
    var noteLines = [];
    var cursor = {
        t: 0,
        note: 48,
        vPath: null,
        hPath: null,
        update: function() {
            this.vPath.position.x = upperLeft.x + timeSpacing * (this.t - leftTime);
            this.vPath.position.y = upperLeft.y;
            this.hPath.position.x = upperLeft.x + 5 + timeSpacing * (this.t - leftTime);
            this.hPath.position.y = frequency.noteToY(this.note);
        }
    }
    var Note = function(t, d, note) {
        this.t = t;
        this.d = d;
        this.note = note;
        this.path = new Path({
            strokeColor: 'blue',
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

    var frequency = {
        noteToFreq: function(note) {
            var bf = 55;
            var twelfthRootTwo = 1.0594630943592953;
            for (var i = 0; i < note; i++) {
                bf *= twelfthRootTwo;
            }
            return bf;
        },
        noteToY: function(note) {
            return upperLeft.y + noteSpacing * (0.5 + topNote - note);
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

        for (var i = 0; i < 24; i++) { // two octaves
            var path = new Path({
                strokeColor: 'black',
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
        cursor.hPath.add(upperLeft.add([0, noteSpacing * 0.5]));
        cursor.hPath.add(upperLeft.add([10, noteSpacing * 0.5]));
    });

    return { };
});
