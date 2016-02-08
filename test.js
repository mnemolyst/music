//var s = 1 / Math.pow(2, 1/12);
//console.log(s);
//console.log(880 / Math.pow(s, 24));
no = [-12, -10, -9, -7, -5, -4, -2, 0, 2, 3, 5, 7, 8, 10, 12];
note = -21;
for (var i = 0, mn = note % 12; mn > no[i]; i++);
console.log(mn);
console.log(i);
