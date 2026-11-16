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

WORLD_MAP = [
    "0000000000000000000000000000000000000000",
    "0000011110000000011000001111111110000000",
    "0001111111100000111100111111111111110000",
    "0000111111000000011001111111111111110000",
    "0000011110000000000001111111111111110000",
    "0000001100000000000011111111111100000000",
    "0000000110000000000111111111110000000000",
    "0000000011100000000111111110000000000000",
    "0000000011111000000111111110000000000000",
    "0000000001111100000011111110000000111000",
    "0000000001111100000011110000000001111100",
    "0000000000110000000000100000000000111000",
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
    radius = 7
    shade_chars = " .:-=+*#%@"
    map_h = len(WORLD_MAP)
    map_w = len(WORLD_MAP[0])
    lines = []

    for y in range(-radius, radius + 1):
        row = ["      "]
        ny = y / radius
        for x in range(-radius * 2, radius * 2 + 1):
            nx = x / (radius * 2)
            r2 = nx * nx + ny * ny
            if r2 <= 1.0:
                nz = math.sqrt(1.0 - r2)
                lat = math.asin(max(-1.0, min(1.0, ny)))
                lon = math.atan2(nx, nz) + angle
                u = (lon / (2 * math.pi)) % 1.0
                v = (lat / math.pi) + 0.5
                mx = int(u * map_w) % map_w
                my = min(map_h - 1, max(0, int(v * map_h)))
                is_land = WORLD_MAP[my][mx] == "1"

                light = max(0.15, min(1.0, nx * -0.4 + ny * -0.3 + nz * 0.85))
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


def get_web_html(btc):
    """Возвращает красивую веб-страницу терминала для открытия в Telegram и браузере."""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MANERA Terminal</title>
<style>
  body {{
    background-color: #0b0e14;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    margin: 0;
    padding: 15px;
    box-sizing: border-box;
  }}
  .terminal {{
    background: #11151c;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px;
    max-width: 520px;
    width: 100%;
    box-shadow: 0 10px 30px rgba(0, 255, 255, 0.1);
  }}
  .header-bar {{
    display: flex;
    gap: 8px;
    margin-bottom: 15px;
    border-bottom: 1px solid #21262d;
    padding-bottom: 10px;
  }}
  .dot {{ width: 12px; height: 12px; border-radius: 50%; }}
  .red {{ background: #ff5f56; }}
  .yellow {{ background: #ffbd2e; }}
  .green {{ background: #27c93f; }}
  .title-text {{ color: #8b949e; font-size: 12px; margin-left: auto; }}
  pre.logo {{
    font-size: 11px;
    line-height: 1.1;
    font-weight: bold;
    text-align: center;
    margin: 0 0 10px 0;
    animation: colorShift 3s infinite alternate;
  }}
  @keyframes colorShift {{
    0% {{ color: #00ffff; text-shadow: 0 0 8px rgba(0,255,255,0.4); }}
    50% {{ color: #58a6ff; text-shadow: 0 0 8px rgba(88,166,255,0.4); }}
    100% {{ color: #d2a8ff; text-shadow: 0 0 8px rgba(210,168,255,0.4); }}
  }}
  pre#earth {{
    font-size: 13px;
    line-height: 1.05;
    text-align: center;
    margin: 10px 0 20px 0;
    letter-spacing: 1px;
  }}
  .land {{ color: #3fb950; font-weight: bold; }}
  .ocean {{ color: #2f81f7; }}
  .info {{
    font-size: 14px;
    line-height: 1.8;
    background: #0d1117;
    padding: 12px 15px;
    border-radius: 8px;
    border: 1px solid #21262d;
  }}
  .info a {{
    color: #58a6ff;
    text-decoration: none;
    font-weight: bold;
  }}
  .info a:hover {{ text-decoration: underline; }}
  .label-tg {{ color: #39c5cf; }}
  .label-tt {{ color: #d2a8ff; }}
  .label-btc {{ color: #e3b341; }}
  .label-time {{ color: #3fb950; }}
  .footer {{
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px dashed #30363d;
    font-size: 11px;
    color: #6e7681;
    line-height: 1.4;
  }}
</style>
</head>
<body>
<div class="terminal">
  <div class="header-bar">
    <div class="dot red"></div>
    <div class="dot yellow"></div>
    <div class="dot green"></div>
    <span class="title-text">cmd.exe — curl manera</span>
  </div>
  <pre class="logo">{LOGO}</pre>
  <pre id="earth"></pre>
  <div class="info">
    <div><span class="label-tg">✈ Telegram:</span> <a href="https://t.me" target="_blank">@ImBOSS_No1</a></div>
    <div><span class="label-tt">♪ TikTok:</span> <a href="https://tiktok.com" target="_blank">@derev_everyday</a></div>
    <div><span class="label-btc">₿ Bitcoin:</span> <b>{btc}</b></div>
    <div><span class="label-time">⌚ Время BY:</span> <span id="clock">--:--:--</span></div>
  </div>
  <div class="footer">
    андрей.ш. лох<br>
    11.03 А.И.Александрович слил калаш цзшке, позор не будет забыт....
  </div>
</div>

<script>
  const worldMap = {json.dumps(WORLD_MAP)};
  const shadeChars = " .:-=+*#%@";
  let angle = 0;

  function renderEarth() {{
    const radius = 7;
    const mapH = worldMap.length;
    const mapW = worldMap[0].length;
    let html = "";

    for (let y = -radius; y <= radius; y++) {{
      const ny = y / radius;
      for (let x = -radius * 2; x <= radius * 2; x++) {{
        const nx = x / (radius * 2);
        const r2 = nx * nx + ny * ny;
        if (r2 <= 1.0) {{
          const nz = Math.sqrt(1.0 - r2);
          const lat = Math.asin(Math.max(-1, Math.min(1, ny)));
          const lon = Math.atan2(nx, nz) + angle;
          const u = ((lon / (2 * Math.PI)) % 1 + 1) % 1;
          const v = (lat / Math.PI) + 0.5;
          const mx = Math.floor(u * mapW) % mapW;
          const my = Math.min(mapH - 1, Math.max(0, Math.floor(v * mapH)));
          const isLand = worldMap[my][mx] === "1";

          let light = nx * -0.4 + ny * -0.3 + nz * 0.85;
          light = Math.max(0.15, Math.min(1.0, light));
          const ch = shadeChars[Math.floor(light * (shadeChars.length - 1))];

          if (isLand) {{
            html += `<span class="land">${{ch}}</span>`;
          }} else {{
            html += `<span class="ocean">${{ch}}</span>`;
          }}
        }} else {{
          html += " ";
        }}
      }}
      html += "\\n";
    }}
    document.getElementById("earth").innerHTML = html;
    angle += 0.14;
  }}

  function updateClock() {{
    const now = new Date();
    const minskTime = new Date(now.toLocaleString("en-US", {{timeZone: "Europe/Minsk"}}));
    document.getElementById("clock").innerText = minskTime.toTimeString().split(" ")[0];
  }}

  setInterval(renderEarth, 100);
  setInterval(updateClock, 1000);
  renderEarth();
  updateClock();
</script>
</body>
</html>"""


class AnimationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        user_agent = self.headers.get("User-Agent", "").lower()
        btc = get_btc_price()

        # Если открыли через браузер или нажали кнопку в Telegram — отдаём веб-терминал
        if "curl" not in user_agent:
            html = get_web_html(btc)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # Если запустили через curl в CMD — отдаём консольную анимацию
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

        earth_frames = [render_earth(i * (2 * math.pi / 36)) for i in range(36)]
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
