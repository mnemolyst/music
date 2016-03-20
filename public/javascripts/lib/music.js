define(['jquery', 'jqueryui', 'paper'], function($, jQueryUi, paperJs) {
    var WindowMouseEvent = window.MouseEvent;
    paperJs.paper.install(this);
    $.ajaxSetup({cache: false});
    $nameInput = $('<input>');
    $nameInput.css('color', 'white');

    var upperLeft = new Point(10, 200);
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

    var melodyColors = {
        1: 'red',
        2: 'blue',
        3: 'green',
        4: 'yellow'
    };
    var currentMelody = 1;
    var dragBox = null;
    var dragStart = new Point();

    ///////////
    // Staff //
    ///////////
    var Staff = function(noteLines, keySig, timeDiv) {
        this.nln = [0, 2, 3, 5, 7, 8, 10, 12]; // note line notes A-G
        this.timeSpacing = 15; // (px / beat)
        this.noteLineSpacing = 15;
        this.keyText = new Group();
        this.timeText = new Group();
        this.hPaths = new Group();
        this.vPaths = new Group();
        this.paths = new Group({
            children: [this.hPaths, this.vPaths],
        });

        this.noteLines = noteLines;
        this.setKey(keySig);
        this.timeDiv = timeDiv; // (beats / measure)
    }
    Staff.prototype.hRefresh = function() {
        this.hPaths.removeChildren();

        for (var i = 0; i < this.noteLines.length; i++) {
            var path = new Path({
                strokeColor: '#aaaaaa',
            });
            var p = upperLeft.add([0, this.noteLineSpacing * (this.noteLines[0] - this.noteLines[i])]);
            path.add(p);
            p.x = view.bounds.width - 10;
            path.add(p);
            this.hPaths.addChild(path);
        }
    }
    Staff.prototype.vRefresh = function() {
        this.vPaths.removeChildren();
        this.timeText.removeChildren();

        var ppm = this.timeSpacing * this.timeDiv; // (px / measure)
        var startX = ppm - (leftTime * this.timeSpacing) % ppm;
        for (var i = 0; i < this.hPaths.bounds.width / ppm; i++) {
            var path = new Path({
                strokeColor: '#aaaaaa',
            });
            var p = upperLeft.add([startX + i * ppm, 0]);
            path.add(p);
            path.add(p.add([0, this.hPaths.bounds.height]));
            this.vPaths.addChild(path);

            this.timeText.addChild(new PointText({
                strokeColor: 'black',
                fontSize: 20,
                content: Math.floor(leftTime / this.timeDiv) + i + 1,
                position: upperLeft.add([startX + i * ppm, -15]),
            }));
        }
    }
    Staff.prototype.refresh = function() {
        this.hRefresh();
        this.vRefresh();
    }
    Staff.prototype.setKey = function(keySig) {
        this.keySig = keySig;
        this.keyText.removeChildren();
        // TODO bass clef
        var lastLeft = null;
        var shiftRight = false;
        for (var i = 0; i < this.keySig.length; i++) {
            if (this.keySig[i] !== 0) {
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
                    content: sfSigns[this.keySig[i]],
                    position: upperLeft.add([10 + (shiftRight ? 15 : 0), this.lineToY(i)]),
                }));
            }
        }
    }
    Staff.prototype.noteInfo = function(note) {
        var noteClass = ((note % 12) + 12) % 12;
        var octave = (note - noteClass) / 12;
        var best = null;
        var bestType = 3;
        var bestDiff = 12;
        for (var i = 0; i < 8; i++) {
            var i7 = i % 7;
            var diff = this.nln[i] + this.keySig[i7] - noteClass;
            if (diff === 0) {
                best = i;
                break;
            } else if (bestType >= 1 && (diff === -1 || diff === 1) && diff === this.keySig[i7]) {
                best = i;
                bestType = 1;
            } else if (bestType >= 2 && (diff === -1 || diff === 1) && 0 === this.keySig[i7]) {
                best = i;
                bestType = 2;
            } else if (bestType >= 3 && Math.abs(diff) < bestDiff) {
                best = i;
                bestDiff = Math.abs(diff);
            }
        }
        var best7 = best % 7;

        return {
            noteLine: best + octave * 7,
            sf: noteClass - this.nln[best] - this.keySig[best7],
            y: (this.noteLines[0] - best - octave * 7) * this.noteLineSpacing,
        }
    }
    Staff.prototype.lineToNote = function(line) {
        var lineClass = ((line % 7) + 7) % 7;
        var octave = (line - lineClass) / 7;
        return this.nln[lineClass] + this.keySig[lineClass] + octave * 12;
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
        this.timeText.remove();
        this.paths.remove();
    }

    //////////
    // Note //
    //////////
    var Note = function(t, d, note, melody, staff) {
        this.t = t; // start time
        this.d = d; // duration
        this.note = note;
        this.melody = melody;

        var noteInfo = staff.noteInfo(this.note);
        var startPoint = staff.hPaths.bounds.topLeft.add([staff.timeSpacing * (this.t - leftTime), noteInfo.y]);
        this.path = new Path({
            strokeColor: '#999999',
            strokeWidth: 5,
            segments: [
                startPoint,
                startPoint.add([staff.timeSpacing * this.d, 0])
            ],
        });
        this.text = new PointText({
            strokeColor: '#999999',
            fontSize: 14,
            content: sfSigns[noteInfo.sf],
            point: this.path.lastSegment.point.clone(),
        });
        this.group = new Group({
            children: [this.path, this.text],
            pivot: this.path.firstSegment.point,
        });
    }
    Note.prototype.refresh = function(staff) {
        var noteInfo = staff.noteInfo(this.note);
        this.group.position = staff.hPaths.bounds.topLeft.add([staff.timeSpacing * (this.t - leftTime), noteInfo.y]);
        this.text.setContent(sfSigns[noteInfo.sf]);
        this.path.lastSegment.point.x = this.path.firstSegment.point.x + staff.timeSpacing * this.d;
        if (this.melody === null) {
            this.path.strokeColor = 'violet';
        } else if (melodyColors.hasOwnProperty(this.melody)) {
            this.path.strokeColor = melodyColors[this.melody];
        } else {
            this.path.strokeColor = '#999999';
        }
        this.text.point = this.path.lastSegment.point.clone();
    }
    Note.prototype.remove = function() {
        this.group.remove();
    }

    /////////////////
    // Composition //
    /////////////////
    var Composition = function(name, staff, dbId) {
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
        this.dbId = dbId || null;
        this.staff = staff;
        this.notes = [];
        this.tempo = 500000; // microseconds per beat
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
                keySig: this.staff.keySig,
                timeDiv: this.staff.timeDiv,
            },
        };
        for (var i = 0; i < this.notes.length; i++) {
            data.notes.push({
                t: this.notes[i].t,
                d: this.notes[i].d,
                n: this.notes[i].note,
                m: this.notes[i].melody,
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
            strokeWidth: 1.5,
        });
        this.hPath = new Path({
            strokeColor: 'red',
            strokeWidth: 2.5,
            segments: [
                [0, 0],
                [10, 0]
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
        this.vPath.segments = [
            staff.hPaths.bounds.topLeft.add([staff.timeSpacing * (this.t - leftTime), 0]),
            staff.hPaths.bounds.bottomLeft.add([staff.timeSpacing * (this.t - leftTime), 0])
        ],
        this.hPath.position.x = staff.hPaths.bounds.topLeft.x + staff.timeSpacing * (this.t - leftTime) - 5;
        this.hPath.position.y = staff.hPaths.bounds.topLeft.y + staff.lineToY(this.noteLine);
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
            keySignatures['am'],
            4
        );

        var composition = new Composition('Untitled', staff);

        var cursor = new Cursor(composition);

        function splitCursor() {
            var melodiesAtIndicator = {};
            for (var i = 0; i < composition.notes.length; i++) {
                var note = composition.notes[c[i][j]];
                if (note.t - 5 < indicatorT && indicatorT < note.t + note.d + 5) {
                    if (! melodiesAtIndicator.hasOwnProperty(note.melody)) {
                        melodiesAtIndicator[note.melody] = {low: note.n, high: note.n};
                    }
                    melodiesAtIndicator[note.melody].low = melodiesAtIndicator[note.melody].low < note.n ? melodiesAtIndicator[note.melody].low : note.n;
                    melodiesAtIndicator[note.melody].high = melodiesAtIndicator[note.melody].high < note.n ? note.n : melodiesAtIndicator[note.melody].high;
                }
            }
        }

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
                    if (data.hasOwnProperty('staff')) {
                        staff.remove();
                        staff = new Staff(data.staff.noteLines, data.staff.keySig, data.staff.timeDiv);
                        staff.refresh();
                    }
                    if (data.hasOwnProperty('notes')) {
                        composition.remove();
                        composition = new Composition(data.name, staff, id);
                        var notes = [];
                        for (var i = 0; i < data['notes'].length; i++) {
                            var note = new Note(data['notes'][i].t, data['notes'][i].d, data['notes'][i].n, data['notes'][i].m, staff);
                            notes.push(note);
                        }
                        composition.notes = notes;
                        composition.tempo = data.tempo || 500000; // microseconds per beat
                        composition.refresh();
                    }
                    cursor.refresh();
                },
            });
        }

        view.onFrame = function(event) {
        }

        var tool = new Tool();
        tool.onKeyDown = function(event) {
            switch (event.key) {
                case 'h':
                    if (cursor.t === 0) {
                        break;
                    }
                    if (event.modifiers.shift) {
                        cursor.t = Math.floor((cursor.t - 1) / staff.timeDiv) * staff.timeDiv;
                    } else {
                        cursor.t = Math.ceil(cursor.t - 1);
                    }
                    if (cursor.t <= leftTime) {
                        leftTime = cursor.t - (cursor.t === 0 ? 0 : 1);
                        composition.refresh();
                        staff.vRefresh();
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
                    if (event.modifiers.shift) {
                        cursor.t = Math.floor(cursor.t / staff.timeDiv + 1) * staff.timeDiv;
                    } else {
                        cursor.t = Math.floor(cursor.t + 1);
                    }
                    if ((cursor.t - leftTime) * staff.timeSpacing >= staff.hPaths.bounds.width) {
                        leftTime = cursor.t - staff.hPaths.bounds.width / staff.timeSpacing;
                        composition.refresh();
                        staff.vRefresh();
                    }
                    cursor.refresh();
                    break;
                case 'n':
                    if (event.modifiers.shift) {
                        var sortFunc = function(a, b) { return b.t - a.t; }
                        var findFunc = function(el, idx, arr) { return (cursor.t > el.t) && (idx === 0 || cursor.t <= arr[idx - 1].t) && (el.note === cursor.note); }
                    } else {
                        var sortFunc = function(a, b) { return a.t - b.t; }
                        var findFunc = function(el, idx, arr) { return (cursor.t < el.t) && (idx === 0 || cursor.t >= arr[idx - 1].t) && (el.note === cursor.note); }
                    }

                    var filtered = composition.notes.filter(function(el) {
                        return el.note === cursor.note;
                    });
                    filtered.sort(sortFunc);
                    var idx = filtered.findIndex(findFunc);

                    if (idx !== -1) {
                        cursor.t = filtered[idx].t;
                        if ((cursor.t - leftTime) * staff.timeSpacing >= staff.hPaths.bounds.width) {
                            leftTime = cursor.t - staff.hPaths.bounds.width / staff.timeSpacing;
                            composition.refresh();
                            staff.vRefresh();
                        }
                        if (cursor.t <= leftTime) {
                            leftTime = cursor.t - (cursor.t === 0 ? 0 : 1);
                            composition.refresh();
                            staff.vRefresh();
                        }
                        cursor.refresh();
                    }
                    break;
                case 'e':
                    var idx = composition.notes.findIndex(function(el) {
                        return (cursor.t >= el.t - 1) && (cursor.t < el.t + el.d) && (el.note === cursor.note);
                    });
                    if (idx !== -1 && composition.notes[idx].d > 1) {
                        cursor.t = composition.notes[idx].t + composition.notes[idx].d;
                        if ((cursor.t - leftTime) * staff.timeSpacing >= staff.hPaths.bounds.width) {
                            leftTime = cursor.t - staff.hPaths.bounds.width / staff.timeSpacing;
                            composition.refresh();
                            staff.vRefresh();
                        }
                        cursor.refresh();
                    }
                    break;
                case '0':
                    cursor.t = 0;
                    leftTime = 0;
                    composition.refresh();
                    staff.vRefresh();
                    cursor.refresh();
                    break;
                case '^':
                    cursor.t = Math.floor(leftTime + 1)
                    cursor.refresh();
                    break;
                case '$':
                    cursor.t = Math.floor(leftTime + staff.hPaths.bounds.width / staff.timeSpacing);
                    cursor.refresh();
                    break;
                //case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
                //    if (! $nameInput.dialog('isOpen')) {
                //        var note = new Note(cursor.t, Number(event.key), cursor.note, 0, staff);
                //        composition.notes.push(note);
                //    }
                //    break;
                case '1': case '2': case'3': case '4': case '5':
                    currentMelody = Number(event.key);
                    break;
                case '-':
                    var idx = composition.notes.findIndex(function(el) {
                        return (cursor.t >= el.t - 1) && (cursor.t < el.t + el.d) && (el.note === cursor.note);
                    });
                    if (idx !== -1 && composition.notes[idx].d > 1) {
                        composition.notes[idx].d--;
                        composition.notes[idx].refresh(composition.staff);
                    }
                    break;
                case '+':
                    var idx = composition.notes.findIndex(function(el) {
                        return (cursor.t >= el.t - 1) && (cursor.t < el.t + el.d) && (el.note === cursor.note);
                    });
                    if (idx !== -1) {
                        composition.notes[idx].d++;
                        composition.notes[idx].refresh(composition.staff);
                    }
                    break;
                case 'x':
                    var idx = composition.notes.findIndex(function(el) {
                        return (cursor.t >= el.t - 1) && (cursor.t < el.t + el.d) && (el.note === cursor.note);
                    });
                    if (idx !== -1) {
                        composition.notes[idx].remove();
                        composition.notes.splice(idx, 1);
                    }
                    break;
                case '/':
                    var idx = composition.notes.findIndex(function(el) {
                        return (cursor.t >= el.t - 1) && (cursor.t < el.t + el.d) && (el.note === cursor.note);
                    });
                    if (idx !== -1) {
                        var oldNote = composition.notes[idx];
                        var oldNoteD3 = oldNote.d / 3;
                        var newNotes = [];
                        for (var i = 0; i < 3; i++) {
                            var newNote = new Note(oldNote.t + i * oldNoteD3, oldNoteD3, oldNote.note, oldNode.melody, staff);
                            newNotes.push(newNote);
                        }
                        composition.notes[idx].remove();
                        composition.notes.splice(idx, 1, newNotes[0], newNotes[1], newNotes[2]);
                    }
                    break;
            }
            //console.log(event.key);
        }

        tool.onMouseDown = function(event) {
            dragStart = event.point;
            dragBox = new Path({
                strokeColor: 'red',
            });
        }

        tool.onMouseDrag = function(event) {
            var left = dragStart.x < event.point.x ? dragStart.x : event.point.x;
            var right = dragStart.x < event.point.x ? event.point.x : dragStart.x;
            var top = dragStart.y < event.point.y ? dragStart.y : event.point.y;
            var bottom = dragStart.y < event.point.y ? event.point.y : dragStart.y;
            dragBox.segments = [[left, top], [right, top], [right, bottom], [left, bottom], [left, top]];
        }

        tool.onMouseUp = function(event) {
            var count = 0;
            for (var i = 0; i < composition.notes.length; i++) {
                if (composition.notes[i].path.isInside(dragBox.bounds)) {
                    count++;
                    if (melodyColors.hasOwnProperty(currentMelody)) {
                        composition.notes[i].melody = currentMelody;
                    } else {
                        delete composition.notes[i].melody;
                    }
                }
            }
            dragBox.remove();
            composition.refresh();
            console.log('selected', count);
        }

        window.onresize = function() {
            view.viewSize = [window.innerWidth, window.innerHeight];
            view.fire('resize', view);
            staff.refresh();
            composition.refresh();
            cursor.refresh();
            sigLinks.position = staff.hPaths.bounds.bottomLeft.add([0, 30]);
            compositionLinks.position = staff.hPaths.bounds.bottomRight.add([0, 30]);
            downloadLink.point = view.bounds.bottomLeft.add([10, -10]);
            submitLink.point = downloadLink.bounds.topLeft.add([0, -5]);
            progressBar.position = submitLink.bounds.rightCenter.add([5, 0]);
            playLink.point = submitLink.bounds.topLeft.add([0, -5]);
            melodyLink.point = playLink.bounds.topLeft.add([0, -5]);
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
                    sigLinks.strokeColor = 'black';
                    this.strokeColor = 'red';
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
        for (var i = 0; i < dbCompositions.length; i++) {
            var pt = new PointText({
                strokeColor: 'black',
                fontSize: 20,
                content: dbCompositions[i].name,
                point: iterPos,
            });
            pt.onClick = (function() {
                var id = dbCompositions[i].id;
                return function() {
                    loadComposition(id);
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
        var progressBar = new Path({
            strokeColor: 'red',
            strokeWidth: 10,
            segments: [
                submitLink.bounds.rightCenter.add([5, 0]),
                submitLink.bounds.rightCenter.add([5, 0])
            ],
            pivot: submitLink.bounds.rightCenter.add([5, 0]),
        });
        submitLink.onClick = function() {
            progressBar.lastSegment.point = progressBar.firstSegment.point.clone();
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
                xhr: function() {
                    var xhr = new window.XMLHttpRequest();
                    xhr.upload.addEventListener('progress', function(e) {
                        if (e.lengthComputable) {
                            var pc = e.loaded / e.total * submitLink.bounds.width;
                            progressBar.lastSegment.point = progressBar.firstSegment.point.add([pc, 0]);
                        }
                    });
                    return xhr;
                },
                success: function(data) {
                    if (composition.dbId === null) {
                        composition.dbId = data;
                    }
                }
            });
        }

        var playLink = new PointText({
            strokeColor: 'black',
            fontSize: 20,
            content: 'Play',
        });
        playLink.onClick = function() {
            //var params = composition.notes.reduce(function(prev, curr) {
            //    if (prev.low === null || curr.note < prev.low) {
            //        prev.low = curr.note;
            //    }
            //    if (prev.high === null || prev.high < curr.note) {
            //        prev.high = curr.note;
            //    }
            //    if (prev.len === null || prev.len < curr.t + curr.d) {
            //        prev.len = curr.t + curr.d;
            //    }
            //    return prev;
            //}, {low:null, high:null, len:null});
            composition.notes.sort(function(a, b) {
                return (b.t + b.d) - (a.t + a.d);
            });
            var lastNote = composition.notes[0];
            var offlineCtx = new OfflineAudioContext(1, 44100 * Math.ceil((lastNote.t + lastNote.d) * composition.tempo), 44100);
            composition.notes.sort(function(a, b) {
                return a.t - b.t;
            });
            
            var sources = [];
            //var oscillator = offlineCtx.createOscillator();
            //sources.push(oscillator);
            for (var i = 0; i < composition.notes.length; i++) {
                var thisSrcIdx = null;
                for (var j = 0; j < sources.length; j++) {
                    var prevNote = composition.notes[sources[j].idx];
                    if (prevNote.t + prevNote.d <= composition.notes[i].t) {
                        thisSrcIdx = j;
                    }
                }
                if (thisSrcIdx === null) {
                    var osc = offlineCtx.createOscillator();
                    var gain = offlineCtx.createGain();
                    gain.gain.setValueAtTime(0, 0);
                    osc.connect(gain);
                    osc.start(0);

                    sources.push({
                        osc: osc,
                        gain: gain,
                        idx: i,
                    });
                    thisSrcIdx = sources.length - 1;
                    console.log('new src', sources.length);
                }
                sources[thisSrcIdx].idx = i;
                var startTime = composition.notes[i].t * composition.tempo;
                var endTime = (composition.notes[i].t + composition.notes[i].d) * composition.tempo;
                //console.log(startTime, endTime);
                sources[thisSrcIdx].osc.frequency.setValueAtTime(440 * Math.pow(1.0594630943592953, composition.notes[i].note), startTime); // TODO make table of these values
                sources[thisSrcIdx].gain.gain.setValueAtTime(1, startTime);
                sources[thisSrcIdx].gain.gain.setValueAtTime(0, endTime);
                console.log(startTime, endTime);
            }
            //var gainNode = offlineCtx.createGain();
            //oscillator.connect(gainNode);
            for (var i = 0; i < sources.length; i++) {
                sources[i].gain.connect(offlineCtx.destination);
            }

            offlineCtx.startRendering().then(function(renderedBuffer) {
                console.log('rendered');
                var audioCtx = new AudioContext();
                var song = audioCtx.createBufferSource();
                song.buffer = renderedBuffer;
                song.connect(audioCtx.destination);
                song.onended = function() {
                    audioCtx.close();
                }
                console.log('starting playback');
                song.start();
            });
        }

        var melodyLink = new PointText({
            strokeColor: 'black',
            fontSize: 20,
            content: 'Melodies',
        });
        melodyLink.onClick = function() {
            var c = [];
            var total = 0;
            for (var i = 0; i < composition.notes.length; i++) {
                var melody = composition.notes[i].melody;
                if (melody) {
                    if (! c.hasOwnProperty(melody-1)) {
                        c[melody-1] = [];
                    }

                    c[melody-1].push(i);
                    total++;
                } else {
                    composition.notes[i].melody = null;
                    console.log('nope', i);
                }
            }
            composition.refresh();
            console.log(JSON.stringify(c), total);
        }

        $(window).trigger('resize');

    });

    return { };
});
