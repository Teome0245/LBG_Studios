#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur HTTP dédié pour l'Atelier de Chorégraphie 3D (Choreographer Studio).
Supporte CORS et les types MIME spécifiques (.vrm, .vrma, .mp3, .json).
"""
import http.server
import socketserver
import os
import mimetypes

PORT = 8766
DIRECTORY = "/home/lbg/Projets/LBG_Studios/packages/compagnon-desktop/overlay"

mimetypes.add_type("model/gltf-binary", ".vrm")
mimetypes.add_type("application/octet-stream", ".vrma")
mimetypes.add_type("audio/mpeg", ".mp3")
mimetypes.add_type("application/json", ".json")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def run():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"✦ Choreographer Studio Web Server actif sur http://0.0.0.0:{PORT}/choreographer.html")
        httpd.serve_forever()

if __name__ == "__main__":
    run()
