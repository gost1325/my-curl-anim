import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Словарь с вашими анимациями
ANIMATIONS = {
    "/dance": [
        "  (o_o)  \n  /| |\\  \n   / \\   ",
        "  \\(o_o)/ \n   | |   \n   / \\   ",
    ],
    "/heart": [
        "   ** **   \n  *******  \n   *****   \n     *     ",
        "  *** ***  \n ********* \n  *******  \n    ***    \n     *     ",
    ],
}

class AnimationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Если открыли не через curl, перенаправляем на ваш сайт или GitHub
        user_agent = self.headers.get("User-Agent", "").lower()
        if "curl" not in user_agent:
            self.send_response(302)
            self.send_header("Location", "https://github.com")
            self.end_headers()
            return

        # Выбираем анимацию по адресу (по умолчанию /dance)
        path = self.path.rstrip("/") or "/dance"
        frames = ANIMATIONS.get(path)

        if not frames:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Animation not found. Try /dance or /heart\n")
            return

        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

        try:
            while True:
                for frame in frames:
                    # Очистка экрана и вывод кадра
                    output = "\033[2J\033[H" + frame + "\n"
                    self.wfile.write(output.encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(0.3)
        except (BrokenPipeError, ConnectionResetError):
            pass  # Клиент закрыл соединение (Ctrl+C)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = ThreadingHTTPServer(("0.0.0.0", port), AnimationHandler)
    print(f"Server started on port {port}")
    server.serve_forever()