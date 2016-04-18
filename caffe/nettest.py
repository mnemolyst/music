import sys
import re
import math
import random
from os import path
caffeRoot = path.join(sys.path[0], '..')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
caffe.set_mode_cpu()
from caffe import layers as L
from caffe import params as P

