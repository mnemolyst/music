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
caffeRoot = path.join(sys.path[0], '..')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
from caffe import layers as L
from caffe import params as P
caffe.set_mode_cpu()
outDir = path.join(sys.path[0], 'random')
lmdbDir = path.join(sys.path[0], 'lmdb')
nets = []
timePrefix = time.strftime('%Y%b%d-%H:%M')
maxNets = 1
numIter = 10
testInt = 10

paramTemplates = {
    'conv1_num_output': {
        'type': 'int',
        'min': 100,
        'max': 500,
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
    'conv2_num_output': {
        'type': 'int',
        'min': 100,
        'max': 500,
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
    'conv3_num_output': {
        'type': 'int',
        'min': 100,
        'max': 500,
    },
    'conv3_kernel_w': {
        'type': 'int',
        'min': 1,
        'max': 20,
    },
    'conv3_kernel_h': {
        'type': 'int',
        'min': 1,
        'max': 10,
    },
    'conv3_stride_w': {
        'type': 'int',
        'min': 1,
        'max': 5,
    },
    'conv3_stride_h': {
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
    'conv_bias_constant': {
        'type': 'real',
        'min': 0,
        'max': 1,
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
        'max': 500,
    },
    'ip3_time_num_output': {
        'type': 'int',
        'min': 100,
        'max': 500,
    },
    'ip3_duration_num_output': {
        'type': 'int',
        'min': 100,
        'max': 500,
    },
    'ip3_velocity_num_output': {
        'type': 'int',
        'min': 100,
        'max': 500,
    },
    'ip_bias_constant': {
        'type': 'real',
        'min': 0,
        'max': 1,
    },
    # solver params
    'bias_lr_mult': {
        'type': 'real',
        'min': 1,
        'max': 3,
    },
    'base_lr': {
        'type': 'log',
        'min': 0.00001,
        'max': 0.001,
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
    #{
    #    'name': 'velocities',
    #    'type': 'Data',
    #    'args': {
    #        'ntop': 1,
    #        'source': path.join(lmdbDir, '{{phase}}/velocities'),
    #        'batch_size': 20,
    #        'backend': P.Data.LMDB,
    #    },
    #},
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
            'stride_w': 'min({{conv1_stride_w}}, {{conv1_kernel_w}})',
            'stride_h': 'min({{conv1_stride_h}}, {{conv1_kernel_h}})',
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
        'name': 'conv2',
        'type': 'Convolution',
        'bottom': 'relu1',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
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
        'name': 'conv3',
        'type': 'Convolution',
        'bottom': 'relu2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
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
                'value': '{{conv_bias_constant}}',
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
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{ip1_num_output}}',
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
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{ip2_num_output}}',
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
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{ip3_note_num_output}}',
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
        'name': 'ip3_time',
        'type': 'InnerProduct',
        'bottom': 'dropout2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{ip3_time_num_output}}',
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
        'name': 'ip3_duration',
        'type': 'InnerProduct',
        'bottom': 'dropout2',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': '{{ip3_duration_num_output}}',
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
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
    #            {'lr_mult': '{{bias_lr_mult}}'},
    #        ],
    #        'num_output': '{{ip3_velocity_num_output}}',
    #        'weight_filler': {
    #            'type': 'xavier',
    #        },
    #        'bias_filler': {
    #            'type': 'constant',
    #            'value': '{{ip_bias_constant}}',
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
        'bottom': 'relu6_note',
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
        'name': 'ip4_time',
        'type': 'InnerProduct',
        'bottom': 'relu6_time',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': 512,
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
        'name': 'ip4_duration',
        'type': 'InnerProduct',
        'bottom': 'relu6_duration',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': '{{bias_lr_mult}}'},
            ],
            'num_output': 256,
            'weight_filler': {
                'type': 'xavier',
            },
            'bias_filler': {
                'type': 'constant',
                'value': '{{ip_bias_constant}}',
            },
        },
    },
    #{
    #    'name': 'ip4_velocity',
    #    'type': 'InnerProduct',
    #    'bottom': 'relu6_velocity',
    #    'args': {
    #        'param': [
    #            {'lr_mult': 1},
    #            {'lr_mult': '{{bias_lr_mult}}'},
    #        ],
    #        'num_output': 16,
    #        'weight_filler': {
    #            'type': 'xavier',
    #        },
    #        'bias_filler': {
    #            'type': 'constant',
    #            'value': '{{ip_bias_constant}}',
    #        },
    #    },
    #},
    {
        'name': 'loss_note',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip4_note',
            'notes',
        ],
    },
    {
        'name': 'loss_time',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip4_time',
            'times',
        ],
    },
    {
        'name': 'loss_duration',
        'type': 'SoftmaxWithLoss',
        'bottom': [
            'ip4_duration',
            'durations',
        ],
    },
    #{
    #    'name': 'loss_velocity',
    #    'type': 'SoftmaxWithLoss',
    #    'bottom': [
    #        'ip4_velocity',
    #        'velocities',
    #    ],
    #},
    {
        'name': 'accuracy_note',
        'type': 'Accuracy',
        'bottom': [
            'ip4_note',
            'notes',
        ],
        'args': {
            'top_k': 2,
        },
    },
    {
        'name': 'accuracy_time',
        'type': 'Accuracy',
        'bottom': [
            'ip4_time',
            'times',
        ],
        'args': {
            'top_k': 3,
        },
    },
    {
        'name': 'accuracy_duration',
        'type': 'Accuracy',
        'bottom': [
            'ip4_duration',
            'durations',
        ],
        'args': {
            'top_k': 3,
        },
    },
    #{
    #    'name': 'accuracy_velocity',
    #    'type': 'SoftmaxWithLoss',
    #    'bottom': [
    #        'ip4_velocity',
    #        'velocities',
    #    ],
    #},
]

