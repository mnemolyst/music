var Png = require('png').Png;
var fs = require('fs');

function cluster(x, med) { // med is array of indices into x
    var c = []; // clusters
    for (var j = 0; j < med.length; j++) {
        c[j] = [];
    }
    for (var i = 0; i < x.length; i++) {
        var minD = null, minJ = 0;
        for (var j = 0; j < med.length; j++) {
            var nd = x[i].n - x[med[j]].n; // note dist
            var td = x[i].t - x[med[j]].t; // time dist
            //var td = (x[i].t + x[i].d * 0.5) - (x[med[j]].t + x[med[j]].d * 0.5); // avg time dist
            var d = nd * nd + td * td;
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
                    var nd = x[c[i][j]].n - x[c[i][k]].n;
                    var td = x[c[i][j]].t - x[c[i][k]].t;
                    sumD += nd * nd + td * td;
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
        med.push(Math.floor(Math.random() * x.length));
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

var x = [];

for (var i = 0; i < 100; i++) {
    var r = Math.random();
    var k = r > 0.75 ? 3 : r > 0.5 ? 2 : r > 0.25 ? 1 : 0;
    x.push({
        n: Math.random() + (k == 0 || k == 1 ? 2 : 0),
        t: Math.random() + (k == 1 || k == 2 ? 2 : 0),
    });
}

var k = 4;
var c = kMed(x, k);

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
