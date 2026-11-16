
import json
import math
import os
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
 
TELEGRAM_USER = "ImBOSS_No1"
TIKTOK_USER = "derev_everyday"
TELEGRAM_URL = f"https://t.me/{TELEGRAM_USER}"
TIKTOK_URL = f"https://www.tiktok.com/@{TIKTOK_USER}"
BTC_API = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
 
LOGO = r"""
 __  __    _    _   _ _____ ____      _
|  \/  |  / \  | \ | | ____|  _ \    / \
| |\/| | / _ \ |  \| |  _| | |_) |  / _ \
| |  | |/ ___ \| |\  | |___|  _ <  / ___ \
|_|  |_/_/   \_\_| \_|_____|_| \_\/_/   \_\
"""
 
# 1 = суша. Строка 0 = север, колонка 0 = 180° з.д.
WORLD_MAP = [
    "0000000000000000000000000000000000000000",
    "0000011110000000011000001111111110000000",
    "0001111111100000111100111111111111110000",
    "0000111111000000011001111111111111110000",
    "0000111100000000000011111111111100000000",
    "0000011000000000000111111111111000000000",
    "0000001100000000001111111111100000000000",
    "0000000011100000001111111100000000000000",
    "0000000011111000001111111100000000000000",
    "0000000001111100000111111000000011100000",
    "0000000001111000000111100000000011111000",
    "0000000000110000000001000000000001110000",
    "0000000000100000000000000000000000000000",
    "0000000000000000000000000000000000000000",
]
 
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
LOGO_COLORS = ["\033[96m", "\033[94m", "\033[95m", "\033[36m"]
SHADE = " .:-=+*#%@"
 
# ---------------------------------------------------------------- BTC ----
BTC = {"price": None, "updated": 0.0}
BTC_LOCK = threading.Lock()
 
 
def fetch_btc():
    req = urllib.request.Request(BTC_API, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=6) as resp:
        return float(json.loads(resp.read().decode())["data"]["amount"])
 
 
def btc_worker():
    """Фоновый поток: обновляет цену раз в минуту, запросы клиентов не блокирует."""
    while True:
        try:
            price = fetch_btc()
            with BTC_LOCK:
                BTC["price"] = price
                BTC["updated"] = time.time()
        except Exception as exc:
            print("BTC fetch failed:", exc)
        time.sleep(60)
 
 
def btc_text():
    with BTC_LOCK:
        p = BTC["price"]
    return "н/д" if p is None else f"${p:,.0f}".replace(",", " ")
 
 
def minsk_time():
    return datetime.now(timezone(timedelta(hours=3))).strftime("%H:%M:%S")
 
 
# -------------------------------------------------------- ASCII globe ----
def render_earth(angle, radius=7):
    map_h, map_w = len(WORLD_MAP), len(WORLD_MAP[0])
    lines = []
    for y in range(-radius, radius + 1):
        ny = y / radius
        row = ["      "]
        for x in range(-radius * 2, radius * 2 + 1):
            nx = x / (radius * 2)
            r2 = nx * nx + ny * ny
            if r2 > 1.0:
                row.append(" ")
                continue
            nz = math.sqrt(1.0 - r2)
            lat = math.asin(max(-1.0, min(1.0, -ny)))  # север сверху
            lon = math.atan2(nx, nz) + angle
            u = (lon / (2 * math.pi)) % 1.0
            v = 0.5 - lat / math.pi
            mx = int(u * map_w) % map_w
            my = min(map_h - 1, max(0, int(v * map_h)))
            light = max(0.15, min(1.0, nx * -0.4 + ny * -0.3 + nz * 0.85))
            ch = SHADE[int(light * (len(SHADE) - 1))]
            if WORLD_MAP[my][mx] == "1":
                row.append(f"{GREEN}{BOLD}{ch}{RESET}")
            else:
                row.append(f"{BLUE}{ch}{RESET}")
        lines.append("".join(row))
    return "\n".join(lines)
 
 
EARTH_FRAMES = [render_earth(i * (2 * math.pi / 36)) for i in range(36)]
 
