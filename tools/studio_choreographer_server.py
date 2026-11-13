#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur HTTP multi-threadé dédié pour l'Atelier de Chorégraphie 3D (Choreographer Studio).
Supporte le multi-threading (ThreadingTCPServer), Range Requests (206 Partial Content pour MP3/VRM),
CORS complet et tous les types MIME nécessaires (.vrm, .vrma, .mp3, .json).
"""
import http.server
import socketserver
import os
import mimetypes
import re
import urllib.parse

PORT = 8766
DIRECTORY = "/home/lbg/Projets/LBG_Studios/packages/compagnon-desktop/overlay"

mimetypes.add_type("model/gltf-binary", ".vrm")
mimetypes.add_type("application/octet-stream", ".vrma")
mimetypes.add_type("audio/mpeg", ".mp3")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/html", ".html")
mimetypes.add_type("text/css", ".css")

BYTE_RANGE_RE = re.compile(r"bytes=(\d+)-(\d*)")

class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_head(self):
        """Support standard HTTP Range requests for MP3 streaming and large VRM chunks."""
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                self.send_response(http.HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts[0], parts[1], parts[2] + '/', parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)

        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(http.HTTPStatus.NOT_FOUND, "File not found")
            return None

        fs = os.fstat(f.fileno())
        total_len = fs[6]

        range_header = self.headers.get("Range")
        if range_header:
            m = BYTE_RANGE_RE.match(range_header)
            if m:
                first = int(m.group(1))
                last = int(m.group(2)) if m.group(2) else total_len - 1
                if first >= total_len:
                    self.send_error(http.HTTPStatus.RANGE_NOT_SATISFIABLE)
                    f.close()
                    return None
                last = min(last, total_len - 1)
                length = last - first + 1
                self.send_response(http.HTTPStatus.PARTIAL_CONTENT)
                self.send_header("Content-type", ctype)
                self.send_header("Content-Range", f"bytes {first}-{last}/{total_len}")
                self.send_header("Content-Length", str(length))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.end_headers()
                f.seek(first)
                return f

        self.send_response(http.HTTPStatus.OK)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(total_len))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def run():
    server_address = ("0.0.0.0", PORT)
    with ThreadedHTTPServer(server_address, RangeHTTPRequestHandler) as httpd:
        print(f"✦ Multi-Threaded Choreographer Studio actif sur http://0.0.0.0:{PORT}/choreographer.html")
        httpd.serve_forever()

if __name__ == "__main__":
    run()
