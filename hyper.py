import sys
import re
import random
import subprocess
import shutil
import time
import pickle
import glob
from os import path, remove
from numpy import zeros, ones, log10, power, isfinite, array, linalg, arange
import matplotlib.pyplot as plt
caffeRoot = path.join(sys.path[0], '..', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
from caffe import layers as L
from caffe import params as P
caffe.set_mode_cpu()
outDir = path.join(sys.path[0], 'caffe', 'random')
lmdbDir = path.join(sys.path[0], 'caffe', 'lmdb')
maxNets = 20

paramTemplates = {
    'conv1_num_output': {
        'type': 'int',
        'min': 5,
        'max': 250,
    },
    'conv1_kernel_w': {
        'type': 'int',
        'min': 1,
        'max': 20,
    },
    'conv1_kernel_h': {
        'type': 'int',
        'min': 1,
        'max': 10,
    },
    'conv1_stride_w': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'conv1_stride_h': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'pool1_kernel_w': {
        'type': 'int',
        'min': 1,
        'max': 10,
    },
    'pool1_kernel_h': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'pool1_stride_w': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'pool1_stride_h': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'conv2_num_output': {
        'type': 'int',
        'min': 5,
        'max': 250,
    },
    'conv2_kernel_w': {
        'type': 'int',
        'min': 1,
        'max': 20,
    },
    'conv2_kernel_h': {
        'type': 'int',
        'min': 1,
        'max': 10,
    },
    'conv2_stride_w': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'conv2_stride_h': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'pool2_kernel_w': {
        'type': 'int',
        'min': 1,
        'max': 10,
    },
    'pool2_kernel_h': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'pool2_stride_w': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'pool2_stride_h': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'conv_bias_constant': {
        'type': 'real',
        'min': 0,
        'max': 1,
    },
    'ip_bias_constant': {
        'type': 'real',
        'min': 0,
        'max': 1,
    },
    'ip1_note_num_output': {
        'type': 'int',
        'min': 10,
        'max': 500,
    },
    'ip1_time_num_output': {
        'type': 'int',
        'min': 10,
        'max': 500,
    },
    'ip1_duration_num_output': {
        'type': 'int',
        'min': 10,
        'max': 500,
    },
    'ip1_velocity_num_output': {
        'type': 'int',
        'min': 10,
        'max': 200,
    },
    'bias_lr_mult': {
        'type': 'real',
        'min': 1,
        'max': 3,
    },
    'base_lr': {
        'type': 'log',
        'min': 0.0001,
        'max': 0.1,
    },
    'lr_momentum': {
        'type': 'real',
        'min': 0.7,
        'max': 0.95,
    },
    'weight_decay': {
        'type': 'log',
        'min': 0.0001,
        'max': 0.005,
    },
    'lr_gamma': {
        'type': 'log',
        'min': 0.00001,
        'max': 0.001,
    },
    'lr_power': {
        'type': 'real',
        'min': 0.25,
        'max': 0.95,
    },
}

layerTemplates = [
    {
        'name': 'images',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': path.join(lmdbDir, '{{phase}}/images'),
            'batch_size': 20,
            'backend': P.Data.LMDB,
            'transform_param': {
                'scale': 1./255
            },
        },
    },
    {
        'name': 'notes',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': path.join(lmdbDir, '{{phase}}/notes'),
            'batch_size': 20,
            'backend': P.Data.LMDB,
        },
    },
    {
        'name': 'times',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': path.join(lmdbDir, '{{phase}}/times'),
            'batch_size': 20,
            'backend': P.Data.LMDB,
        },
    },
    {
        'name': 'durations',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': path.join(lmdbDir, '{{phase}}/durations'),
            'batch_size': 20,
            'backend': P.Data.LMDB,
        },
    },
    {
        'name': 'velocities',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': path.join(lmdbDir, '{{phase}}/velocities'),
            'batch_size': 20,
            'backend': P.Data.LMDB,
        },
    },
    {
        'name': 'conv1',
        'type': 'Convolution',
        'bottom': 'images',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{conv1_num_output}}',
            'kernel_w': '{{conv1_kernel_w}}',
            'kernel_h': '{{conv1_kernel_h}}',
            'stride_w': '{{conv1_stride_w}}',
            'stride_h': '{{conv1_stride_h}}',
            'weight_filler': {
                'type': 'xavier'
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{conv_bias_constant}}',
            },
        },
    },
    {
        'name': 'relu1',
        'type': 'ReLU',
        'bottom': 'conv1',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'pool1',
        'type': 'Pooling',
        'bottom': 'relu1',
        'args': {
            'pool': P.Pooling.MAX,
            'kernel_w': '{{pool1_kernel_w}}',
            'kernel_h': '{{pool1_kernel_h}}',
            'stride_w': '{{pool1_stride_w}}',
            'stride_h': '{{pool1_stride_h}}',
        },
    },
    {
        'name': 'conv2',
        'type': 'Convolution',
        'bottom': 'pool1',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{conv2_num_output}}',
            'kernel_w': '{{conv2_kernel_w}}',
            'kernel_h': '{{conv2_kernel_h}}',
            'stride_w': '{{conv2_stride_w}}',
            'stride_h': '{{conv2_stride_h}}',
            'weight_filler': {
                'type': 'xavier'
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{conv_bias_constant}}',
            },
        },
    },
    {
        'name': 'relu2',
        'type': 'ReLU',
        'bottom': 'conv2',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'pool2',
        'type': 'Pooling',
        'bottom': 'relu2',
        'args': {
            'pool': P.Pooling.MAX,
            'kernel_w': '{{pool2_kernel_w}}',
            'kernel_h': '{{pool2_kernel_h}}',
            'stride_w': '{{pool2_stride_w}}',
            'stride_h': '{{pool2_stride_h}}',
        },
    },
    {
        'name': 'ip1_note',
        'type': 'InnerProduct',
        'bottom': 'pool2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{ip1_note_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
            },
        },
    },
    {
        'name': 'ip1_time',
        'type': 'InnerProduct',
        'bottom': 'pool2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{ip1_time_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
            },
        },
    },
    {
        'name': 'ip1_duration',
        'type': 'InnerProduct',
        'bottom': 'pool2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{ip1_duration_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
            },
        },
    },
    {
        'name': 'ip1_velocity',
        'type': 'InnerProduct',
        'bottom': 'pool2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{ip1_velocity_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
            },
        },
    },
    {
        'name': 'relu5',
        'type': 'ReLU',
        'bottom': 'ip1_note',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu6',
        'type': 'ReLU',
        'bottom': 'ip1_time',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu7',
        'type': 'ReLU',
        'bottom': 'ip1_duration',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu8',
        'type': 'ReLU',
        'bottom': 'ip1_velocity',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'ip2_note',
        'type': 'InnerProduct',
        'bottom': 'relu5',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': 128,
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
            },
        },
    },
    {
        'name': 'ip2_time',
        'type': 'InnerProduct',
        'bottom': 'relu6',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': 64,
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
            },
        },
    },
    {
        'name': 'ip2_duration',
        'type': 'InnerProduct',
        'bottom': 'relu7',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': 64,
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
            },
        },
    },
    {
        'name': 'ip2_velocity',
        'type': 'InnerProduct',
        'bottom': 'relu8',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': 16,
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
            },
        },
    },
    {
        'name': 'loss_note',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip2_note',
            'notes',
        ],
    },
    {
        'name': 'loss_time',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip2_time',
            'times',
        ],
    },
    {
        'name': 'loss_duration',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip2_duration',
            'durations',
        ],
    },
    {
        'name': 'loss_velocity',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip2_velocity',
            'velocities',
        ],
    },
]

