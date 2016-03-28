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

def runSolver(solverFile, numIter, testInterval, testCount):
    solver = caffe.SGDSolver(solverFile)
    trainLoss = zeros((numIter, 4))
    testLoss = zeros((ceil(float(numIter) / testInterval), 4))
    for it in range(numIter):
        solver.step(1)
        trainLoss[it] = (
            solver.net.blobs['SoftmaxWithLoss1'].data,
            solver.net.blobs['SoftmaxWithLoss2'].data,
            solver.net.blobs['SoftmaxWithLoss3'].data,
            solver.net.blobs['SoftmaxWithLoss4'].data,
        )
        with open(path.join(sys.path[0], 'caffe', 'random', 'current'), 'w') as f:
            f.write(pickle.dumps(trainLoss))
        if not isfinite(trainLoss[it].sum()):
            raise ArithmeticError
        if it % testInterval == 0:
            idx = int(floor(it / testInterval))
            testIter = 10#testCount / 20 # TODO don't assume batch size == 20
            for i in range(testIter):
                solver.test_nets[0].forward()
                testLoss[idx] += (
                    solver.test_nets[0].blobs['SoftmaxWithLoss1'].data,
                    solver.test_nets[0].blobs['SoftmaxWithLoss2'].data,
                    solver.test_nets[0].blobs['SoftmaxWithLoss3'].data,
                    solver.test_nets[0].blobs['SoftmaxWithLoss4'].data,
                )
            testLoss[idx] /= testIter
            if not isfinite(testLoss[idx].sum()):
                raise ArithmeticError
    return (trainLoss, testLoss)

if __name__ == '__main__':
    solverFile = sys.argv[1]
    numIter = int(sys.argv[2])
    testInterval = int(sys.argv[3])
    env = lmdb.open('caffe/lmdb/test/images')
    testCount = env.stat()['entries']
    env.close()
    for db in ['train/images', 'train/notes', 'train/times', 'train/durations', 'train/velocities', 'test/images', 'test/notes', 'test/times', 'test/durations', 'test/velocities']:
        env = lmdb.open('caffe/lmdb/' + db)
        env.reader_check()
        env.close()
    try:
        (trainLoss, testLoss) = runSolver(solverFile, numIter, testInterval, testCount)
    except Exception as err:
        sys.stderr.write(str(err))
        raise err
    else:
        print pickle.dumps((trainLoss, testLoss))
