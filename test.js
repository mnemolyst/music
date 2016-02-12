
    var Note = function(t, d, note, staff) {
        this.t = t; // start time
        this.d = d; // duration
        this.note = note;

        //var noteInfo = staff.noteInfo(this.note);
        //this.path = new Path({
        //    strokeColor: 'blue',
        //    strokeWidth: 5,
        //    segments: [
        //        [upperLeft.x + staff.timeSpacing * (this.t - leftTime),                              upperLeft.y + noteInfo.y],
        //        [upperLeft.x + staff.timeSpacing * (this.t - leftTime) + staff.timeSpacing * this.d, upperLeft.y + noteInfo.y]
        //    ],
        //});
        //this.text = new PointText({
        //    strokeColor: 'black',
        //    fontSize: 14,
        //    content: sfSigns[noteInfo.sf],
        //    point: this.path.lastSegment.point.clone(),
        //});
        //this.group = new Group({
        //    children: [this.path, this.text],
        //    pivot: this.path.firstSegment.point,
        //});
    }
    Note.prototype.update = function(staff) {
        var noteInfo = staff.noteInfo(this.note);
        this.group.position.x = upperLeft.x + staff.timeSpacing * (this.t - leftTime);
        this.group.position.y = upperLeft.y + noteInfo.y;
        this.text.setContent(sfSigns[noteInfo.sf]);
    }

var note = new Note();
console.log(note.[[Prototype]]);
