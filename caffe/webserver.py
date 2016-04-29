import cgi
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
    def do_POST(self):

def main():
    try:
        server = HTTPServer(('', 8080), Handler)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()

if __name__ == '__main__':
    main()
