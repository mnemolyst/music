from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs
import sys
from os import path
import lmdb
import numpy as np
from numpy import zeros, isfinite, floor, ceil, arange, linalg, array, ones
import pickle
import PIL
import StringIO
caffeRoot = path.join(path.expanduser('~'), 'music_project', 'caffe')
sys.path.insert(1, path.join(caffeRoot, 'python'))
import caffe
import socket
if socket.gethostname() == 'anode':
    caffe.set_mode_cpu()
else:
    caffe.set_mode_gpu()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/net':
            qs = parse_qs(parsed.query)
            netPath = qs['net'][0] + '.prototxt'
            version = qs['ver'][0]
            layer = qs['layer'][0]
            bop = qs['bop'][0]
            if 'snap' in qs:
                net = caffe.Net(path.join(caffeRoot, 'music', 'net', version, netPath), path.join(caffeRoot, 'music', 'net', version, 'snapshots', qs['snap'][0] + '.caffemodel'), caffe.TRAIN)
            else:
                net = caffe.Net(path.join(caffeRoot, 'music', 'net', version, netPath), caffe.TRAIN)

            if bop == 'b':
                data = net.blobs[layer].data
            elif bop == 'p':
                data = net.params[layer][0].data
                print data.min()
                print data.max()
                data = 255 * (data - data.min()) / (data.max() - data.min())
                print 'shape', data.shape
                n = int(np.ceil(np.sqrt(data.shape[0] * data.shape[1])))
                resImg = PIL.Image.new('L', (data.shape[3] * data.shape[1], data.shape[2] * data.shape[0]))
                print 'size', resImg.size
                for i in range(data.shape[0]):
                    for j in range(data.shape[1]):
                        #print data.astype(np.ubyte)[i, j, ...]
                        img = PIL.Image.fromarray(data.astype(np.ubyte)[i, j, ...], 'L')
                        resImg.paste(img, (j * data.shape[3], i * data.shape[2]))
                contentType = 'image/png'
                stringbuf = StringIO.StringIO()
                resImg.save(stringbuf, 'png')
                response = stringbuf.getvalue()
        else:
            contentType = 'text/html'
            response = 'hi'
        self.send_response(200)
        self.send_header('Content-type', contentType)
        self.end_headers()
        self.wfile.write(response)
    def do_POST(self):
        pass

if __name__ == '__main__':
    try:
        print 'running'
        server = HTTPServer(('', 8080), Handler)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
