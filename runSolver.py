import sys
import pickle
from os import path
from numpy import zeros, isfinite, floor, ceil
caffeRoot = path.join(sys.path[0], '..', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
from caffe import layers as L
from caffe import params as P
caffe.set_mode_cpu()
outDir = path.join(sys.path[0], 'caffe', 'random')
lmdbDir = path.join(sys.path[0], 'caffe', 'lmdb')
numNet = 1
numIter = 25
testInterval = 5

def runSolver(solver):
    global numIter, testInterval
    trainLoss = zeros((numIter, 4))
    testLoss = zeros((int(ceil(numIter / testInterval)), 4))
    for it in range(numIter):
        solver.step(1)
        trainLoss[it] = (
            solver.net.blobs['SoftmaxWithLoss1'].data,
            solver.net.blobs['SoftmaxWithLoss2'].data,
            solver.net.blobs['SoftmaxWithLoss3'].data,
            solver.net.blobs['SoftmaxWithLoss4'].data,
        )
        if it % testInterval == 0:
            solver.test_nets[0].forward()
            testLoss[int(floor(it / testInterval))] = (
                solver.test_nets[0].blobs['SoftmaxWithLoss1'].data,
                solver.test_nets[0].blobs['SoftmaxWithLoss2'].data,
                solver.test_nets[0].blobs['SoftmaxWithLoss3'].data,
                solver.test_nets[0].blobs['SoftmaxWithLoss4'].data,
            )
    return (trainLoss, testLoss)

if __name__ == '__main__':
    solverFile = sys.argv[1]
    try:
        solver = caffe.SGDSolver(solverFile)
        (trainLoss, testLoss) = runSolver(solver)
    except Exception as err:
        sys.stderr.write(err)
    else:
        #print trainLoss.sum() / numIter
        if isfinite(trainLoss.sum()) and isfinite(testLoss.sum()):
            print pickle.dumps((trainLoss, testLoss))
        else:
            raise ArithmeticError
