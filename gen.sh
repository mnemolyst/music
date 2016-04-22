#!/bin/bash

set -e

for ((i=0; i<10; i=i+1)); do
echo $i;
node boxTest.js;
#node convertmidi.js midi/Bartok/mikro037.mid 1000;
#node convertmidi.js midi/Bartok/mikro040.mid 1000;
#node convertmidi.js midi/Bartok/mikro073.mid 1000;
#node convertmidi.js midi/Bartok/mikro082.mid 1000;
#node convertmidi.js midi/Bartok/mikro083.mid 1000;
#node convertmidi.js midi/Bartok/mikro091.mid 1000;
#node convertmidi.js midi/Bartok/mikro097.mid 1000;
#node convertmidi.js midi/Bartok/mikro101.mid 1000;
#node convertmidi.js midi/Bartok/mikro113.mid 1000;
#node convertmidi.js midi/Bartok/mikro122.mid 1000;
#node convertmidi.js midi/Bartok/mikro123.mid 1000;
#node convertmidi.js midi/Bartok/mikro124.mid 1000;
#node convertmidi.js midi/Bartok/mikro125.mid 1000;
#node convertmidi.js midi/Bartok/mikro126.mid 1000;
#node convertmidi.js midi/Bartok/mikro127.mid 1000;
#node convertmidi.js midi/Bartok/mikro130.mid 1000;
#node convertmidi.js midi/Bartok/mikro131.mid 1000;
#node convertmidi.js midi/Bartok/mikro133.mid 1000;
#node convertmidi.js midi/Bartok/mikro136.mid 1000;
#node convertmidi.js midi/Bartok/mikro140.mid 1000;
#node convertmidi.js midi/Bartok/mikro141.mid 1000;
#node convertmidi.js midi/Bartok/mikro142.mid 1000;
#node convertmidi.js midi/Bartok/mikro143.mid 1000;
#node convertmidi.js midi/Bartok/mikro144.mid 1000;
#node convertmidi.js midi/Bartok/mikro145.mid 1000;
#node convertmidi.js midi/Bartok/mikro146.mid 1000;
#node convertmidi.js midi/Bartok/mikro147.mid 1000;

#node convertmidi.js midi/Bach/bwv772.mid 1000;
#node convertmidi.js midi/Bach/bwv773.mid 1000;
#node convertmidi.js midi/Bach/bwv774.mid 1000;
#node convertmidi.js midi/Bach/bwv775.mid 1000;
#node convertmidi.js midi/Bach/bwv776.mid 1000;
#node convertmidi.js midi/Bach/bwv777.mid 1000;
#node convertmidi.js midi/Bach/bwv778.mid 1000;
#node convertmidi.js midi/Bach/bwv779.mid 1000;
#node convertmidi.js midi/Bach/bwv780.mid 1000;
#node convertmidi.js midi/Bach/bwv781.mid 1000;
#node convertmidi.js midi/Bach/bwv782.mid 1000;
#node convertmidi.js midi/Bach/bwv783.mid 1000;
#node convertmidi.js midi/Bach/bwv784.mid 1000;
#node convertmidi.js midi/Bach/bwv785.mid 1000;
#node convertmidi.js midi/Bach/bwv786.mid 1000;
#node convertmidi.js midi/Bach/bwv787.mid 1000;
#node convertmidi.js midi/Bach/bwv788.mid 1000;
#node convertmidi.js midi/Bach/bwv789.mid 1000;
#node convertmidi.js midi/Bach/bwv790.mid 1000;
#node convertmidi.js midi/Bach/bwv791.mid 1000;
##node convertmidi.js midi/Bach/bwv792.mid 1000;
##node convertmidi.js midi/Bach/bwv793.mid 1000;
##node convertmidi.js midi/Bach/bwv794.mid 1000;
##node convertmidi.js midi/Bach/bwv795.mid 1000;
##node convertmidi.js midi/Bach/bwv796.mid 1000;
##node convertmidi.js midi/Bach/bwv797.mid 1000;
##node convertmidi.js midi/Bach/bwv798.mid 1000;
##node convertmidi.js midi/Bach/bwv799.mid 1000;
##node convertmidi.js midi/Bach/bwv800.mid 1000;
##node convertmidi.js midi/Bach/bwv801.mid 1000;
cd ../caffe/music/lmdb;
./load.sh;
cd ../../../music;
done
