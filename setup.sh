#!/bin/bash
mkdir ../caffe/music
mkdir ../caffe/music/lmdb
mkdir ../caffe/music/lmdb/train
mkdir ../caffe/music/lmdb/train/images
mkdir ../caffe/music/lmdb/train/notes
mkdir ../caffe/music/lmdb/train/times
mkdir ../caffe/music/lmdb/train/durations
mkdir ../caffe/music/lmdb/train/loaded
mkdir ../caffe/music/lmdb/test
mkdir ../caffe/music/lmdb/test/images
mkdir ../caffe/music/lmdb/test/notes
mkdir ../caffe/music/lmdb/test/times
mkdir ../caffe/music/lmdb/test/durations
mkdir ../caffe/music/lmdb/test/loaded
ln -s ../music/caffe/lmdb/clear.sh ../caffe/music/lmdb/
ln -s ../music/caffe/lmdb/load.sh ../caffe/music/lmdb/
