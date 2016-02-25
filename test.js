function dist(a, b, notes) {
    var nd = notes[a].n - notes[b].n;
    var td = notes[a].t - notes[b].t;
    return Math.abs(10000 * nd * nd * nd) + td * td;
}

function shuffleArray(array) {
    array = array.slice();
    for (var i = array.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
    return array;
}

function cluster(x, med) { // med is array of indices into x
    var c = []; // clusters
    for (var j = 0; j < med.length; j++) {
        c[j] = [];
    }
    for (var i = 0; i < x.length; i++) {
        var minD = null, minJ = 0;
        for (var j = 0; j < med.length; j++) {
            var d = dist(i, med[j], x);
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
                    sumD += dist(c[i][j], c[i][k], x);
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

function kMed(x, k, cSeeds) {
    if (cSeeds) {
        var med = cSeeds;
    } else {
        var xi = []
        for (var i = 0; i < x.length; i++) {
            xi.push(i);
        }
        var med = shuffleArray(xi).slice(0, k);
    }
    var c, oldMed;

    do {
        c = cluster(x, med);
        oldMed = med;
        med = findMed(x, c);
        if (cSeeds) {
            for (var i = 0; i < c.length; i++) {
                if (c[i].indexOf(cSeeds[i]) === -1) {
                    med = cSeeds; // reset
                    continue;
                }
            }
        }
    } while (diffMed(oldMed, med));

    return c;
}

var a = [
{n:1, t:1},
{n:2, t:1},
{n:1, t:2},
{n:2, t:2},
{n:11, t:1},
{n:12, t:1},
{n:11, t:2},
{n:12, t:2},
{n:1, t:11},
{n:2, t:11},
{n:1, t:12},
{n:2, t:12},
{n:11, t:11},
{n:12, t:11},
{n:11, t:12},
{n:12, t:12},
];

var c = kMed(a, 4, [0, 4, 12, 8]);
console.log(c);
