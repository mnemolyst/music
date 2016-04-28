import sys
import pickle
import lmdb
from os import path
from numpy import zeros, isfinite, floor, ceil
caffeRoot = path.join(path.expanduser('~'), 'music_project', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
caffe.set_mode_cpu()
lmdbDir = path.join(sys.path[0], 'lmdb')
losses = ['SoftmaxWithLoss1', 'SoftmaxWithLoss2', 'SoftmaxWithLoss3']#, 'SoftmaxWithLoss4']

def runSolver(solverFile, snapshot, numIter, testInterval, testCount):
    solver = caffe.SGDSolver(solverFile)
    if snapshot:
        solver.restore(snapshot) # FIXME maybe
    trainLoss = zeros((numIter, len(losses)))
    testLoss = zeros((ceil(float(numIter) / testInterval), len(losses)))
    accuracy = zeros((ceil(float(numIter) / testInterval), len(losses)))
    for it in range(numIter):
        solver.step(1)
        trainLoss[it] = [
            solver.net.blobs['SoftmaxWithLoss1'].data,
            solver.net.blobs['SoftmaxWithLoss2'].data,
            solver.net.blobs['SoftmaxWithLoss3'].data,
            #solver.net.blobs['SoftmaxWithLoss4'].data,
        ]
        if not isfinite(trainLoss[it].sum()):
            raise ArithmeticError
        if it == 0 or (it + 1) % testInterval == 0:
            idx = int(floor(it / testInterval))
            testIter = 10#testCount / 20 # TODO don't assume batch size == 20
            for i in range(testIter):
                solver.test_nets[0].forward()
                testLoss[idx] += [
                    solver.test_nets[0].blobs['SoftmaxWithLoss1'].data,
                    solver.test_nets[0].blobs['SoftmaxWithLoss2'].data,
                    solver.test_nets[0].blobs['SoftmaxWithLoss3'].data,
                    #solver.test_nets[0].blobs['SoftmaxWithLoss4'].data,
                ]
                accuracy[idx] += [
                    solver.test_nets[0].blobs['Accuracy1'].data,
                    solver.test_nets[0].blobs['Accuracy2'].data,
                    solver.test_nets[0].blobs['Accuracy3'].data,
                    #solver.test_nets[0].blobs['Accuracy4'].data,
                ]
            testLoss[idx] /= testIter
            accuracy[idx] /= testIter
            if not isfinite(testLoss[idx].sum()):
                raise ArithmeticError
        with open(path.join(sys.path[0], 'random', 'current'), 'w') as f:
            f.write(pickle.dumps([trainLoss, testLoss, accuracy]))
    solver.snapshot()
    return [trainLoss, testLoss, accuracy]

if __name__ == '__main__':
    solverFile = None
    snapshot = None
    numIter = None
    testInterval = None
    for i in range(len(sys.argv)):
        if sys.argv[i] == '--solver':
            solverFile = sys.argv[i+1]
        elif sys.argv[i] == '--snapshot':
            snapshot = sys.argv[i+1]
        elif sys.argv[i] == '--iter':
            numIter = int(sys.argv[i+1])
        elif sys.argv[i] == '--testint':
            testInterval = int(sys.argv[i+1])
    env = lmdb.open('lmdb/test/images')
    testCount = env.stat()['entries']
    env.close()
    for db in ['train/images', 'train/notes', 'train/times', 'train/durations', 'train/velocities', 'test/images', 'test/notes', 'test/times', 'test/durations', 'test/velocities']:
        env = lmdb.open('lmdb/' + db)
        env.reader_check()
        env.close()
    try:
        [trainLoss, testLoss, accuracy] = runSolver(solverFile, snapshot, numIter, testInterval, testCount)
    except Exception as err:
        sys.stderr.write(str(err))
        raise err
    else:
        print pickle.dumps([trainLoss, testLoss, accuracy])
