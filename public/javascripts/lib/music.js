define(['jquery', 'paper'], function($, paperJs) {
    var WindowMouseEvent = window.MouseEvent;
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

    var sfSigns = {
        '-1': '\u266d', // flat
        '0': '\u266e', // natural
        '1': '\u266f', // sharp
    };

    var Staff = function(noteLines, key) {
        this.nln = [0, 2, 3, 5, 7, 8, 10]; // note line notes A-G
        this.timeSpacing = 15;
        this.noteLineSpacing = 15;
        this.noteLines = noteLines;
        this.keyText = new Group();
        this.paths = new Group();
        //this.key = key;
        //this.sf = keySignatures[key]; // sharps & flats
        this.setKey(key);
        for (var i = 0; i < noteLines.length; i++) {
            var path = new Path({
                strokeColor: '#aaaaaa',
            });
            var p = upperLeft.subtract([0, this.noteLineSpacing * (noteLines[i] - noteLines[0])]);
            path.add(p);
            p.x = view.viewSize.width - 100;
            path.add(p);
            this.paths.addChild(path);
        }
    }
    Staff.prototype.setKey = function(key) {
        this.key = key;
        this.sf = keySignatures[key];
        this.keyText.removeChildren();
        // TODO bass clef
        var lastLeft = null;
        var shiftRight = false;
        for (var i = 0; i < this.sf.length; i++) {
            if (this.sf[i] !== 0) {
                if (lastLeft === i - 1) {
                    shiftRight = true;
                    lastLeft = null;
                } else {
                    shiftRight = false
                    lastLeft = i;
                }
                this.keyText.addChild(new PointText({
                    strokeColor: 'black',
                    fontSize: 30,
                    content: sfSigns[this.sf[i]],
                    position: upperLeft.add([10 + (shiftRight ? 15 : 0), this.lineToY(i)]),
                }));
            }
        }
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
            strokeColor: 'black',
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

    var Cursor = function(staff) {
        this.t = 0;
        this.noteLine = 5;
        this.note = 8;
        this.vPath = new Path({
            strokeColor: 'red',
            segments: [
                upperLeft,
                staff.paths.lastChild.firstSegment.point
            ],
            pivot: upperLeft,
        });
        this.hPath = new Path({
            strokeColor: 'red',
            segments: [
                upperLeft.add([0, 0]),
                upperLeft.add([-10, 0])
            ],
        });
    }
    Cursor.prototype.setNote = function(note, staff) {
        this.note = note;
        this.noteLine = staff.noteToLine(note);
    }
    Cursor.prototype.setNoteLine = function(noteLine, staff) {
        this.noteLine = noteLine;
        this.note = staff.lineToNote(noteLine);
    }
    Cursor.prototype.update = function(staff) {
        this.vPath.position.x = upperLeft.x + staff.timeSpacing * (this.t - leftTime);
        this.vPath.position.y = upperLeft.y;
        this.hPath.position.x = upperLeft.x - 5 + staff.timeSpacing * (this.t - leftTime);
        this.hPath.position.y = upperLeft.y + staff.lineToY(this.noteLine);
    }

    var Composition = function() {
        this.name = 'Mine';
        this.notes = [];
        this.dbId = null;
        this.update = function(staff) {
            for (var i = 0; i < this.notes.length; i++) {
                this.notes[i].update(staff);
            }
        }
    }
    Composition.prototype.stringify = function() {
        var data = {
            name: this.name,
            notes: [],
        };
        for (var i = 0; i < this.notes.length; i++) {
            data.notes.push({
                t: this.notes[i].t,
                d: this.notes[i].d,
                n: this.notes[i].note,
            });
        }
        return JSON.stringify(data);
    }

    $(document).ready(function() {
        var canvas = document.getElementById('canvas');
        var $canvas = $(canvas);
        paper.setup(canvas);

        var doubleStaff = new Staff(
            [5, 3, 1, -1, -3, -7, -9, -11, -13, -15],
            'eM'
        );

        var cursor = new Cursor(doubleStaff);

        var composition = new Composition();

        view.onFrame = function(event) {
        }

        var tool = new Tool();
        tool.onKeyDown = function(event) {
            switch (event.key) {
                case 'h':
                    cursor.t--;
                    if (cursor.t <= leftTime) {
                        leftTime--;
                        composition.update(doubleStaff);
                    }
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
                    if (cursor.t >= leftTime + doubleStaff.paths.bounds.width / doubleStaff.timeSpacing) {
                        leftTime++;
                        composition.update(doubleStaff);
                    }
                    cursor.update(doubleStaff);
                    break;
                case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8':
                    var note = new Note(cursor.t, Number(event.key), cursor.note, doubleStaff);
                    composition.notes.push(note);
                    note.update(doubleStaff);
                    break;
                case '+':
                    // change key
                    break;
            }
        };

        window.onresize = function() {
            view.viewSize = [window.innerWidth, window.innerHeight];
            //var rect = new Rectangle(upperLeft, view.viewSize.subtract([200, 200]));
            //doubleStaff.paths.fitBounds(rect);
            for (var i = 0; i < doubleStaff.paths.children.length; i++) {
                doubleStaff.paths.children[i].lastSegment.point.x = view.viewSize.width - 100;
            }
            downloadLink.point = view.bounds.bottomLeft.add([10, -10]);
            submitLink.point = downloadLink.bounds.topLeft.add([0, -5]);
            view.fire('resize', view);
        }

        var sigLinks = new Group();
        var sigPos = upperLeft.add([0, doubleStaff.paths.bounds.height + 30]);
        for (var i in keySignatures) {
            var sl = new PointText({
                strokeColor: 'black',
                fontSize: 20,
                content: i,
                point: sigPos,
            });
            sl.onClick = (function() {
                var key = i;
                return function() {
                    doubleStaff.setKey(key);
                    composition.update(doubleStaff);
                }
            })()
            sigLinks.addChild(sl);
            if (sigLinks.children.length % 8 === 0) {
                sigPos = doubleStaff.paths.bounds.bottomLeft.add([0, 30 + sigLinks.children.length / 8 * 20]);
            } else {
                sigPos = sigPos.add([sl.bounds.width + 10, 0]);
            }
        }

        var downloadLink = new PointText({
            strokeColor: 'black',
            fontSize: 20,
            content: 'Download',
        });
        downloadLink.onClick = function() {
            var data = composition.stringify();
            var a = document.createElement('a');
            var now = new Date();
            var dateTime = now.getFullYear() + '-' + (now.getMonth() + 1) + '-' + now.getDate() + '-' + now.getHours() + '-' + now.getMinutes() + '-' + now.getSeconds();
            a.download = 'composition-' + dateTime + '.json';
            a.title = 'Download composition';
            a.href = 'data:text/json,' + data;

            document.querySelector('body').appendChild(a);
            var clickEvent = new WindowMouseEvent('click', {
                bubbles: false,
                cancelable: false,
                view: window,
            });
            a.dispatchEvent(clickEvent);
        }

        var submitLink = new PointText({
            strokeColor: 'black',
            fontSize: 20,
            content: 'Submit',
        });
        submitLink.onClick = function() {
            var data = composition.stringify();
            if (composition.dbId) {
                url = '/composition/' + composition.dbId;
            } else {
                url = '/composition';
            }
            $.ajax({
                url: url,
                method: 'POST',
                data: data,
                contentType: 'application/json',
                success: function(data) {
                    if (composition.dbId === null) {
                        composition.dbId = data;
                    }
                }
            });
        }

        $(window).trigger('resize');

        //var AudioContext = window.AudioContext || window.webkitAudioContext;
        //var audioCtx = new AudioContext();
        //var oscillator = audioCtx.createOscillator();
        //oscillator.type = 'sine';
        //oscillator.frequency.value = 440;
        //var gainNode = audioCtx.createGain();
        //oscillator.connect(gainNode);
        //gainNode.connect(audioCtx.destination);
        //oscillator.start();
        //oscillator.stop(1);
    });

    return { };
});
