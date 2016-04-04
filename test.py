import sys
import subprocess
from os import path
import glob
import lmdb
from numpy import zeros, isfinite, floor, ceil, arange, linalg, array, ones
import pickle
caffeRoot = path.join(sys.path[0], '..')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
caffe.set_mode_cpu()

netFile = sys.argv[1]
net = caffe.Net(netFile, caffe.TRAIN)
net.forward()
print net.blobs['Data1'].data
