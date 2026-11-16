import os
import ssl
import time
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOGO = r"""
 __  __    _    _   _ _____ ____      _    

|  \/  |  / \  | \ | | ____|  _ \    / \   
| |\/| | / _ \ |  \| |  _| | |_) |  / _ \  
| |  | |/ ___ \| |\  | |___|  _ <  / ___ \ 
|_|  |_/_/   \_\_| \_|_____|_| \_\/_/   \_\
"""

# Кадры вращающейся Земли
EARTH_FRAMES = [
    r"""
        .---.
      .'   _ '.
     /   .' '. \

    |   |     | |
    |    '._.'  |
     \         /
      '._____.'
    """,
    r"""
        .---.
      .'  _  '.
     /  .' '.  \

    |  |     |  |
    |   '._.'   |
     \         /
      '._____.'
    """,
    r"""
        .---.
      .' _   '.
     / .' '.   \

    | |     |   |
    |  '._.'    |
     \         /
      '._____.'
    """,
    r"""
        .---.
      .'     '.
     / '.   .' \

    |    | |    |
    |   .' '.   |
     \         /
      '._____.'
    """,
    r"""
        .---.
      .'     '.
     /   .---. \

    |   /     \ |
    |   \     / |
     \   '---' /
      '._____.'
    """,
    r"""
        .---.
      .'     '.
     / .---.   \

    | /     \   |
    | \     /   |
     \ '---'   /
      '._____.'
    """
]

COLORS = ["\033[96m", "\033[94m", "\033[95m", "\033[36m"]
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"

CACHE = {"btc": "загрузка...", "updated": 0}
SSL_CONTEXT = ssl._create_unverified_context()


def get_btc_price():
    now = time.time()
    if CACHE["btc"] != "загрузка..." and (now - CACHE["updated"] < 300):
        return CACHE["btc"]

    try:
        req = urllib.request.Request(
            "https://coinbase.com",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5, context=SSL_CONTEXT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            price = float(data["data"]["amount"])
            CACHE["btc"] = f"${price:,.0f}".replace(",", " ")
            CACHE["updated"] = now
    except Exception:
        if CACHE["btc"] == "загрузка...":
            CACHE["btc"] = "н/д"

    return CACHE["btc"]


def get_minsk_time():
    # Минское время (UTC+3)
    tz_minsk = timezone(timedelta(hours=3))
    return datetime.now(tz_minsk).strftime("%H:%M:%S")


class AnimationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        user_agent = self.headers.get("User-Agent", "").lower()
        if "curl" not in user_agent:
            self.send_response(302)
            self.send_header("Location", "https://t.me")
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

        btc = get_btc_price()

        footer = (
            f"\n{DIM}──────────────────────────────────────────────────\n"
            f"андрей.ш. лох\n"
            f"11.03 А.И.Александрович слил калаш цзшке, позор не будет забыт....{RESET}\n"
        )

        step = 0
        try:
            while True:
                color = COLORS[step % len(COLORS)]
                earth = EARTH_FRAMES[step % len(EARTH_FRAMES)]
                current_time = get_minsk_time()

                info_block = (
                    f"  {CYAN}✈ Telegram:{RESET}  {BOLD}@ImBOSS_No1{RESET}  (t.me/ImBOSS_No1)\n"
                    f"  {MAGENTA}♪ TikTok:{RESET}    {BOLD}@derev_everyday{RESET}\n"
                    f"  {YELLOW}₿ Bitcoin:{RESET}   {BOLD}{btc}{RESET}\n"
                    f"  {GREEN}⌚ Время BY:{RESET}  {current_time}\n"
                )

                frame = (
                    "\033[2J\033[H"
                    f"{color}{LOGO}{RESET}"
                    f"{CYAN}{earth}{RESET}\n"
                    f"{info_block}"
                    f"{footer}"
                )

                self.wfile.write(frame.encode("utf-8"))
                self.wfile.flush()
                step += 1
                time.sleep(0.35)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = ThreadingHTTPServer(("0.0.0.0", port), AnimationHandler)
    print(f"Server started on port {port}")
    server.serve_forever()

