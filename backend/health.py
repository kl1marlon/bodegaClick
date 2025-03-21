#!/usr/bin/env python3
"""
Script independiente para comprobar la salud del servicio.
También actúa como proxy para redirigir solicitudes al gateway.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import sys
import os
import json
import time

# Puerto para el servidor de health check
PORT = int(os.environ.get('HEALTH_PORT', 8001))

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Endpoint de health check
        if self.path == '/health' or self.path == '/health/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Verificar si el backend y gateway están disponibles
            backend_status = self._check_service("backend", 8000, "/api/health/")
            gateway_status = self._check_service("gateway", 80, "/")
            
            response = {
                'status': 'healthy',
                'service': 'health-service',
                'services': {
                    'backend': backend_status,
                    'gateway': gateway_status
                }
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
        
        # Para cualquier otra solicitud, intentar redirigirla al gateway
        # después de que esté disponible
        self._wait_for_gateway()
        try:
            # Redirigir al gateway
            gateway_url = f"http://gateway:80{self.path}"
            print(f"Redirigiendo solicitud a: {gateway_url}")
            
            # Copiar los encabezados
            headers = {}
            for key in self.headers:
                headers[key] = self.headers[key]
            
            req = urllib.request.Request(gateway_url, headers=headers)
            with urllib.request.urlopen(req) as response:
                # Copiar los encabezados de respuesta
                self.send_response(response.status)
                for key, val in response.getheaders():
                    if key.lower() != 'transfer-encoding':  # Excluir transfer-encoding
                        self.send_header(key, val)
                self.end_headers()
                
                # Copiar el cuerpo de la respuesta
                self.wfile.write(response.read())
        except urllib.error.URLError as e:
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': f'Error comunicando con el servicio: {str(e)}'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': f'Error interno: {str(e)}'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _wait_for_gateway(self):
        # Esperar a que el gateway esté disponible
        retries = 0
        while retries < 10:
            try:
                urllib.request.urlopen("http://gateway:80/", timeout=1)
                return True
            except:
                retries += 1
                if retries >= 10:
                    print("Gateway no disponible después de 10 intentos")
                    return False
                print(f"Gateway no disponible, reintentando ({retries}/10)...")
                time.sleep(2)
    
    def _check_service(self, service_name, port, path):
        try:
            url = f"http://{service_name}:{port}{path}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=1) as response:
                return {
                    'status': 'up',
                    'code': response.status
                }
        except Exception as e:
            return {
                'status': 'down',
                'error': str(e)
            }
            
    def log_message(self, format, *args):
        # Imprimir logs en stdout para diagnóstico
        if "/health" not in args[0]:  # No loggear health checks para reducir ruido
            sys.stdout.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format%args))

    def do_POST(self):
        # Para solicitudes POST, reenviar al gateway
        self._forward_request("POST")
    
    def do_PUT(self):
        self._forward_request("PUT")
    
    def do_DELETE(self):
        self._forward_request("DELETE")
    
    def _forward_request(self, method):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        self._wait_for_gateway()
        try:
            # Crear la solicitud
            gateway_url = f"http://gateway:80{self.path}"
            headers = {}
            for key in self.headers:
                headers[key] = self.headers[key]
            
            req = urllib.request.Request(gateway_url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                for key, val in response.getheaders():
                    if key.lower() != 'transfer-encoding':
                        self.send_header(key, val)
                self.end_headers()
                self.wfile.write(response.read())
        except urllib.error.URLError as e:
            self.send_response(502)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': f'Error comunicando con el servicio: {str(e)}'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': f'Error interno: {str(e)}'}
            self.wfile.write(json.dumps(response).encode('utf-8'))

if __name__ == '__main__':
    print(f"Iniciando servidor de health check en puerto {PORT}")
    try:
        with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
            print(f"Health check listo en http://0.0.0.0:{PORT}/health")
            print(f"Proxy inverso habilitado para otras rutas")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 