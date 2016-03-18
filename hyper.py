import sys
import re
import math
import random
from os import path
caffeRoot = path.join(sys.path[0], '..', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
from caffe import layers as L
from caffe import params as P
caffe.set_mode_cpu()
templateFile = path.join(sys.path[0], 'caffe', 'train_test.template')
outDir = path.join(sys.path[0], 'caffe', 'random')
snapshot = path.join(sys.path[0], 'caffe', 'snapshots', '_iter_6509.caffemodel')
maxIter = 10

paramTemplates = {
    'batch_size': {
        'type': 'int',
        'min': 1,
        'max': 50,
    },
    'conv1_num_output': {
        'type': 'int',
        'min': 5,
        'max': 250,
    },
    'conv1_kernel_w': {
    },
    'conv1_kernel_h': {
    },
    'conv1_stride_w': {
    },
    'conv1_stride_h': {
    },
    'pool1_kernel_w': {
    },
    'pool1_kernel_h': {
    },
    'pool1_stride_w': {
    },
    'pool1_stride_h': {
    },
    'conv2_num_output': {
        'type': 'int',
        'min': 5,
        'max': 250,
    },
    'conv2_kernel_w': {
    },
    'conv2_kernel_h': {
    },
    'conv2_stride_w': {
    },
    'conv2_stride_h': {
    },
    'pool2_kernel_w': {
    },
    'pool2_kernel_h': {
    },
    'pool2_stride_w': {
    },
    'pool2_stride_h': {
    },
    'conv_bias_constant': {
    },
    'ip_bias_constant': {
    },
    'ip1_note_num_output': {
    },
    'ip1_time_num_output': {
    },
    'ip1_duration_num_output': {
    },
    'ip1_velocity_num_output': {
    },
    'bias_lr_mult': {
        #2
    },
}

layerTemplates = [
    {
        'name': 'images',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': 'music/lmdb/train/images',
            'batch_size': '{{batch_size}}',
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
            'source': 'music/lmdb/train/notes',
            'batch_size': '{{batch_size}}',
            'backend': P.Data.LMDB,
        },
    },
    {
        'name': 'times',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': 'music/lmdb/train/times',
            'batch_size': '{{batch_size}}',
            'backend': P.Data.LMDB,
        },
    },
    {
        'name': 'durations',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': 'music/lmdb/train/durations',
            'batch_size': '{{batch_size}}',
            'backend': P.Data.LMDB,
        },
    },
    {
        'name': 'velocities',
        'type': 'Data',
        'args': {
            'ntop': 1,
            'source': 'music/lmdb/train/velocities',
            'batch_size': '{{batch_size}}',
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
        'name': 'pool1',
        'type': 'Pooling',
        'bottom': 'conv1',
        'args': {
            'pool': 'MAX',
            'kernel_w': '{{pool1_kernel_w}}',
            'kernel_h': '{{pool1_kernel_h}}',
            'stride_w': '{{pool1_stride_w}}',
            'stride_h': '{{pool1_stride_h}}',
        },
    },
    {
        'name': 'conv2',
        'type': 'Convolution',
        'bottom': 'images',
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
        'name': 'pool2',
        'type': 'Pooling',
        'bottom': 'conv2',
        'args': {
            'pool': 'MAX',
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
        'name': 'relu1',
        'type': 'ReLU',
        'bottom': 'ip1_note',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu2',
        'type': 'ReLU',
        'bottom': 'ip1_time',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu3',
        'type': 'ReLU',
        'bottom': 'ip1_duration',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'relu4',
        'type': 'ReLU',
        'bottom': 'ip1_velocity',
        'args': {
            'in_place': True,
        },
    },
    {
        'name': 'ip2_note',
        'type': 'InnerProduct',
        'bottom': 'ip1_note',
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
        'bottom': 'ip1_time',
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
        'bottom': 'ip1_duration',
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
        'bottom': 'ip1_velocity',
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

def genValues(paramTemplates):
    values = {}
    for k, v in paramTemplates.iteritems():
        if v['type'] == 'real':
            value = float(v['min']) + random.random() * (float(v['max']) - float(v['min']))
        elif v['type'] == 'log':
            value = math.pow(10, float(v['min']) + random.random() * (float(v['max']) - float(v['min'])))
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
    ret = {}
    for el in d:
        value = d[el]
        if type(d[el]) is dict:
            value = subValues(d[el], paramValues)
        elif type(d[el]) is str:
            m = re.search('{{(.*)}}', d[el])
            if m:
                value = paramValues[m.group(1).strip()]
        ret[el] = (value)
    return ret

def genNet(layerDefs):
    net = caffe.NetSpec()
    for l in layerDefs:
        if l.has_key('bottom'):
            layer = getattr(L, l['type'])(getattr(net, l['bottom']), **l['args'])
        else:
            layer = getattr(L, l['type'])(**l['args'])
        net.__dict__.update({l['name']: layer})
    return net

for i in range(maxIter):
    paramValues = genValues(paramTemplates)
    layerDefs = map(lambda x: subValues(x, paramValues), layerTemplates)
    net = genNet(layerDefs)
    #print net.to_proto()
    #print dir(net.to_proto().layer)
    #print net.conv1.to_proto().layer[1].convolution_param.num_output