# ---------------------------------------------------------------- HTML ----
HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MANERA</title>
<style>
  :root { --bg:#070a10; --panel:#0f141c; --line:#202833; --txt:#e6edf3; --mut:#7d8896;
          --cy:#39d0e0; --pu:#c49bff; --gr:#3fb950; --ye:#e3b341; --bl:#2f81f7; }
  * { box-sizing: border-box; }
  html, body { margin:0; height:100%; background:var(--bg); color:var(--txt);
               font-family:'Courier New',Courier,monospace; overflow-x:hidden; }
  #stars { position:fixed; inset:0; z-index:0; }
  .wrap { position:relative; z-index:1; min-height:100%; display:flex;
          justify-content:center; align-items:center; padding:16px; }
  .terminal { width:100%; max-width:540px; background:rgba(15,20,28,.88);
              backdrop-filter:blur(6px); border:1px solid var(--line);
              border-radius:14px; padding:20px;
              box-shadow:0 0 40px rgba(57,208,224,.12);
              animation:rise .8s ease both; }
  @keyframes rise { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:none; } }
  .bar { display:flex; gap:8px; align-items:center; border-bottom:1px solid var(--line);
         padding-bottom:10px; margin-bottom:14px; }
  .dot { width:12px; height:12px; border-radius:50%; }
  .r{background:#ff5f56}.y{background:#ffbd2e}.g{background:#27c93f}
  .bar span { margin-left:auto; color:var(--mut); font-size:12px; }
  pre { margin:0; }
  #logo { font-size:11px; line-height:1.1; font-weight:bold; text-align:center;
          animation:hue 4s infinite alternate; }
  @keyframes hue { 0%{color:#00ffff;text-shadow:0 0 10px #0ff6}
                   50%{color:#58a6ff;text-shadow:0 0 10px #58a6ff66}
                   100%{color:#d2a8ff;text-shadow:0 0 10px #d2a8ff66} }
  #earth { font-size:13px; line-height:1.05; text-align:center; margin:10px 0 16px; letter-spacing:1px; }
  .land { color:var(--gr); font-weight:bold; } .ocean { color:var(--bl); }
  .typed { min-height:20px; color:var(--cy); font-size:14px; margin-bottom:12px; }
  .typed::after { content:'▌'; animation:blink 1s steps(1) infinite; }
  @keyframes blink { 50% { opacity:0; } }
  .links { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px; }
  .btn { display:block; text-decoration:none; text-align:center; padding:12px 8px;
         border-radius:10px; border:1px solid var(--line); background:#0b1017;
         color:var(--txt); font-weight:bold; font-size:14px;
         transition:transform .15s, box-shadow .15s, border-color .15s; }
  .btn small { display:block; color:var(--mut); font-weight:normal; margin-top:3px; font-size:11px; }
  .btn:hover { transform:translateY(-3px); }
  .tg:hover { border-color:var(--cy); box-shadow:0 6px 20px rgba(57,208,224,.25); }
  .tt:hover { border-color:var(--pu); box-shadow:0 6px 20px rgba(196,155,255,.25); }
  .stats { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
  .stat { background:#0b1017; border:1px solid var(--line); border-radius:10px; padding:10px 12px; font-size:13px; }
  .stat b { display:block; font-size:18px; margin-top:4px; }
  .btc b { color:var(--ye); } .clk b { color:var(--gr); }
  .flash { animation:flash .8s; }
  @keyframes flash { 0%{color:#fff;text-shadow:0 0 12px var(--ye)} 100%{} }
  .foot { margin-top:14px; border-top:1px dashed var(--line); padding-top:10px;
          font-size:11px; color:var(--mut); text-align:center; }
</style>
</head>
<body>
<canvas id="stars"></canvas>
<div class="wrap"><div class="terminal">
  <div class="bar"><div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
    <span>~ $ curl manera</span></div>
  <pre id="logo">__LOGO__</pre>
  <pre id="earth"></pre>
  <div class="typed" id="typed"></div>
  <div class="links">
    <a class="btn tg" href="__TG__" target="_blank" rel="noopener">✈ Telegram<small>@__TGU__</small></a>
    <a class="btn tt" href="__TT__" target="_blank" rel="noopener">♪ TikTok<small>@__TTU__</small></a>
  </div>
  <div class="stats">
    <div class="stat btc">₿ Bitcoin<b id="btc">__BTC__</b></div>
    <div class="stat clk">⌚ Время BY<b id="clock">--:--:--</b></div>
  </div>
  <div class="foot">tip: <code>curl этот-адрес</code> в терминале — там тоже анимация</div>
</div></div>
 
<script>
const worldMap = __MAP__;
const shade = " .:-=+*#%@";
let angle = 0;
 
function renderEarth() {
  const R = 7, H = worldMap.length, W = worldMap[0].length;
  let out = "";
  for (let y = -R; y <= R; y++) {
    const ny = y / R;
    for (let x = -R * 2; x <= R * 2; x++) {
      const nx = x / (R * 2), r2 = nx * nx + ny * ny;
      if (r2 > 1) { out += " "; continue; }
      const nz = Math.sqrt(1 - r2);
      const lat = Math.asin(Math.max(-1, Math.min(1, -ny)));
      const lon = Math.atan2(nx, nz) + angle;
      const u = ((lon / (2 * Math.PI)) % 1 + 1) % 1;
      const v = 0.5 - lat / Math.PI;
      const mx = Math.floor(u * W) % W;
      const my = Math.min(H - 1, Math.max(0, Math.floor(v * H)));
      const light = Math.max(.15, Math.min(1, nx * -.4 + ny * -.3 + nz * .85));
      const ch = shade[Math.floor(light * (shade.length - 1))];
      out += `<span class="${worldMap[my][mx] === "1" ? "land" : "ocean"}">${ch}</span>`;
    }
    out += "\n";
  }
  document.getElementById("earth").innerHTML = out;
  angle += 0.12;
}
setInterval(renderEarth, 100); renderEarth();
 
function tick() {
  document.getElementById("clock").textContent =
    new Date().toLocaleTimeString("ru-RU", { timeZone: "Europe/Minsk", hour12: false });
}
setInterval(tick, 1000); tick();
 
async function refreshBtc() {
  try {
    const r = await fetch("/api/btc", { cache: "no-store" });
    const d = await r.json();
    const el = document.getElementById("btc");
    if (el.textContent !== d.text) {
      el.textContent = d.text;
      el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash");
    }
  } catch (e) {}
}
setInterval(refreshBtc, 30000);
 
const phrases = ["> connecting to MANERA...", "> globe online ✔", "> welcome, traveller", "> pick a link below ↓"];
let pi = 0, ci = 0, del = false;
function type() {
  const el = document.getElementById("typed"), p = phrases[pi];
  el.textContent = p.slice(0, ci);
  if (!del && ci < p.length) { ci++; setTimeout(type, 55); }
  else if (!del) { del = true; setTimeout(type, 1400); }
  else if (ci > 0) { ci--; setTimeout(type, 25); }
  else { del = false; pi = (pi + 1) % phrases.length; setTimeout(type, 300); }
}
type();
 
const cv = document.getElementById("stars"), cx = cv.getContext("2d");
let stars = [];
function resize() {
  cv.width = innerWidth; cv.height = innerHeight;
  stars = Array.from({ length: Math.min(220, Math.floor(cv.width * cv.height / 8000)) }, () => ({
    x: Math.random() * cv.width, y: Math.random() * cv.height,
    z: Math.random() * 1.5 + .3, p: Math.random() * 6.28 }));
}
addEventListener("resize", resize); resize();
(function loop(t) {
  cx.clearRect(0, 0, cv.width, cv.height);
  for (const s of stars) {
    s.y += s.z * .15; if (s.y > cv.height) { s.y = 0; s.x = Math.random() * cv.width; }
    cx.globalAlpha = .4 + .6 * Math.abs(Math.sin(t / 900 + s.p));
    cx.fillStyle = "#cfe8ff"; cx.fillRect(s.x, s.y, s.z, s.z);
  }
  requestAnimationFrame(loop);
})(0);
</script>
</body>
</html>"""
 
 
def build_html():
    return (HTML.replace("__LOGO__", LOGO)
                .replace("__TG__", TELEGRAM_URL).replace("__TGU__", TELEGRAM_USER)
                .replace("__TT__", TIKTOK_URL).replace("__TTU__", TIKTOK_USER)
                .replace("__BTC__", btc_text())
                .replace("__MAP__", json.dumps(WORLD_MAP)))
 
 
# -------------------------------------------------------------- server ----
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass
 
    def _send(self, code, ctype, body):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)
 
    def do_GET(self):
        path = self.path.split("?")[0]
 
        if path == "/healthz":
            return self._send(200, "text/plain", "ok")
        if path == "/api/btc":
            return self._send(200, "application/json", json.dumps({"text": btc_text()}))
        if path != "/":
            return self._send(404, "text/plain; charset=utf-8", "404 not found")
 
        if "curl" not in self.headers.get("User-Agent", "").lower():
            return self._send(200, "text/html; charset=utf-8", build_html())
 
        # curl: бесконечный ASCII-стрим
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        step = 0
        try:
            self.wfile.write(b"\033[?25l")
            while True:
                color = LOGO_COLORS[(step // 3) % len(LOGO_COLORS)]
                info = (
                    f"  {CYAN}✈ Telegram:{RESET}  {BOLD}@{TELEGRAM_USER}{RESET}  ({TELEGRAM_URL})\n"
                    f"  {MAGENTA}♪ TikTok:{RESET}    {BOLD}@{TIKTOK_USER}{RESET}  ({TIKTOK_URL})\n"
                    f"  {YELLOW}₿ Bitcoin:{RESET}   {BOLD}{btc_text()}{RESET}\n"
                    f"  {GREEN}⌚ Время BY:{RESET}  {minsk_time()}\n"
                )
                frame = (
                    "\033[2J\033[H"
                    f"{color}{LOGO}{RESET}\n"
                    f"{EARTH_FRAMES[step % len(EARTH_FRAMES)]}\n\n"
                    f"{info}\n{DIM}Ctrl+C — выход{RESET}\n"
                )
                self.wfile.write(frame.encode("utf-8"))
                self.wfile.flush()
                step += 1
                time.sleep(0.12)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
 
 
if __name__ == "__main__":
    threading.Thread(target=btc_worker, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.daemon_threads = True
    print(f"Server started on port {port}")
    server.serve_forever()
 
