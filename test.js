var Png = require('png').Png;
var fs = require('fs');

function dist(a, b) {
    var nd = a.n - b.n;
    var td = a.t - b.t;
    return nd * nd + td * td;
}

function cluster(x, med) { // med is array of indices into x
    var c = []; // clusters
    for (var j = 0; j < med.length; j++) {
        c[j] = [];
    }
    for (var i = 0; i < x.length; i++) {
        var minD = null, minJ = 0;
        for (var j = 0; j < med.length; j++) {
            var d = dist(x[i], x[med[j]]);
            if (minD === null || d < minD) {
                minD = d;
                minJ = j; // index into med
            }
        }
        c[minJ].push(i) // put index into x in cluster minJ
    }
    return c;
}

function findMed(x, c) { // c in array of arrays of indices into x
    var med = [];
    for (var i = 0; i < c.length; i++) { // for each cluster...
        var minD = null, minJ = 0;
        for (var j = 0; j < c[i].length; j++) { // for each potential medioid...
            var sumD = 0;
            for (var k = 0; k < c[i].length; k++) { // sum the distances to all other points
                if (j !== k) {
                    sumD += dist(x[c[i][j]], x[c[i][k]]);
                }
            }
            if (minD === null || sumD < minD) {
                minD = sumD;
                minJ = j; // c[i][j] is the best medioid so far for cluster i
            }
        }
        med[i] = c[i][minJ];
    }
    return med;
}

function diffMed(med1, med2) {
    if (med1.length !== med2.length) {
        return true;
    }
    for (var i = 0; i < med1.length; i++) {
        if (med1[i] !== med2[i]) {
            return true;
        }
    }
    return false;
}

function kMed(x, k) {
    var med = [], newMed, c;
    for (var i = 0; i < k; i++) {
        var ri = Math.floor(Math.random() * x.length);
        while (med.indexOf(ri) !== -1) {
            ri = Math.floor(Math.random() * x.length);
        }
        med.push(ri);
    }

    var keepGoing = true;
    while (keepGoing) {
        c = cluster(x, med);
        newMed = findMed(x, c);
        if (diffMed(med, newMed)) {
            med = newMed;
        } else {
            keepGoing = false;
        }
    }

    return c;
}

function minSilhouette(x, c) {
    var min = 1;
    for (var i = 0; i < x.length; i++) {
        var thisAvg, minOtherAvg = null;
        for (var j = 0; j < c.length; j++) {
            var sumD = 0;
            var isInThis = false;
            for (var k = 0; k < c[j].length; k++) {
                if (i === c[j][k]) {
                    isInThis = true;
                } else {
                    sumD += dist(x[i], x[c[j][k]]);
                }
            }
            var avgD = sumD / k;
            if (isInThis) {
                thisAvg = avgD;
            } else if (minOtherAvg === null || avgD < minOtherAvg) {
                minOtherAvg = avgD;
            }
        }
        var s = (minOtherAvg - thisAvg)/Math.max(thisAvg, minOtherAvg);
        if (s < min) {
            min = s;
        }
    }
    return min;
}

var x = [];

for (var i = 0; i < 100; i++) {
    var r = Math.random();
    var k = r > 0.75 ? 3 : r > 0.5 ? 2 : r > 0.25 ? 1 : 0;
    x.push({
        n: Math.random() + (k == 0 || k == 1 ? 1 : 0),
        t: Math.random() + (k == 1 || k == 2 ? 1 : 0),
    });
}

var k = 4;
var c = kMed(x, k);
while (minSilhouette(x, c) < 0) {
    console.log(minSilhouette(x, c));
    c = kMed(x, k);
}

var imageBuf = new Buffer(100 * 100);
imageBuf.fill(0);
for (var i = 0; i < c.length; i++) {
    for (var j = 0; j < c[i].length; j++) {
        imageBuf[100 * Math.floor(x[c[i][j]].t * 100 / 3) + Math.floor(x[c[i][j]].n * 100 / 3)] = Math.floor(0xff * (i + 1) / k);
    }
}
var png = new Png(imageBuf, 100, 100, 'gray', 8);
png.encode(function(image) {
    fs.writeFileSync('test.png', image);
});
