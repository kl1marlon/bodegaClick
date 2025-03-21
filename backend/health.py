#!/usr/bin/env python3
"""
Script independiente para comprobar la salud del servicio.
Puede ser ejecutado por contenedores Docker o servicios externos.
"""

import http.server
import socketserver
import sys
import os
import json

# Puerto para el servidor de health check
PORT = int(os.environ.get('HEALTH_PORT', 8001))

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/health/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'backend-health-check'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': 'Not found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def log_message(self, format, *args):
        # Desactivar logs para no saturar stdout
        pass

if __name__ == '__main__':
    print(f"Iniciando servidor de health check en puerto {PORT}")
    try:
        with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
            print(f"Health check listo en http://localhost:{PORT}/health")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 