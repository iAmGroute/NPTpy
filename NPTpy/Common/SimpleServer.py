import os
import sys
import traceback
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if not mimetypes.inited:
    mimetypes.init()
fileExtMap = {}
for t in mimetypes.types_map:
    fileExtMap[t[1:]] = mimetypes.types_map[t]
fileExtMap.update({
    '':      'application/octet-stream', # Fallback
    'map':   'application/json',
    'eot':   'application/vnd.ms-fontobject',
    'ttf':   'font/ttf',
    'woff':  'font/woff',
    'woff2': 'font/woff2',
    'py':    'text/plain',
    'c':     'text/plain',
    'h':     'text/plain'
})

def scanDir(path, maxDepth=4):
    maxDepth -= 1
    if maxDepth < 0:
        return []
    result = [];
    for name in os.listdir(path):
        if name.startswith('.'):
            continue
        fullname = path + '/' + name
        if os.path.isdir(fullname):
            result.extend(scanDir(fullname, maxDepth))
        else:
            result.append(fullname)
    return result

def tryReadFile(path):
    content = None
    try:
        with open(path, 'rb') as f:
            content = f.read()
    except OSError as e:
        print('Can\'t open file "{0}":\n\t{1}'.format(path, e))
    return content

class Page:
    def __init__(self, contentType):
        self.contentType = contentType
    def getContent(self):
        raise NotImplementedError

class LoadedPage(Page):
    def __init__(self, contentType, content):
        Page.__init__(self, contentType)
        self.content = content
    def getContent(self):
        return self.content

class FileRefPage(Page):
    def __init__(self, contentType, contentPath):
        Page.__init__(self, contentType)
        self.contentPath = contentPath
    def getContent(self):
        return tryReadFile(self.contentPath)

def guessContentType(path):
    ext = path[path.rfind('.'):][1:]
    ext = ext.lower()
    result = fileExtMap.get(ext, fileExtMap[''])
    return result

def consumeDir(dirName):
    try:
        files = scanDir(dirName)
    except OSError as e:
        print('Can\'t scan directory "{0}":\n\t{1}'.format(dirName, e))
        return {}
    result = {}
    for file in files:
        print(file)
        contentType = guessContentType(file)
        content     = tryReadFile(file)
        name = file[len(dirName):]
        result[name] = LoadedPage(contentType, content)
    return result


class SimpleServerHandler(BaseHTTPRequestHandler):

    server_version = 'WebUI'

    def __init__(self, *args, **kwargs):
        if not hasattr(self, 'pages'): self.pages = None
        if not hasattr(self,   'api'): self.api   = None
        super().__init__(*args, **kwargs)

    def end_headers(self):
        self.send_header('access-control-allow-credentials', 'true')
        self.send_header('access-control-allow-origin',      '*')
        BaseHTTPRequestHandler.end_headers(self)

    def getPage(self):
        return self.pages.get(self.path)

    def do_GET(self):
        if self.pages:
            page = self.getPage()
            if page:
                self.sendPage(page)
            else:
                # self.send404()
                self.sendRedirect()
        else:
            self.sendNotImplemented()

    def do_POST(self):
        if self.api:
            try:
                size    = int(self.headers['Content-Length'])
                request = self.rfile.read(size)
                data    = json.loads(request)
                reply   = self.api.process(self, data)
                content = bytes(json.dumps(reply), 'utf-8')
                page    = LoadedPage('application/json; charset=utf-8', content)
                self.sendPage(page)
            except Exception as e:
                _, _, tb = sys.exc_info()
                traceback.print_tb(tb)
                filename, line, func, text = traceback.extract_tb(tb)[-1]
                info = '{} | {} | @{}() {}:{}'.format(repr(e), text, func, filename, line)
                self.send400(info)
        else:
            self.sendNotImplemented()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('access-control-allow-methods', 'POST, OPTIONS, GET')
        self.send_header('access-control-allow-headers', 'content-type')
        self.send_header('allow', 'POST, OPTIONS, GET')
        self.end_headers()

    def send400(self, info=''):
        content = bytes(info, 'utf-8')
        self.send_response(HTTPStatus.BAD_REQUEST)
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)

    def send404(self):
        self.send_error(HTTPStatus.NOT_FOUND)

    def send415(self):
        self.send_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    def sendRedirect(self):
        self.send_response(HTTPStatus.MOVED_PERMANENTLY)
        self.send_header('Location', '/')
        self.end_headers()

    def sendNotImplemented(self):
        self.send_error(HTTPStatus.NOT_IMPLEMENTED)

    def sendPage(self, page):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', page.contentType)
        self.send_header('Content-Length', len(page.content))
        self.end_headers()
        self.wfile.write(page.content)


class SimpleServer:

    def __init__(self, directory=None, api=None):
        pages = None
        if directory:
            pages = consumeDir(directory)
            pages['/'] = pages.get('/index.html')
        self.handlerClass = SimpleServerHandler
        self.handlerClass.pages = pages
        self.handlerClass.api   = api
        self.server = None

    def run(self, port=0, address='0.0.0.0'):
        with ThreadingHTTPServer((address, port), self.handlerClass) as a:
            print('Listening on ' + str(a.server_address))
            self.server = a
            a.allow_reuse_address = True
            a.serve_forever()

    def stop(self):
        try:
            self.server.socket.close()
            self.server.shutdown()
        except OSError:
            return False
        return True

