import sys
import subprocess
from os import path
import glob
import lmdb
from numpy import zeros, isfinite, floor, ceil, arange, linalg, array, ones
import pickle
caffeRoot = path.join(sys.path[0], '..', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
caffe.set_mode_cpu()

#prototxt.push('channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.note) + '"');

prototxt = 'channels: 1\nheight: 1\nwidth: 1\ndata: "' + String(trainPoint.note) + '"'

#var child = childProcess.spawn(
#    '/usr/local/bin/protoc',
#    ['--encode=caffe.Datum', 'caffe.proto'],
#    { cwd: path.join(__dirname, '../caffe/src/caffe/proto') }
#);

p = subprocess.Popen(['/usr/local/bin/protoc', '--encode=caffe.Datum', 'caffe.proto'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
