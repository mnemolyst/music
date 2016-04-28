import sys
import re
import random
import subprocess
import shutil
import time
import pickle
import glob
from os import path, remove
from numpy import ones, log10, power, isfinite, array, linalg, arange, concatenate
import matplotlib.pyplot as plt
caffeRoot = path.join(path.expanduser('~'), 'music_project', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
from caffe import layers as L
from caffe import params as P
caffe.set_mode_cpu()
outDir = path.join(sys.path[0], 'random')
lmdbDir = path.join(sys.path[0], 'lmdb')
nets = []
timePrefix = time.strftime('%Y%b%d-%H:%M')
maxNets = 10
numIter = 300
testInt = 10

paramTemplates = {
    'conv1_num_output': {
        'type': 'int',
        'min': 8,
        'max': 64,
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
    # ip1, ip2
    'ip1_num_output': {
        'type': 'int',
        'min': 200,
        'max': 800,
    },
    'ip2_num_output': {
        'type': 'int',
        'min': 200,
        'max': 800,
    },
    # ip3
    'ip3_note_num_output': {
        'type': 'int',
        'min': 100,
        'max': 400,
    },
    # solver params
    'base_lr': {
        'type': 'log',
        'min': 0.001,
        'max': 0.1,
    },
    'lr_momentum': {
        'type': 'real',
        'min': 0.75,
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
paramTemplates['conv2_num_output'] = paramTemplates['conv1_num_output']
paramTemplates['conv2_kernel_w'] =   paramTemplates['conv1_kernel_w']
paramTemplates['conv2_kernel_h'] =   paramTemplates['conv1_kernel_h']
paramTemplates['conv2_stride_w'] =   paramTemplates['conv1_stride_w']
paramTemplates['conv2_stride_h'] =   paramTemplates['conv1_stride_h']
paramTemplates['conv3_num_output'] = paramTemplates['conv1_num_output']
paramTemplates['conv3_kernel_w'] =   paramTemplates['conv1_kernel_w']
paramTemplates['conv3_kernel_h'] =   paramTemplates['conv1_kernel_h']
paramTemplates['conv3_stride_w'] =   paramTemplates['conv1_stride_w']
paramTemplates['conv3_stride_h'] =   paramTemplates['conv1_stride_h']
paramTemplates['ip3_time_num_output'] =     paramTemplates['ip3_note_num_output']
paramTemplates['ip3_duration_num_output'] = paramTemplates['ip3_note_num_output']
paramTemplates['ip3_velocity_num_output'] = paramTemplates['ip3_note_num_output']
paramTemplates['ip4_note_num_output'] =     paramTemplates['ip3_note_num_output']
paramTemplates['ip4_time_num_output'] =     paramTemplates['ip3_note_num_output']
paramTemplates['ip4_duration_num_output'] = paramTemplates['ip3_note_num_output']
paramTemplates['ip4_velocity_num_output'] = paramTemplates['ip3_note_num_output']

layerTemplates = [
    {
        'name': 'images',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': path.join(lmdbDir, 'train/images'),
            'batch_size': 20,
            'backend': P.Data.LMDB,
            'transform_param': {
                'scale': 1./255
            },
            'include': {
                'phase': caffe.TRAIN,
            },
        },
    },
    {
        'name': 'notes',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': path.join(lmdbDir, 'train/notes'),
            'batch_size': 20,
            'backend': P.Data.LMDB,
            'include': {
                'phase': caffe.TRAIN,
            },
        },
    },
    {
        'name': 'times',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': path.join(lmdbDir, 'train/times'),
            'batch_size': 20,
            'backend': P.Data.LMDB,
            'include': {
                'phase': caffe.TRAIN,
            },
        },
    },
    {
        'name': 'durations',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': path.join(lmdbDir, 'train/durations'),
            'batch_size': 20,
            'backend': P.Data.LMDB,
            'include': {
                'phase': caffe.TRAIN,
            },
        },
    },
    #{
    #    'name': 'velocities',
    #    'type': 'Data',
    #    'args': {
    #        'ntop': 1,
    #        'source': path.join(lmdbDir, 'train/velocities'),
    #        'batch_size': 20,
    #        'backend': P.Data.LMDB,
    #        'include': {
    #            'phase': caffe.TRAIN,
    #        },
    #    },
    #},
    {
        'name': 'conv1',
        'type': 'Convolution',
        'bottom': 'images',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{conv1_num_output}}',
            'kernel_w': '{{conv1_kernel_w}}',
            'kernel_h': '{{conv1_kernel_h}}',
            'stride_w': 'min({{conv1_stride_w}}, {{conv1_kernel_w}})',
            'stride_h': 'min({{conv1_stride_h}}, {{conv1_kernel_h}})',
            'weight_filler': {
                'type': 'xavier'
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
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
        'name': 'conv2',
        'type': 'Convolution',
        'bottom': 'relu1',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{conv2_num_output}}',
            'kernel_w': '{{conv2_kernel_w}}',
            'kernel_h': '{{conv2_kernel_h}}',
            'stride_w': 'min({{conv2_stride_w}}, {{conv2_kernel_w}})',
            'stride_h': 'min({{conv2_stride_h}}, {{conv2_kernel_h}})',
            'weight_filler': {
                'type': 'xavier'
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
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
        'name': 'conv3',
        'type': 'Convolution',
        'bottom': 'relu2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{conv3_num_output}}',
            'kernel_w': '{{conv3_kernel_w}}',
            'kernel_h': '{{conv3_kernel_h}}',
            'stride_w': 'min({{conv3_stride_w}}, {{conv3_kernel_w}})',
            'stride_h': 'min({{conv3_stride_h}}, {{conv3_kernel_h}})',
            'weight_filler': {
                'type': 'xavier'
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    {
        'name': 'relu3',
        'type': 'ReLU',
        'bottom': 'conv3',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'pool1',
        'type': 'Pooling',
        'bottom': 'relu3',
        'args': {
            'pool': P.Pooling.MAX,
            'kernel_w': '{{pool1_kernel_w}}',
            'kernel_h': '{{pool1_kernel_h}}',
            'stride_w': 'min({{pool1_stride_w}}, {{pool1_kernel_w}})',
            'stride_h': 'min({{pool1_stride_h}}, {{pool1_kernel_h}})',
        },
    },
    {
        'name': 'ip1',
        'type': 'InnerProduct',
        'bottom': 'pool1',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{ip1_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    {
        'name': 'relu4',
        'type': 'ReLU',
        'bottom': 'ip1',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'dropout1',
        'type': 'Dropout',
        'bottom': 'relu4',
        'args': {
            'dropout_ratio': 0.5,
        },
    },
    {
        'name': 'ip2',
        'type': 'InnerProduct',
        'bottom': 'dropout1',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{ip2_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    {
        'name': 'relu5',
        'type': 'ReLU',
        'bottom': 'ip2',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'dropout2',
        'type': 'Dropout',
        'bottom': 'relu5',
        'args': {
            'dropout_ratio': 0.5,
        },
    },
    {
        'name': 'ip3_note',
        'type': 'InnerProduct',
        'bottom': 'dropout2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{ip3_note_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    {
        'name': 'ip3_time',
        'type': 'InnerProduct',
        'bottom': 'dropout2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{ip3_time_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    {
        'name': 'ip3_duration',
        'type': 'InnerProduct',
        'bottom': 'dropout2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{ip3_duration_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    #{
    #    'name': 'ip3_velocity',
    #    'type': 'InnerProduct',
    #    'bottom': 'dropout2',
    #    'args': {
    #        'param': [
    #            {'lr_mult': 1},
    #            {'lr_mult': 2},
    #        ],
    #        'num_output': '{{ip3_velocity_num_output}}',
    #        'weight_filler': {
    #            'type': 'xavier',
    #        },
    #        'bias_filler': {
    #            'type': 'constant',
    #            'value': 0.2,
    #        },
    #    },
    #},
    {
        'name': 'relu6_note',
        'type': 'ReLU',
        'bottom': 'ip3_note',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu6_time',
        'type': 'ReLU',
        'bottom': 'ip3_time',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu6_duration',
        'type': 'ReLU',
        'bottom': 'ip3_duration',
        'args': {
            'in_place': True,
        },
    },
    #{
    #    'name': 'relu6_velocity',
    #    'type': 'ReLU',
    #    'bottom': 'ip3_velocity',
    #    'args': {
    #        'in_place': True,
    #    },
    #},
    {
        'name': 'ip4_note',
        'type': 'InnerProduct',
        'bottom': 'dropout2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{ip4_note_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    {
        'name': 'ip4_time',
        'type': 'InnerProduct',
        'bottom': 'dropout2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{ip4_time_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    {
        'name': 'ip4_duration',
        'type': 'InnerProduct',
        'bottom': 'dropout2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': '{{ip4_duration_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    #{
    #    'name': 'ip4_velocity',
    #    'type': 'InnerProduct',
    #    'bottom': 'dropout2',
    #    'args': {
    #        'param': [
    #            {'lr_mult': 1},
    #            {'lr_mult': 2},
    #        ],
    #        'num_output': '{{ip4_velocity_num_output}}',
    #        'weight_filler': {
    #            'type': 'xavier',
    #        },
    #        'bias_filler': {
    #            'type': 'constant',
    #            'value': 0.2,
    #        },
    #    },
    #},
    {
        'name': 'relu7_note',
        'type': 'ReLU',
        'bottom': 'ip4_note',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu7_time',
        'type': 'ReLU',
        'bottom': 'ip4_time',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu7_duration',
        'type': 'ReLU',
        'bottom': 'ip4_duration',
        'args': {
            'in_place': True,
        },
    },
    #{
    #    'name': 'relu7_velocity',
    #    'type': 'ReLU',
    #    'bottom': 'ip4_velocity',
    #    'args': {
    #        'in_place': True,
    #    },
    #},
    {
        'name': 'ip5_note',
        'type': 'InnerProduct',
        'bottom': 'relu6_note',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': 128,
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    {
        'name': 'ip5_time',
        'type': 'InnerProduct',
        'bottom': 'relu6_time',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': 256,
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    {
        'name': 'ip5_duration',
        'type': 'InnerProduct',
        'bottom': 'relu6_duration',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': 256,
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2,
            },
        },
    },
    #{
    #    'name': 'ip5_velocity',
    #    'type': 'InnerProduct',
    #    'bottom': 'relu6_velocity',
    #    'args': {
    #        'param': [
    #            {'lr_mult': 1},
    #            {'lr_mult': 2},
    #        ],
    #        'num_output': 16,
    #        'weight_filler': {
    #            'type': 'xavier',
    #        },
    #        'bias_filler': {
    #            'type': 'constant',
    #            'value': 0.2,
    #        },
    #    },
    #},
    {
        'name': 'loss_note',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip5_note',
            'notes',
        ],
    },
    {
        'name': 'loss_time',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip5_time',
            'times',
        ],
    },
    {
        'name': 'loss_duration',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip5_duration',
            'durations',
        ],
    },
    #{
    #    'name': 'loss_velocity',
    #    'type': 'SoftmaxWithLoss',
    #    'bottom': [
    #        'ip5_velocity',
    #        'velocities',
    #    ],
    #},
    {
        'name': 'accuracy_note',
        'type': 'Accuracy',
        'bottom': [
            'ip5_note',
            'notes',
        ],
        'args': {
            'top_k': 2,
            'include': {
                'phase': caffe.TEST,
            },
        },
    },
    {
        'name': 'accuracy_time',
        'type': 'Accuracy',
        'bottom': [
            'ip5_time',
            'times',
        ],
        'args': {
            'top_k': 3,
            'include': {
                'phase': caffe.TEST,
            },
        },
    },
    {
        'name': 'accuracy_duration',
        'type': 'Accuracy',
        'bottom': [
            'ip5_duration',
            'durations',
        ],
        'args': {
            'top_k': 3,
            'include': {
                'phase': caffe.TEST,
            },
        },
    },
    #{
    #    'name': 'accuracy_velocity',
    #    'type': 'SoftmaxWithLoss',
    #    'bottom': [
    #        'ip5_velocity',
    #        'velocities',
    #    ],
    #},
]

solverTemplate = """
train_net: '{{net}}'
test_net: '{{net}}'
test_iter: 1
test_interval: 10000
# The base learning rate, momentum and the weight decay of the network.
base_lr: 0.01
momentum: 0.9
weight_decay: 0.0005
# The learning rate policy
lr_policy: "inv"
gamma: 0.0001
power: 0.75
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

def subValues(d, paramValues):
    if type(d) is str:
        while True:
            m = re.search('{{(.*?)}}', d)
            if m:
                d = d[:m.start()] + str(paramValues[m.group(1).strip()]) + d[m.end():]
            else:
                break
        try:
            return eval(d)
        except (NameError, SyntaxError):
            return d
    elif type(d) is dict:
        ret = {}
        for el in d:
            ret[el] = subValues(d[el], paramValues)
        return ret
    elif type(d) is list:
        return map(lambda x: subValues(x, paramValues), d)
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
    return (w, xi, y)

def newSolver(n):
    global paramTemplates, layerTemplates, solverTemplate, timePrefix, outDir, nets
    netFile = timePrefix + '-train-test-' + str(n) + '.prototxt'
    solverFile = timePrefix + '-solver-' + str(n) + '.prototxt'
    paramValues = genValues(paramTemplates)
    layerDefs = subValues(layerTemplates, paramValues)
    net = genNet(layerDefs)
    with open(path.join(outDir, netFile), 'w') as f:
        testData = str(caffe.to_proto(net.images, net.notes, net.times, net.durations)).replace('train', 'test').replace('TRAIN', 'TEST')
        #f.write(str(caffe.to_proto(net.loss_note, net.loss_time, net.loss_duration, net.loss_velocity)))
        f.write(testData + str(caffe.to_proto(net.loss_note, net.loss_time, net.loss_duration, net.accuracy_note, net.accuracy_time, net.accuracy_duration)))
    solverDef = solverTemplate
    solverDef = solverDef.replace('{{net}}', path.join(outDir, netFile))
    solverDef = solverDef.replace('{{snapshot_int}}', str(numIter))
    solverDef = solverDef.replace('{{snapshot_prefix}}', path.join(outDir, 'snapshots', timePrefix + '-' + str(n)))
    solverDef = genSolver(solverDef, paramValues)
    with open(path.join(outDir, solverFile), 'w') as f:
        f.write(solverDef)
    p = subprocess.Popen(['python', 'runSolver.py', '--solver', path.join(outDir, solverFile), '--iter', str(numIter), '--testint', str(testInt)], stdout=subprocess.PIPE)
    out = p.stdout.read()

    try:
        losses = pickle.loads(out)
    except Exception as e:
        losses = array([float('nan'), float('nan'), float('nan')])

    if p.poll() == 0 and isfinite(losses[0].sum()) and isfinite(losses[1].sum()):
        #(w, xi, y) = fitPoly(losses[0].sum(1))
        #staX = w[1] / (-2 * w[0])
        #staY = ((w[0] * staX) + w[1]) * staX + w[2]
        #plt.plot(range(losses[0].sum(1).shape[0]), losses[0].sum(1), xi, y)
        #plt.savefig(path.join(outDir, 'plot', solverFile) + '.loss.png')
        #plt.clf()
        nets.append({
            'solverFile': solverFile,
            'paramValues': paramValues,
            'trainLoss': losses[0],
            'testLoss': losses[1],
            'accuracy': losses[2],
        })
        with open(path.join(outDir, timePrefix + '-nets'), 'w') as f:
            f.write(pickle.dumps(nets))
    else:
        remove(path.join(outDir, netFile))
        remove(path.join(outDir, solverFile))

netsFile = None
for i in range(len(sys.argv)):
    if sys.argv[i] == '--nets':
        netsFile = sys.argv[i+1]

if netsFile:
    newNets = []
    with open(netsFile) as f:
        nets = pickle.loads(f.read())
    for net in nets:
        print net['solverFile']
        m = re.search('(.*)-solver-(\d+)', net['solverFile'])
        if m:
            snapshots = glob.glob(path.join(path.dirname(netsFile), 'snapshots', m.group(1) + '-' + m.group(2) + '*solverstate'))
            snapshots.sort(key = lambda x: int(x[x.index('_iter_') + 6 : -12]), reverse = True)
            p = subprocess.Popen(['python', 'runSolver.py', '--solver', path.join(path.dirname(netsFile), net['solverFile']), '--snapshot', snapshots[0], '--iter', str(numIter), '--testint', str(testInt)], stdout=subprocess.PIPE)
            out = p.stdout.read()
            try:
                losses = pickle.loads(out)
            except Exception as e:
                losses = array([float('nan'), float('nan'), float('nan')])

            if p.poll() == 0 and isfinite(losses[0].sum()) and isfinite(losses[1].sum()):
                newNets.append({
                    'solverFile': net['solverFile'],
                    'paramValues': net['paramValues'],
                    'trainLoss': concatenate((net['trainLoss'], losses[0])),
                    'testLoss': concatenate((net['testLoss'], losses[1])),
                    'accuracy': concatenate((net['accuracy'], losses[2])),
                })
    with open(netsFile, 'w') as f:
        f.write(pickle.dumps(newNets))

else:
    # make new nets
    while True:
        if len(nets) < maxNets:
            print len(nets)
            newSolver(len(nets))
        if len(nets) >= maxNets:
            break
