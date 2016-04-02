var yes = 0;
for (i = 0; i < 100000; i++) yes += Math.random() < 1/3;
console.log(yes);
