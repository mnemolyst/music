import sys
import re
from os import path
caffe_root = path.join(sys.path[0], '..', 'caffe')
sys.path.insert(1, path.join(caffe_root, 'python'))
import caffe
caffe.set_mode_cpu()
model_def = path.join(sys.path[0], 'caffe', 'train_test.template')
model_weights = path.join(sys.path[0], 'caffe', 'snapshots', '_iter_6509.caffemodel')

file = open(model_def, 'r')
template = file.read()
file.close()

pIter1 = re.finditer('%{(.*?)}%', template, re.S)
for i1 in pIter1:
    pIter2 = re.finditer('(\S+)\s*=\s*(\S+)', i1.group())
    for i2 in pIter2:
        print i2.group(1)
        print i2.group(2)

#net = caffe.Net(model_def, model_weights, caffe.TEST)
#net = caffe.Net(model_def, model_weights, caffe.TEST)
