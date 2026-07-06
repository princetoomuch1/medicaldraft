from http.server import BaseHTTPRequestHandler, HTTPServer
import json

HOST = "127.0.0.1"
PORT = 8000


class MedicalDraftHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in {"/", "/health"}:
            payload = {"status": "ok", "service": "medical-draft-backend"}
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            body = b"Not Found"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), MedicalDraftHandler)
    print(f"Medical Draft backend running on http://{HOST}:{PORT}")
    server.serve_forever()
