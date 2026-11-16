import os
import time
import json
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Красивый ASCII-логотип MANERA
LOGO = r"""
 __  __    _    _   _ _____ ____      _    

|  \/  |  / \  | \ | | ____|  _ \    / \   
| |\/| | / _ \ |  \| |  _| | |_) |  / _ \  
| |  | |/ ___ \| |\  | |___|  _ <  / ___ \ 
|_|  |_/_/   \_\_| \_|_____|_| \_\/_/   \_\
"""

# Цвета для анимации логотипа (голубой, синий, фиолетовый, бирюзовый)
COLORS = ["\033[96m", "\033[94m", "\033[95m", "\033[36m"]
RESET = "\033[0m"
DIM = "\033[2m"      # Тусклый / мелкий вид в терминале
YELLOW = "\033[93m"
GREEN = "\033[92m"

# Кэш для данных, чтобы не нагружать API при каждом кадре
CACHE = {"data": None, "updated": 0}


def get_live_info():
    now = time.time()
    # Обновляем погоду и курсы раз в 5 минут (300 секунд)
    if CACHE["data"] and (now - CACHE["updated"] < 300):
        return CACHE["data"]

    # 1. Погода в Миорах (Беларусь)
    weather = "н/д"
    try:
        req = urllib.request.Request(
            "https://wttr.in",
            headers={"User-Agent": "curl/7.81.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            weather = resp.read().decode("utf-8").strip()
    except Exception:
        weather = "не удалось загрузить"

    # 2. Официальный курс USD к BYN (API Нацбанка РБ)
    usd_byn = "н/д"
    try:
        with urllib.request.urlopen("https://nbrb.by", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            usd_byn = f"{data['Cur_OfficialRate']} BYN"
    except Exception:
        usd_byn = "ошибка загрузки"

    # 3. Курс Bitcoin (CoinGecko API)
    btc_usd = "н/д"
    try:
        req = urllib.request.Request(
            "https://coingecko.com",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            price = data["bitcoin"]["usd"]
            btc_usd = f"${price:,.0f}".replace(",", " ")
    except Exception:
        btc_usd = "ошибка загрузки"

    result = (
        f"{YELLOW}📍 Погода (Миоры, BY):{RESET} {weather}\n"
        f"{GREEN}💵 Курс USD (НБРБ):{RESET}    {usd_byn}\n"
        f"{YELLOW}₿  Bitcoin (BTC):{RESET}      {btc_usd}\n"
    )
    CACHE["data"] = result
    CACHE["updated"] = now
    return result


class AnimationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        user_agent = self.headers.get("User-Agent", "").lower()
        if "curl" not in user_agent:
            self.send_response(302)
            self.send_header("Location", "https://github.com")
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

        info_block = get_live_info()
        footer = (
            f"\n{DIM}--------------------------------------------------\n"
            f"андрей.ш. лох\n"
            f"11.03 А.И.Александрович слил калаш цзшке, позор не будет забыт....{RESET}\n"
        )

        step = 0
        try:
            while True:
                color = COLORS[step % len(COLORS)]
                frame = (
                    "\033[2J\033[H"
                    f"{color}{LOGO}{RESET}\n"
                    f"{info_block}"
                    f"{footer}"
                )
                self.wfile.write(frame.encode("utf-8"))
                self.wfile.flush()
                step += 1
                time.sleep(0.5)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = ThreadingHTTPServer(("0.0.0.0", port), AnimationHandler)
    print(f"Server started on port {port}")
    server.serve_forever()
