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

layerConstructors = {
    'Data': L.Data,
    'Convolution': L.Convolution,
}

layerDefs = {
    'images': {
        'type': 'Data',
        'args': {
            'source': 'music/lmdb/train/images',
            'batch_size': 10,
            'backend': P.Data.LMDB,
            'transform_param': {
                'scale': 1./255
            },
            'ntop': 1
        }
    },
    'conv1': {
        'type': 'Convolution',
        'bottom': 'images',
        'args': {
            'param': [
                {'lr_mult': 1},
                {'lr_mult': 2},
            ],
            'num_output': 30,
            'kernel_size': 4,
            'stride': 2,
            'weight_filler': {
                'type': 'xavier'
            },
            'bias_filler': {
                'type': 'constant',
                'value': 0.2
            }
        }
    }
}

def parseParams(template):
    params = []
    pIter1 = re.finditer('%{(.*?)}%', template, re.S)
    for i1 in pIter1:
        param = {
            'start': i1.start(),
            'end': i1.end()
        }
        m = i1.group()
        # TODO real parsing
        #pBlockIter2 = re.finditer('(\S+)\s*=\s*<<<(.*)>>>', m, re.S)
        #for i2 in pBlockIter2:
        #    param[i2.group(1)] = i2.group(2)
        pIter2 = re.finditer('(\S+)\s*=\s*(\S+)', m)
        for i2 in pIter2:
            param[i2.group(1)] = i2.group(2)
        params.append(param)
    return params

def genValues(params):
    values = []
    for param in params:
        if param['type'] == 'real':
            value = float(param['min']) + random.random() * (float(param['max']) - float(param['min']))
        elif param['type'] == 'log':
            value = math.pow(10, float(param['min']) + random.random() * (float(param['max']) - float(param['min'])))
        elif param['type'] == 'int':
            n = (int(param['max']) - int(param['min'])) / int(param['step'])
            c = random.randint(0, n)
            value = int(param['min']) + c * int(param['step'])
        #elif param['type'] == 'repeat':
        #    n = (int(param['max']) - int(param['min'])) / int(param['step'])
        #    c = random.randint(0, n)
        #    subT = param['template'].replace('%<', '%{').replace('>%', '}%')
        #    print subT
        #    subP = parseParams(subT)
        #    subV = genValues(subP)
        #    rep = int(param['min']) + c * int(param['step'])
        #    value = subValues(subT, subP, subV) * rep
        else:
            continue
        values.append(value)

    return values

def subValues(template, params, values):
    for (p, v) in zip(params, values):
        template = template[:p['start']] + str(v) + template[p['end']:]
    return template

#file = open(templateFile, 'r')
#modelTemplate = file.read()
#file.close()
#
#params = parseParams(modelTemplate)
#print params

#for i in range(maxIter):
#    values = genValues(params)
#    modelDef = subValues(modelTemplate, params, values)

n = caffe.NetSpec()

for k in layerDefs:
    print k
    if layerDefs[k].has_key('bottom'):
        print 'hi'
        layer = getattr(L, layerDefs[k]['type'])(getattr(n, layerDefs[k]['bottom']), **layerDefs[k]['args'])
    else:
        print 'yo'
        layer = getattr(L, layerDefs[k]['type'])(**layerDefs[k]['args'])
    n.__dict__.update({k: layer})

#print n.conv1
#print dir(n.conv1.to_proto())
print n.conv1.to_proto().layer[1].param[1].lr_mult
