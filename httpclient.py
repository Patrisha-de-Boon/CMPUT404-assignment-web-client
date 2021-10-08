#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust, and Patrisha de Boon
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

from socketserver import StreamRequestHandler
import sys
import socket
import re
# you may use urllib to encode data appropriately
from urllib.parse import ParseResult, urlparse, quote

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class Request():
    def __init__(self, method):
        self.protocol: str = "HTTP/1.1"
        self.method: str = method
        self.uri: str = "/"
        self.params: dict = {}
        self.headers: dict = {}
        
    def compile_request(self):        
        paramStr = ""
        if (self.params and len(self.params) > 0):
            isFirst = True
            for name, value in self.params.items():
                if (isFirst):
                    isFirst = False
                else:
                    paramStr += "&"
                
                if name:
                    paramStr += quote(name)
                    if value:
                        paramStr += "=" + quote(value)
            
            self.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=utf-8"
            self.headers["Content-Length"] = len(paramStr.encode('utf-8'))
        else:
            self.headers["Content-Length"] = 0

        strRequest = self.method + " " + quote(self.uri) + " " + self.protocol + "\r\n"

        self.headers["User-Agent"] = "HttpClient/1.0"
        self.headers["Accept"] = "*/*"

        if (not "Connection" in self.headers):
            self.headers["Connection"] = "close"

        for name, value in self.headers.items():
            strRequest += name + ": " + (str(value)) + "\r\n"

        strRequest += "\r\n" + paramStr
        return strRequest

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

    def __str__(self):
        return "code = " + str(self.code) + "; body = " + self.body + "\n"

#get host information. This function is from Lab2
def get_remote_ip(host):
    try:
        remote_ip = socket.gethostbyname(host)
    except socket.gaierror:
        return None

    return remote_ip

class HTTPClient(object):
    def connect(self, host, port):
        if (not port):
            port = 80

        remote_ip = get_remote_ip(host)
        if remote_ip:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((remote_ip, port))
            return True
        else:
            self.response.code = 400
            self.response.body = "Hostname could not be resolved"
            return False

    def get_code(self, data):
        regResponse = re.search('^[^ ]* (\d+) ', data)
        if (regResponse):
            return int(regResponse.group(1))

        return None

    def get_body(self, data):
        regResponse = re.search('\r\n\r\n((.|\n|\r|\f)*)', data)
        if (regResponse):
            return regResponse.group(1)
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self):
        buffer = bytearray()
        done = False
        while not done:
            part = self.socket.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def parse_and_connect(self, url):
        urlComponents: ParseResult = urlparse(url)
        if (urlComponents):
            if (urlComponents.scheme and urlComponents.scheme != "http"):
                self.response.code = 505
                self.response.body = "Unsupported HTTP Version"
                return False
            else:
                if (self.connect(urlComponents.hostname, urlComponents.port)):
                    if (urlComponents.port and urlComponents.port != 80):
                        self.request.headers["Host"] = urlComponents.hostname + ":" + str(urlComponents.port)
                    else:
                        self.request.headers["Host"] = urlComponents.hostname
                    self.request.uri = urlComponents.path if urlComponents.path else "/"
                    if (urlComponents.query):
                        for query in urlComponents.query.split("&"):
                            queryComponents = query.split("=")
                            if (len(queryComponents) == 2):
                                self.request.params[queryComponents[0]] = queryComponents[1]
                            else:
                                self.request.params[queryComponents[0]] = None
                    return True
                else:
                    return False
        
        self.response.code = 500
        self.response.body = "Unable to parse url"
        return False

    def send_and_recieve(self):
        payload = self.request.compile_request()
        self.sendall(payload)
        self.socket.shutdown(socket.SHUT_WR)
        data = self.recvall()
        self.close()
        self.response.code = self.get_code(data)
        self.response.body = self.get_body(data)

    def GET(self, url, args=None):
        self.response = HTTPResponse(500, "")
        self.request = Request("GET")
        if (args):
            self.request.params = args
        if (url):
            if (not self.parse_and_connect(url)):
                return self.response
            self.send_and_recieve()
        
        return self.response

    def POST(self, url, args=None):
        self.response = HTTPResponse(500, "")
        self.request = Request("POST")
        if (args):
            self.request.params = args
        if (url):
            if (not self.parse_and_connect(url)):
                return self.response
            self.send_and_recieve()
        
        return self.response

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST(url, args)
        elif (command == "GET"):
            return self.GET(url, args)
        else:
            return HTTPResponse(405, "Method not allowed")
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