solverTemplate = """
train_net: '{{train_net}}'
test_net: '{{test_net}}'
test_iter: 1
test_interval: 10000
# The base learning rate, momentum and the weight decay of the network.
base_lr: {{base_lr}}
momentum: {{lr_momentum}}
weight_decay: {{weight_decay}}
# The learning rate policy
lr_policy: "inv"
gamma: {{lr_gamma}}
power: {{lr_power}}
# Display every 100 iterations
#display: 100
# The maximum number of iterations
#max_iter: 10000
# snapshot intermediate results
snapshot: {{snapshot_int}}
snapshot_prefix: "{{snapshot_prefix}}"
#solver mode: CPU or GPU
solver_mode: CPU
"""

def genValues(paramTemplates):
    values = {}
    for k, v in paramTemplates.iteritems():
        if v['type'] == 'real':
            value = float(v['min']) + random.random() * (float(v['max']) - float(v['min']))
        elif v['type'] == 'log':
            lMin = log10(float(v['min']))
            lMax = log10(float(v['max']))
            value = power(10, lMin + random.random() * (lMax - lMin))
        elif v['type'] == 'int':
            if v.has_key('step'):
                step = int(v['step'])
            else:
                step = 1
            n = (int(v['max']) - int(v['min'])) / step
            c = random.randint(0, n)
            value = int(v['min']) + c * step
        else:
            value = None
        values[k] = value
    return values

