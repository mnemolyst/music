#!/bin/bash
for ((i=0; i<10; i=i+1)); do
echo $i;
node convertmidi.js midi/Bach/bwv772.mid 1000;
node convertmidi.js midi/Bach/bwv773.mid 1000;
node convertmidi.js midi/Bach/bwv774.mid 1000;
node convertmidi.js midi/Bach/bwv775.mid 1000;
node convertmidi.js midi/Bach/bwv776.mid 1000;
node convertmidi.js midi/Bach/bwv777.mid 1000;
node convertmidi.js midi/Bach/bwv778.mid 1000;
node convertmidi.js midi/Bach/bwv779.mid 1000;
node convertmidi.js midi/Bach/bwv780.mid 1000;
node convertmidi.js midi/Bach/bwv781.mid 1000;
node convertmidi.js midi/Bach/bwv782.mid 1000;
node convertmidi.js midi/Bach/bwv783.mid 1000;
node convertmidi.js midi/Bach/bwv784.mid 1000;
node convertmidi.js midi/Bach/bwv785.mid 1000;
node convertmidi.js midi/Bach/bwv786.mid 1000;
node convertmidi.js midi/Bach/bwv787.mid 1000;
node convertmidi.js midi/Bach/bwv788.mid 1000;
node convertmidi.js midi/Bach/bwv789.mid 1000;
node convertmidi.js midi/Bach/bwv790.mid 1000;
node convertmidi.js midi/Bach/bwv791.mid 1000;
#node convertmidi.js midi/Bach/bwv792.mid 1000;
#node convertmidi.js midi/Bach/bwv793.mid 1000;
#node convertmidi.js midi/Bach/bwv794.mid 1000;
#node convertmidi.js midi/Bach/bwv795.mid 1000;
#node convertmidi.js midi/Bach/bwv796.mid 1000;
#node convertmidi.js midi/Bach/bwv797.mid 1000;
#node convertmidi.js midi/Bach/bwv798.mid 1000;
#node convertmidi.js midi/Bach/bwv799.mid 1000;
#node convertmidi.js midi/Bach/bwv800.mid 1000;
#node convertmidi.js midi/Bach/bwv801.mid 1000;
cd ../caffe/music/lmdb;
./load.sh;
cd ../../../music;
done