solverTemplate = """
train_net: '{{train_net}}'
test_net: '{{test_net}}'
test_iter: 20
test_interval: 10000
# The base learning rate, momentum and the weight decay of the network.
base_lr: 0.0005
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

def subValues(d, paramValues, phase):
    if type(d) is str:
        while True:
            m = re.search('{{(.*?)}}', d)
            if m:
                if m.group(1).strip() == 'phase':
                    d = d[:m.start()] + phase + d[m.end():]
                else:
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
    return (w, xi, y)

def newSolver(n):
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
            #f.write(str(caffe.to_proto(net.loss_note, net.loss_time, net.loss_duration, net.loss_velocity)))
            f.write(str(caffe.to_proto(net.loss_note, net.loss_time, net.loss_duration, net.accuracy_note, net.accuracy_time, net.accuracy_duration)))
    solverDef = solverTemplate
    solverDef = solverDef.replace('{{train_net}}', path.join(outDir, netFiles['train']))
    solverDef = solverDef.replace('{{test_net}}', path.join(outDir, netFiles['test']))
    solverDef = solverDef.replace('{{snapshot_int}}', str(numIter))
    solverDef = solverDef.replace('{{snapshot_prefix}}', path.join(outDir, 'snapshots', timePrefix + '-' + str(n)))
    solverDef = genSolver(solverDef, paramValues)
    with open(path.join(outDir, solverFile), 'w') as f:
        f.write(solverDef)
    p = subprocess.Popen(['python', 'runSolver.py', '--solver', path.join(outDir, solverFile), '--iter', str(numIter), '--testint', str(testInt)], stdout=subprocess.PIPE)
    out = p.stdout.read()

    try:
        unp = pickle.loads(out)
    except Exception as e:
        unp = array([float('nan'), float('nan'), float('nan')])

    if p.poll() == 0 and isfinite(unp[0].sum()) and isfinite(unp[1].sum()):
        #(w, xi, y) = fitPoly(unp[0].sum(1))
        #staX = w[1] / (-2 * w[0])
        #staY = ((w[0] * staX) + w[1]) * staX + w[2]
        #plt.plot(range(unp[0].sum(1).shape[0]), unp[0].sum(1), xi, y)
        #plt.savefig(path.join(outDir, 'plot', solverFile) + '.loss.png')
        #plt.clf()
        nets.append([solverFile, paramValues, unp])
        with open(path.join(outDir, timePrefix + '-nets'), 'w') as f:
            f.write(pickle.dumps(nets))
    else:
        remove(path.join(outDir, netFiles['train']))
        remove(path.join(outDir, netFiles['test']))
        remove(path.join(outDir, solverFile))

# make new nets
while True:
    if len(nets) < maxNets:
        print len(nets)
        newSolver(len(nets))
    if len(nets) >= maxNets:
        break
