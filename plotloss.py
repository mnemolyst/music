import sys
from os import path
import glob
from numpy import zeros, isfinite, floor, ceil, arange, linalg, array, ones
import matplotlib.pyplot as plt
import pickle
caffeRoot = path.join(sys.path[0], '..', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
caffe.set_mode_cpu()

def fitPoly(data, degree=2):
    xi = arange(0, data.shape[0])
    xi2 = array([x*x for x in xi])
    #xi3 = array([x*x*x for x in xi])
    #A = array((xi3, xi2, xi, ones(data.shape[0])))
    A = array((xi2, xi, ones(data.shape[0])))
    lstsq = linalg.lstsq(A.T, data)
    w = lstsq[0]
    #y = w[0]*xi3 + w[1]*xi2 + w[2]*xi + w[3]
    y = w[0]*xi2 + w[1]*xi + w[2]
    return (lstsq, w, xi, y)

if __name__ == '__main__':
    #solverFiles = glob.glob(path.join(sys.path[0], 'caffe', 'random', 'snapshots', '*solverstate'))
    #snapshot = path.join(outDir, 'snapshots', path.basename(m.group(1)) + '-' + m.group(2) + '_iter_100.solverstate')
    #for solverFile in solverFiles:
    #    print solverFile
    inFile = sys.argv[1]
    #idx = int(sys.argv[2])
    with open(inFile) as f:
        e = pickle.loads(f.read())

    if path.basename(inFile) == 'current':
        w = zeros(e.shape[1])
        for i in range(e.shape[1]):
            print fitPoly(e[:,i])[0]
        s = e.sum(1)
        plt.figure(figsize=(24, 8))
        plt.plot(e)
        plt.plot(s)
        plt.show()
    else:
        e.sort(lambda a,b: cmp(sum(a[2][1][3]), sum(b[2][1][3])))
        for t in e:
            print t[0], '\t', t[2][1][3], '\t', sum(t[2][1][3])
