define(['jquery', 'jqueryui', 'paper'], function($, jQueryUi, paperJs) {
    var WindowMouseEvent = window.MouseEvent;
    paperJs.paper.install(this);
    $.ajaxSetup({cache: false});
    $nameInput = $('<input>');
    $nameInput.css('color', 'white');

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

    ///////////
    // Staff //
    ///////////
    var Staff = function(noteLines, key) {
        this.nln = [0, 2, 3, 5, 7, 8, 10]; // note line notes A-G
        this.timeSpacing = 15;
        this.noteLineSpacing = 15;
        this.keyText = new Group();
        this.paths = new Group();

        this.noteLines = noteLines;
        this.setKey(key);
        this.init();
    }
    Staff.prototype.init = function() {
        for (var i = 0; i < this.noteLines.length; i++) {
            var path = new Path({
                strokeColor: '#aaaaaa',
            });
            var p = upperLeft.subtract([0, this.noteLineSpacing * (this.noteLines[i] - this.noteLines[0])]);
            path.add(p);
            p.x = view.viewSize.width - 100;
            path.add(p);
            this.paths.addChild(path);
        }
    }
    Staff.prototype.setKey = function(key) {
        this.key = key;
        this.keyText.removeChildren();
        // TODO bass clef
        var lastLeft = null;
        var shiftRight = false;
        for (var i = 0; i < this.key.length; i++) {
            if (this.key[i] !== 0) {
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
                    content: sfSigns[this.key[i]],
                    position: upperLeft.add([10 + (shiftRight ? 15 : 0), this.lineToY(i)]),
                }));
            }
        }
    }
    Staff.prototype.noteInfo = function(note) {
        var i = 0, noteClass = ((note % 12) + 12) % 12, nlnl = this.nln.length;
        var octave = (note - noteClass) / 12;
        while (i < nlnl && Math.abs(noteClass - this.nln[(i+1)%nlnl] - this.key[(i+1)%nlnl]) < Math.abs(noteClass - this.nln[i] - this.key[i])) {
            i++;
        }
        i = i % nlnl;

        return {
            noteLine: i + octave * nlnl,
            key: noteClass - this.nln[i] - this.key[i],
            y: (this.noteLines[0] - i - octave * nlnl) * this.noteLineSpacing,
        }
    }
    Staff.prototype.lineToNote = function(line) {
        var lineClass = ((line % this.nln.length) + this.nln.length) % this.nln.length;
        var octave = (line - lineClass) / this.nln.length;
        return this.nln[lineClass] + this.key[lineClass] + octave * 12;
    }
    Staff.prototype.noteToLine = function(note) {
        var noteInfo = this.noteInfo(note);
        return noteInfo.noteLine;
    }
    Staff.prototype.lineToY = function(line) {
        return (this.noteLines[0] - line) * this.noteLineSpacing;
    }
    Staff.prototype.noteToY = function(note) {
        var noteLine = this.noteToLine(note);
        return this.lineToY(noteLine);
    }
    Staff.prototype.remove = function() {
        this.keyText.remove();
        this.paths.remove();
    }

    //////////
    // Note //
    //////////
    var Note = function(t, d, note, staff) {
        this.t = t; // start time
        this.d = d; // duration
        this.note = note;

        var noteInfo = staff.noteInfo(this.note);
        var startPoint = staff.paths.bounds.topLeft.add([staff.timeSpacing * (this.t - leftTime), noteInfo.y]);
        this.path = new Path({
            strokeColor: 'blue',
            strokeWidth: 5,
            segments: [
                startPoint,
                startPoint.add([staff.timeSpacing * this.d, 0])
            ],
        });
        this.text = new PointText({
            strokeColor: 'black',
            fontSize: 14,
            content: sfSigns[noteInfo.key],
            point: this.path.lastSegment.point.clone(),
        });
        this.group = new Group({
            children: [this.path, this.text],
            pivot: this.path.firstSegment.point,
        });
    }
    Note.prototype.refresh = function(staff) {
        var noteInfo = staff.noteInfo(this.note);
        this.group.position = staff.paths.bounds.topLeft.add([staff.timeSpacing * (this.t - leftTime), noteInfo.y]);
        this.text.setContent(sfSigns[noteInfo.key]);
    }
    Note.prototype.remove = function() {
        this.group.remove();
    }

    /////////////////
    // Composition //
    /////////////////
    var Composition = function(name, staff) {
        this.name = name;
        this.nameText = new PointText({
            strokeColor: 'black',
            fontSize: 20,
            content: this.name,
            point: [10, 30],
        });
        this.nameText.onClick = function() {
            $nameInput.dialog('open').trigger('focus');
        }
        this.dbId = null;
        this.staff = staff;
        this.notes = [];
    }
    Composition.prototype.refresh = function() {
        for (var i = 0; i < this.notes.length; i++) {
            this.notes[i].refresh(this.staff);
        }
    }
    Composition.prototype.stringify = function() {
        var data = {
            name: this.name,
            notes: [],
            staff: {
                noteLines: this.staff.noteLines,
                key: this.staff.key,
            },
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
    Composition.prototype.remove = function() {
        this.nameText.remove();
        for (var i = 0; i < this.notes.length; i++) {
            this.notes[i].remove();
        }
    }

    ////////////
    // Cursor //
    ////////////
    var Cursor = function(composition) {
        this.composition = composition;
        this.t = 0;
        this.setNoteLine(0);
        this.vPath = new Path({
            strokeColor: 'red',
            segments: [
                composition.staff.paths.bounds.topLeft,
                composition.staff.paths.bounds.bottomLeft
            ],
            pivot: composition.staff.paths.bounds.topLeft,
        });
        this.hPath = new Path({
            strokeColor: 'red',
            segments: [
                composition.staff.paths.bounds.topLeft.add([-10, composition.staff.lineToY(this.noteLine)]),
                composition.staff.paths.bounds.topLeft.add([0,   composition.staff.lineToY(this.noteLine)])
            ],
        });
    }
    Cursor.prototype.setNote = function(note) {
        this.note = note;
        this.noteLine = this.composition.staff.noteToLine(note);
    }
    Cursor.prototype.setNoteLine = function(noteLine) {
        this.noteLine = noteLine;
        this.note = this.composition.staff.lineToNote(noteLine);
    }
    Cursor.prototype.refresh = function() {
        var staff = this.composition.staff;
        this.vPath.position = staff.paths.bounds.topLeft.add([staff.timeSpacing * (this.t - leftTime), 0]);
        this.hPath.position = staff.paths.bounds.topLeft.add([staff.timeSpacing * (this.t - leftTime) - 5, staff.lineToY(this.noteLine)]);
    }
    Cursor.prototype.remove = function() {
        this.vPath.remove();
        this.hPath.remove();
    }

    $(document).ready(function() {
        var canvas = document.getElementById('canvas');
        paper.setup(canvas);

        var staff = new Staff(
            [5, 3, 1, -1, -3, -7, -9, -11, -13, -15],
            keySignatures['eM']
        );

        var composition = new Composition('Untitled', staff);

        var cursor = new Cursor(composition);

        $nameInput.dialog({
            autoOpen: false,
            buttons: {
                'OK': function() {
                    composition.name = $nameInput.val();
                    composition.nameText.content = $nameInput.val();
                    $nameInput.dialog('close');
                }
            },
            open: function() {
                $nameInput.val(composition.name);
            },
        });

        function loadComposition(id) {
            $.get({
                url: '/composition/' + id,
                dataType: 'json',
                success: function(data) {
                    // TODO change in place
                    if (data.hasOwnProperty('staff') && data['staff'].length === 2) {
                        staff.remove();
                        staff = new Staff(data.staff.noteLines, data.staff.key);
                    }
                    if (data.hasOwnProperty('notes')) {
                        composition.remove();
                        composition = new Composition(data.name, staff);
                        var notes = [];
                        for (var i = 0; i < data['notes'].length; i++) {
                            var note = new Note(data['notes'][i].t, data['notes'][i].d, data['notes'][i].n, staff);
                            notes.push(note);
                        }
                        composition.notes = notes;
                    }
                    composition.dbId = id;
                    cursor.refresh();
                    composition.refresh();
                },
            });
        }

        view.onFrame = function(event) {
        }

        var tool = new Tool();
        tool.onKeyDown = function(event) {
            switch (event.key) {
                case 'h':
                    cursor.t--;
                    if (cursor.t <= leftTime) {
                        leftTime--;
                        composition.refresh();
                    }
                    cursor.refresh();
                    break;
                case 'j':
                    if (event.modifiers.shift) {
                        cursor.setNote(cursor.note - 1);
                    } else {
                        cursor.setNoteLine(cursor.noteLine - 1);
                    }
                    cursor.refresh();
                    break;
                case 'k':
                    if (event.modifiers.shift) {
                        cursor.setNote(cursor.note + 1);
                    } else {
                        cursor.setNoteLine(cursor.noteLine + 1);
                    }
                    cursor.refresh();
                    break;
                case 'l':
                    cursor.t++;
                    if (cursor.t >= leftTime + staff.paths.bounds.width / staff.timeSpacing) {
                        leftTime++;
                        composition.refresh();
                    }
                    cursor.refresh();
                    break;
                case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8':
                    if (! $nameInput.dialog('isOpen')) {
                        var note = new Note(cursor.t, Number(event.key), cursor.note, staff);
                        composition.notes.push(note);
                    }
                    break;
                case '+':
                    // change key
                    break;
            }
        };

        window.onresize = function() {
            view.viewSize = [window.innerWidth, window.innerHeight];
            for (var i = 0; i < staff.paths.children.length; i++) {
                staff.paths.children[i].lastSegment.point.x = view.viewSize.width - 100;
            }
            sigLinks.position = staff.paths.bounds.bottomLeft.add([0, 30]);
            compositionLinks.position = staff.paths.bounds.bottomRight.add([0, 30]);
            downloadLink.point = view.bounds.bottomLeft.add([10, -10]);
            submitLink.point = downloadLink.bounds.topLeft.add([0, -5]);
            view.fire('resize', view);
        }

        var sigLinks = new Group();
        var iterPos = new Point(0, 0);
        for (var i in keySignatures) {
            var pt = new PointText({
                strokeColor: 'black',
                fontSize: 20,
                content: i,
                point: iterPos,
            });
            pt.onClick = (function() {
                var idx = i;
                return function() {
                    staff.setKey(keySignatures[idx]);
                    composition.refresh();
                }
            })()
            sigLinks.addChild(pt);
            if (sigLinks.children.length % 8 === 0) {
                iterPos = iterPos.add([0, pt.bounds.height + 5]);
                iterPos.x = 0;
            } else {
                iterPos = iterPos.add([pt.bounds.width + 10, 0]);
            }
        }
        sigLinks.pivot = sigLinks.bounds.topLeft;

        var compositionLinks = new Group();
        var iterPos = new Point(0, 0);
        for (var i in compositionIds) {
            var pt = new PointText({
                strokeColor: 'black',
                fontSize: 20,
                content: i,
                point: iterPos,
            });
            pt.onClick = (function() {
                var idx = compositionIds[i];
                return function() {
                    loadComposition(idx);
                }
            })()
            compositionLinks.addChild(pt);
            if (compositionLinks.children.length % 8 === 0) {
                iterPos = iterPos.add([0, pt.bounds.height + 5]);
                iterPos.x = 0;
            } else {
                iterPos = iterPos.add([pt.bounds.width + 10, 0]);
            }
        }
        compositionLinks.pivot = compositionLinks.bounds.topRight;

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
