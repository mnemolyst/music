import sys
import pickle
import lmdb
from os import path
from numpy import zeros, isfinite, floor, ceil
caffeRoot = path.join(sys.path[0], '..', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
caffe.set_mode_cpu()
lmdbDir = path.join(sys.path[0], 'caffe', 'lmdb')

def runSolver(solver, numIter, testInterval):
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
        if not isfinite(trainLoss[it].sum()):
            raise ArithmeticError
        if it % testInterval == 0:
            solver.test_nets[0].forward()
            idx = int(floor(it / testInterval))
            testLoss[idx] = (
                solver.test_nets[0].blobs['SoftmaxWithLoss1'].data,
                solver.test_nets[0].blobs['SoftmaxWithLoss2'].data,
                solver.test_nets[0].blobs['SoftmaxWithLoss3'].data,
                solver.test_nets[0].blobs['SoftmaxWithLoss4'].data,
            )
            if not isfinite(testLoss[idx].sum()):
                raise ArithmeticError
    return (trainLoss, testLoss)

if __name__ == '__main__':
    solverFile = sys.argv[1]
    numIter = int(sys.argv[2])
    testInterval = int(sys.argv[3])
    for db in ['train/images', 'train/notes', 'train/times', 'train/durations', 'train/velocities', 'test/images', 'test/notes', 'test/times', 'test/durations', 'test/velocities']:
        env = lmdb.open('caffe/lmdb/' + db)
        env.reader_check()
        env.close()
    try:
        solver = caffe.SGDSolver(solverFile)
        (trainLoss, testLoss) = runSolver(solver, numIter, testInterval)
    except Exception as err:
        #sys.stderr.write(err)
        raise err
    else:
        print pickle.dumps((trainLoss, testLoss))
