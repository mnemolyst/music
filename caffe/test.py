import sys
import subprocess
from os import path
import glob
import lmdb
import numpy
from numpy import zeros, isfinite, floor, ceil, arange, linalg, array, ones
import pickle
import PIL
caffeRoot = path.join(sys.path[0], '../../caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
caffe.set_mode_gpu()

if len(sys.argv) == 2:
    net = caffe.Net(sys.argv[1], caffe.TEST)
elif len(sys.argv) == 3:
    net = caffe.Net(sys.argv[1], sys.argv[2], caffe.TEST)

net.forward()

transformer = caffe.io.Transformer({'data': net.blobs['Data1'].data.shape})
transformer.set_raw_scale('data', 255)      # rescale from [0, 1] to [0, 255]

for i in range(5):
    print i
    print 'note', net.blobs['Data2'].data[i][0][0][0]
    print 'time', net.blobs['Data3'].data[i][0][0][0]
    print 'duration', net.blobs['Data4'].data[i][0][0][0]
    raw = net.blobs['Data1'].data[i][0]
    image = transformer.preprocess('data', raw)
    img = PIL.Image.fromarray(image.astype(numpy.ubyte), 'L')
    img.save(path.join('test_images', str(i) + '.png'))
