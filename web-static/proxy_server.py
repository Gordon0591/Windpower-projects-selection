"""静态文件 + API 代理服务器"""
import http.server
import urllib.request
import urllib.error
import os

API_TARGET = "http://localhost:8000"
PORT = 3000
WEB_ROOT = os.path.dirname(os.path.abspath(__file__))


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_ROOT, **kwargs)

    def do_GET(self):
        if self.path.startswith("/v1/"):
            self.proxy_request()
        else:
            super().do_GET()

    def proxy_request(self):
        url = API_TARGET + self.path
        try:
            req = urllib.request.Request(url)
            # Forward headers
            for h in ["authorization", "content-type", "accept"]:
                val = self.headers.get(h)
                if val:
                    req.add_header(h, val)

            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                self.send_header("Content-Type",
                                 resp.headers.get("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f'{{"error":"{str(e)}"}}'.encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"Proxy server running on http://0.0.0.0:{PORT}")
    print(f"  Static files: {WEB_ROOT}")
    print(f"  API proxy: /v1/* -> {API_TARGET}/v1/*")
    server.serve_forever()
