import sys
import subprocess
from os import path
import glob
import lmdb
import numpy as np
from numpy import zeros, isfinite, floor, ceil, arange, linalg, array, ones
import matplotlib.pyplot as plt
import pickle
import PIL
caffeRoot = path.join(path.expanduser('~'), 'music_project', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
caffe.set_mode_cpu()

if len(sys.argv) == 2:
    net = caffe.Net(sys.argv[1], caffe.TRAIN)
elif len(sys.argv) == 3:
    net = caffe.Net(sys.argv[1], sys.argv[2], caffe.TRAIN)

net.forward()

transformer = caffe.io.Transformer({'data': net.blobs['Images'].data.shape})
transformer.set_raw_scale('data', 255)      # rescale from [0, 1] to [0, 255]

def vis_square(data):
    """Take an array of shape (n, height, width) or (n, height, width, 3)
       and visualize each (height, width) thing in a grid of size approx. sqrt(n) by sqrt(n)"""

    # normalize data for display
    print '1', data.shape
    data = (data - data.min()) / (data.max() - data.min())

    print '2', data.shape
    # force the number of filters to be square
    n = int(np.ceil(np.sqrt(data.shape[0])))
    #padding = (((0, n * n - data.shape[0]),
    #           (0, 1), (0, 1))                 # add some space between filters
    #           + ((0, 0),) * (data.ndim - 3))  # don't pad the last dimension (if there is one)
    #data = np.pad(data, padding, mode='constant', constant_values=1)  # pad with ones (white)

    print '3', data.shape
    # tile the filters into an image
    print 'reshape', ((n, n) + data.shape[1:])
    print 'transpose', ((0, 2, 1, 3) + tuple(range(4, data.ndim + 1)))
    #data = data.reshape((n, n) + data.shape[1:-1]).transpose((0, 2, 1, 3))
    data = data.reshape((n, n) + data.shape[1:]).transpose((0, 2, 1, 3) + tuple(range(4, data.ndim + 1)))
    print '4', data.shape
    print 'reshape', ((n * data.shape[1], n * data.shape[3]) + data.shape[4:])
    data = data.reshape((n * data.shape[1], n * data.shape[3]) + data.shape[4:])

    print '5', data.shape
    #plt.imsave('images/test.png', data)
    plt.imshow(data); plt.axis('off')
    plt.show()
    #return PIL.Image.fromarray(data.astype(np.ubyte), 'L')

def dump(i):
    #print 'note', net.blobs['Notes'].data[i][0][0][0]
    #print 'time', net.blobs['Times'].data[i][0][0][0]
    #print 'duration', net.blobs['Durations'].data[i][0][0][0]
    #raw = net.blobs['Images'].data[i][0]
    #image = transformer.preprocess('data', raw)
    #img = PIL.Image.fromarray(image.astype(np.ubyte), 'L')
    #img.save(path.join('test', str(i) + '.png'))

    #print dir(net.params['Convolution2'][0])
    #print net.params['Convolution2'][0].num
    #print net.params['Convolution2'][0].channels
    #print net.params['Convolution2'][0].height
    #print net.params['Convolution2'][0].width
    filters = net.params['Convolution2'][0].data
    vis_square(filters)
    #img = vis_square(filters.transpose(0, 2, 3, 1))
    #img.save(path.join('test', str(i) + '.png'))

dump(0)