def subValues(d, paramValues, phase):
    if type(d) is str:
        m = re.search('{{(.*)}}', d)
        if m:
            if m.group(1).strip() == 'phase':
                return d[:m.start()] + phase + d[m.end():]
            else:
                return paramValues[m.group(1).strip()]
        else:
            return d
    elif type(d) is dict:
        ret = {}
        for el in d:
            ret[el] = subValues(d[el], paramValues, phase)
        return ret
    elif type(d) is list:
        return map(lambda x: subValues(x, paramValues, phase), d)
    else:
        return d

def genNet(layerDefs):
    net = caffe.NetSpec()
    for l in layerDefs:
        if l.has_key('args'):
            args = l['args']
        else:
            args = {}

        if l.has_key('bottom'):
            if type(l['bottom']) is list:
                bottoms = map(lambda x: getattr(net, x), l['bottom'])
                layer = getattr(L, l['type'])(*bottoms, **args)
            else:
                layer = getattr(L, l['type'])(getattr(net, l['bottom']), **args)
        else:
            layer = getattr(L, l['type'])(**args)
        net.__dict__.update({l['name']: layer})
    return net

def genSolver(solverTemplate, paramValues):
    def subValue(m):
        return str(paramValues[m.group(1).strip()])
    return re.sub('{{(.*?)}}', subValue, solverTemplate)

def fitPoly(data, degree=2):
    xi = arange(0, data.shape[0])
    xi2 = array([x*x for x in xi])
    #xi3 = array([x*x*x for x in xi])
    #A = array((xi3, xi2, xi, ones(data.shape[0])))
    A = array((xi2, xi, ones(data.shape[0])))
    w = linalg.lstsq(A.T, data)[0]
    #y = w[0]*xi3 + w[1]*xi2 + w[2]*xi + w[3]
    y = w[0]*xi2 + w[1]*xi + w[2]
    return (xi, y, w)

