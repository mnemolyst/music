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

