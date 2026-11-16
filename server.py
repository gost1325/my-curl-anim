import os
import ssl
import time
import json
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOGO = r"""
 __  __    _    _   _ _____ ____      _    

|  \/  |  / \  | \ | | ____|  _ \    / \   
| |\/| | / _ \ |  \| |  _| | |_) |  / _ \  
| |  | |/ ___ \| |\  | |___|  _ <  / ___ \ 
|_|  |_/_/   \_\_| \_|_____|_| \_\/_/   \_\
"""

COLORS = ["\033[96m", "\033[94m", "\033[95m", "\033[36m"]
RESET = "\033[0m"
DIM = "\033[2m"
YELLOW = "\033[93m"
GREEN = "\033[92m"

CACHE = {"data": None, "updated": 0}

# Отключаем строгую проверку SSL для стабильной работы на облачных серверах
SSL_CONTEXT = ssl._create_unverified_context()

# Расшифровка кодов погоды Open-Meteo
WEATHER_CODES = {
    0: "Ясно", 1: "Преимущественно ясно", 2: "Переменная облачность", 3: "Пасмурно",
    45: "Туман", 48: "Изморозь", 51: "Легкая морось", 53: "Морось", 55: "Сильная морось",
    61: "Небольшой дождь", 63: "Дождь", 65: "Сильный дождь",
    71: "Небольшой снег", 73: "Снег", 75: "Сильный снег", 77: "Снежные зерна",
    80: "Ливень", 81: "Сильный ливень", 85: "Снегопад", 95: "Гроза"
}


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=8, context=SSL_CONTEXT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_live_info():
    now = time.time()
    if CACHE["data"] and (now - CACHE["updated"] < 300):
        return CACHE["data"]

    # 1. Погода строго по координатам г. Миоры (55.6222, 27.6281) через Open-Meteo
    weather = "недоступно"
    try:
        w_url = (
            "https://open-meteo.com"
            "?latitude=55.6222&longitude=27.6281&current_weather=true&windspeed_unit=ms"
        )
        w_data = fetch_json(w_url)
        cw = w_data["current_weather"]
        temp = cw["temperature"]
        wind = cw["windspeed"]
        desc = WEATHER_CODES.get(cw["weathercode"], "")
        sign = "+" if temp > 0 else ""
        weather = f"{sign}{temp}°C, {desc}, ветер {wind} м/с"
    except Exception:
        weather = "ошибка загрузки"

    # 2. Курс USD к BYN (через Open Exchange Rates API, работает из любой страны)
    usd_byn = "недоступно"
    try:
        r_data = fetch_json("https://er-api.com")
        rate = r_data["rates"]["BYN"]
        usd_byn = f"{rate:.4f} BYN"
    except Exception:
        usd_byn = "ошибка загрузки"

    # 3. Курс Bitcoin в USD (через API Coinbase, без лимитов на IP Render)
    btc_usd = "недоступно"
    try:
        b_data = fetch_json("https://coinbase.com")
        price = float(b_data["data"]["amount"])
        btc_usd = f"${price:,.0f}".replace(",", " ")
    except Exception:
        btc_usd = "ошибка загрузки"

    result = (
        f"{YELLOW}📍 Погода (Миоры, BY):{RESET} {weather}\n"
        f"{GREEN}💵 Курс USD / BYN:{RESET}     {usd_byn}\n"
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