def runSolver(n):
    global paramTemplates, layerTemplates, solverTemplate, timePrefix, outDir, nets
    netFiles = {
        'train': timePrefix + '-train-' + str(n) + '.prototxt',
        'test': timePrefix + '-test-' + str(n) + '.prototxt',
    }
    solverFile = timePrefix + '-solver-' + str(n) + '.prototxt'
    paramValues = genValues(paramTemplates)
    for phase in ['train', 'test']:
        layerDefs = subValues(layerTemplates, paramValues, phase)
        net = genNet(layerDefs)
        with open(path.join(outDir, netFiles[phase]), 'w') as f:
            f.write(str(caffe.to_proto(net.loss_note, net.loss_time, net.loss_duration, net.loss_velocity)))
    solverDef = solverTemplate
    solverDef = solverDef.replace('{{train_net}}', path.join(outDir, netFiles['train']))
    solverDef = solverDef.replace('{{test_net}}', path.join(outDir, netFiles['test']))
    solverDef = solverDef.replace('{{snapshot_int}}', '100')
    solverDef = solverDef.replace('{{snapshot_prefix}}', path.join(outDir, 'snapshots', timePrefix + '-' + str(n)))
    solverDef = genSolver(solverDef, paramValues)
    with open(path.join(outDir, solverFile), 'w') as f:
        f.write(solverDef)
    p = subprocess.Popen(['python', 'runSolver.py', path.join(outDir, solverFile), '100', '10'], stdout=subprocess.PIPE)
    out = p.stdout.read()

    try:
        unp = pickle.loads(out)
    except Exception as e:
        unp = array((float('nan'), float('nan')))

    if p.poll() == 0 and isfinite(unp[0].sum()) and isfinite(unp[1].sum()):
        print unp[1]
        (xi, y, w) = fitPoly(unp[1].sum(1))
        staX = w[1] / (-2 * w[0])
        staY = ((w[0] * staX) + w[1]) * staX + w[2]
        plt.plot(xi, unp[1].sum(1), xi, y)
        plt.savefig(path.join(outDir, 'plot', solverFile) + '.loss.png')
        plt.clf()
        nets.append((solverFile, w, y, staX, staY))
        with open(path.join(outDir, timePrefix + '-nets'), 'w') as f:
            f.write(pickle.dumps(nets))
        shutil.move(path.join(outDir, netFiles['train']), path.join(outDir, 'good', netFiles['train']))
        shutil.move(path.join(outDir, netFiles['test']), path.join(outDir, 'good', netFiles['test']))
        shutil.move(path.join(outDir, solverFile), path.join(outDir, 'good', solverFile))
    else:
        #shutil.move(path.join(outDir, netFiles['train']), path.join(outDir, 'nogood', netFiles['train']))
        #shutil.move(path.join(outDir, netFiles['test']), path.join(outDir, 'nogood', netFiles['test']))
        #shutil.move(path.join(outDir, solverFile), path.join(outDir, 'nogood', solverFile))
        remove(path.join(outDir, netFiles['train']))
        remove(path.join(outDir, netFiles['test']))
        remove(path.join(outDir, solverFile))

nets = []
timePrefix = time.strftime('%Y%b%d-%H:%M')
#trainFiles = glob.glob(path.join(outDir, 'good', '*train*'))
#testFiles = glob.glob(path.join(outDir, 'good', '*test*'))
#for pair in zip(trainFiles, testFiles):
#    trainM = re.match('(.*?)-train-(\d+).prototxt', pair[0])
#    testM = re.match('(.*?)-test-(\d+).prototxt', pair[1])
#    trainNet = caffe.Net(pair[0], path.join(outDir, 'snapshots', path.basename(trainM.group(1)) + '-' + trainM.group(2) + '_iter_25.caffemodel'), caffe.TRAIN)
#    testNet = caffe.Net(pair[1], path.join(outDir, 'snapshots', path.basename(testM.group(1)) + '-' + testM.group(2) + '_iter_25.caffemodel'), caffe.TEST)
#    testNet.forward(start = 'Convolution1')
#    print dir(trainNet)
#    print testNet.blobs['SoftmaxWithLoss1'].data
#    print testNet.blobs['SoftmaxWithLoss2'].data
#    print testNet.blobs['SoftmaxWithLoss3'].data
#    print testNet.blobs['SoftmaxWithLoss4'].data
#    for i in range(25):
#        trainNet.step(1)
#    testNet.forward('Convolution1')
#    print testNet.blobs['SoftmaxWithLoss1'].data
#    print testNet.blobs['SoftmaxWithLoss2'].data
#    print testNet.blobs['SoftmaxWithLoss3'].data
#    print testNet.blobs['SoftmaxWithLoss4'].data
#    break
solverFiles = glob.glob(path.join(outDir, 'good', '*solver*'))
for solverFile in solverFiles:
    m = re.match('(.*?)-solver-(\d+).prototxt', solverFile)
    snapshot = path.join(outDir, 'snapshots', path.basename(m.group(1)) + '-' + m.group(2) + '_iter_100.solverstate')
    solver = caffe.SGDSolver(solverFile)
    print dir(solver)
    solver.restore(snapshot)
    solver.step(100)
    break
#while True:
#    if len(nets) < maxNets:
#        print len(nets)
#        runSolver(len(nets))
#    if len(nets) >= maxNets:
#        break

#nets.sort(lambda a, b: cmp(a[1], b[1]))
