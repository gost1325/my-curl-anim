import os
import ssl
import time
import math
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

# Карта мира для наложения на 3D-сферу (1 - суша, 0 - океан)
WORLD_MAP = [
    "0000000000000000000000000000000000000000",
    "0000011110000000011000001111111110000000",
    "0001111111100000111100111111111111110000",
    "0000111111000000011001111111111111110000",
    "0000011110000000000001111111111111000000",
    "0000001100000000000011111111111100000000",
    "0000000110000000000111111111110000000000",
    "0000000011100000000111111110000000000000",
    "0000000011111000000011111100000000000000",
    "0000000001111100000001111000000011100000",
    "0000000001111000000001110000000111110000",
    "0000000000110000000000100000000011100000",
    "0000000000100000000000000000000000000000",
    "0000000000000000000000000000000000000000",
]

COLORS = ["\033[96m", "\033[94m", "\033[95m", "\033[36m"]
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"

CACHE = {"btc": "загрузка...", "updated": 0}
SSL_CONTEXT = ssl._create_unverified_context()


def render_earth(angle):
    """Генерирует красивый 3D-шар Земли с синими океанами и зелёными материками."""
    radius = 7
    shade_chars = " .:-=+*#%@"
    map_h = len(WORLD_MAP)
    map_w = len(WORLD_MAP[0])
    lines = []

    for y in range(-radius, radius + 1):
        row = ["      "]  # Отступ слева для центрирования под логотипом
        # Корректировка пропорций шрифта терминала (символы выше, чем шире)
        ny = y / radius
        for x in range(-radius * 2, radius * 2 + 1):
            nx = x / (radius * 2)
            r2 = nx * nx + ny * ny
            if r2 <= 1.0:
                nz = math.sqrt(1.0 - r2)

                # Сферические координаты (широта и долгота) с учётом поворота
                lat = math.asin(max(-1.0, min(1.0, ny)))
                lon = math.atan2(nx, nz) + angle

                # Перевод координат в индекс на карте мира
                u = (lon / (2 * math.pi)) % 1.0
                v = (lat / math.pi) + 0.5
                mx = int(u * map_w) % map_w
                my = min(map_h - 1, max(0, int(v * map_h)))
                is_land = WORLD_MAP[my][mx] == "1"

                # Расчёт освещения (источник света спереди-слева-сверху)
                light = nx * -0.4 + ny * -0.3 + nz * 0.85
                light = max(0.15, min(1.0, light))
                char_idx = int(light * (len(shade_chars) - 1))
                ch = shade_chars[char_idx]

                if is_land:
                    row.append(f"{GREEN}{BOLD}{ch}{RESET}")
                else:
                    row.append(f"{BLUE}{ch}{RESET}")
            else:
                row.append(" ")
        lines.append("".join(row))

    return "\n".join(lines)


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

        # Предварительно рендерим 36 кадров плавного оборота Земли для быстрой работы
        earth_frames = [render_earth(i * (2 * math.pi / 36)) for i in range(36)]
        btc = get_btc_price()

        footer = (
            f"\n{DIM}──────────────────────────────────────────────────\n"
            f"андрей.ш. лох\n"
            f"11.03 А.И.Александрович слил калаш цзшке, позор не будет забыт....{RESET}\n"
        )

        step = 0
        try:
            while True:
                color = COLORS[(step // 3) % len(COLORS)]
                earth = earth_frames[step % len(earth_frames)]
                current_time = get_minsk_time()

                info_block = (
                    f"  {CYAN}✈ Telegram:{RESET}  {BOLD}@ImBOSS_No1{RESET}  (t.me/ImBOSS_No1)\n"
                    f"  {MAGENTA}♪ TikTok:{RESET}    {BOLD}@derev_everyday{RESET}\n"
                    f"  {YELLOW}₿ Bitcoin:{RESET}   {BOLD}{btc}{RESET}\n"
                    f"  {GREEN}⌚ Время BY:{RESET}  {current_time}\n"
                )

                frame = (
                    "\033[2J\033[H"
                    f"{color}{LOGO}{RESET}\n"
                    f"{earth}\n\n"
                    f"{info_block}"
                    f"{footer}"
                )

                self.wfile.write(frame.encode("utf-8"))
                self.wfile.flush()
                step += 1
                time.sleep(0.12)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = ThreadingHTTPServer(("0.0.0.0", port), AnimationHandler)
    print(f"Server started on port {port}")
    server.serve_forever()
