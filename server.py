import json
import math
import mimetypes
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_EXT = (".mp3", ".ogg", ".wav", ".m4a", ".opus", ".flac")


def find_music():
    """Трек для фона: MUSIC_FILE, затем baldinini*.mp3, затем любой аудиофайл рядом со скриптом."""
    env = os.environ.get("MUSIC_FILE")
    if env and os.path.isfile(env):
        return env
    try:
        names = sorted(os.listdir(BASE_DIR))
    except OSError:
        return None
    pref = [n for n in names if n.lower().startswith("baldinini") and n.lower().endswith(AUDIO_EXT)]
    other = [n for n in names if n.lower().endswith(AUDIO_EXT)]
    for n in pref + other:
        return os.path.join(BASE_DIR, n)
    return None


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
<meta name="theme-color" content="#05070d">
<title>MANERA</title>
<style>
  @property --ang { syntax:'<angle>'; initial-value:0deg; inherits:false; }
  :root { --bg:#05070d; --panel:#0c1119; --line:#1e2733; --txt:#e6edf3; --mut:#7d8896;
          --cy:#39d0e0; --pu:#c49bff; --pk:#ff5ea8; --gr:#3fb950; --ye:#e3b341; --bl:#2f81f7;
          --pulse:0; }
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html,body { margin:0; height:100%; background:var(--bg); color:var(--txt);
              font-family:'Courier New',Courier,monospace; overflow-x:hidden; }
  body.locked { overflow:hidden; }

  /* ---------- фон ---------- */
  .nebula { position:fixed; inset:-20%; z-index:0; filter:blur(60px) saturate(1.3); opacity:.55;
            background:
              radial-gradient(40% 40% at 20% 30%, #1b6cff55, transparent 70%),
              radial-gradient(35% 35% at 80% 20%, #b44dff55, transparent 70%),
              radial-gradient(45% 45% at 60% 85%, #00e0c755, transparent 70%),
              radial-gradient(30% 30% at 10% 90%, #ff3d8155, transparent 70%);
            animation:drift 22s ease-in-out infinite alternate; }
  @keyframes drift { to { transform:translate3d(4%,-3%,0) rotate(8deg) scale(1.1); } }
  #fx { position:fixed; inset:0; z-index:1; pointer-events:none; }
  .scan { position:fixed; inset:0; z-index:50; pointer-events:none; opacity:.18;
          background:repeating-linear-gradient(0deg, transparent 0 2px, #000 2px 3px); }
  .vig { position:fixed; inset:0; z-index:49; pointer-events:none;
         background:radial-gradient(ellipse at center, transparent 55%, #000a 100%); }

  /* ---------- заставка ---------- */
  #intro { position:fixed; inset:0; z-index:100; display:flex; flex-direction:column;
           justify-content:center; align-items:center; gap:22px; background:#05070d;
           transition:opacity .9s ease, visibility .9s; cursor:pointer; text-align:center; padding:20px; }
  #intro.gone { opacity:0; visibility:hidden; }
  .glitch { position:relative; font-size:clamp(46px,14vw,110px); font-weight:bold; letter-spacing:.12em;
            color:#fff; text-shadow:0 0 24px #39d0e088; }
  .glitch::before,.glitch::after { content:attr(data-text); position:absolute; inset:0; overflow:hidden; }
  .glitch::before { color:#ff3d81; transform:translate(3px,0); clip-path:inset(0 0 55% 0); animation:gl1 2.4s infinite steps(1); }
  .glitch::after  { color:#39d0e0; transform:translate(-3px,0); clip-path:inset(55% 0 0 0); animation:gl2 2.1s infinite steps(1); }
  @keyframes gl1 { 0%{transform:translate(3px,0)} 20%{transform:translate(-4px,1px)} 40%{transform:translate(2px,-1px)} 60%{transform:translate(-2px,0)} 80%{transform:translate(5px,1px)} }
  @keyframes gl2 { 0%{transform:translate(-3px,0)} 25%{transform:translate(4px,-1px)} 50%{transform:translate(-5px,1px)} 75%{transform:translate(2px,0)} }
  .enter { color:var(--cy); font-size:16px; letter-spacing:.2em; animation:pulse 1.6s ease-in-out infinite; }
  @keyframes pulse { 50% { opacity:.35; } }
  .silent { color:var(--mut); font-size:12px; text-decoration:underline; background:none; border:0;
            font-family:inherit; cursor:pointer; padding:6px; }
  .silent:hover { color:var(--txt); }

  /* ---------- карточка ---------- */
  .wrap { position:relative; z-index:2; min-height:100%; display:flex; justify-content:center;
          align-items:center; padding:18px; perspective:1100px; }
  .tilt { width:100%; max-width:560px; transition:transform .12s ease-out; transform-style:preserve-3d; }
  .terminal { width:100%; border:1px solid transparent; border-radius:16px; padding:20px;
              background:linear-gradient(var(--panel),var(--panel)) padding-box,
                         conic-gradient(from var(--ang), var(--cy), var(--pu), var(--pk), var(--cy)) border-box;
              animation:spin 7s linear infinite;
              box-shadow:0 0 calc(30px + var(--pulse) * 50px) rgba(57,208,224,calc(.12 + var(--pulse) * .35));
              opacity:0; transform:translateY(24px); transition:opacity .9s .1s, transform .9s .1s; }
  body.in .terminal { opacity:1; transform:none; }
  @keyframes spin { to { --ang:360deg; } }
  .bar { display:flex; gap:8px; align-items:center; border-bottom:1px solid var(--line); padding-bottom:10px; margin-bottom:14px; }
  .dot { width:12px; height:12px; border-radius:50%; } .r{background:#ff5f56}.y{background:#ffbd2e}.g{background:#27c93f}
  .bar span { margin-left:auto; color:var(--mut); font-size:12px; }
  .live { display:inline-block; width:8px; height:8px; border-radius:50%; background:#27c93f; margin-right:6px;
          box-shadow:0 0 8px #27c93f; animation:pulse 1.4s infinite; }
  pre { margin:0; }
  #logo { font-size:11px; line-height:1.1; font-weight:bold; text-align:center;
          animation:hue 5s infinite alternate; transform:scale(calc(1 + var(--pulse) * .04)); transition:transform .08s; }
  @keyframes hue { 0%{color:#0ff;text-shadow:0 0 12px #0ff8} 50%{color:#58a6ff;text-shadow:0 0 12px #58a6ff88} 100%{color:#d2a8ff;text-shadow:0 0 12px #d2a8ff88} }
  #earth { font-size:13px; line-height:1.05; text-align:center; margin:10px 0 14px; letter-spacing:1px; }
  .land { color:var(--gr); font-weight:bold; } .ocean { color:var(--bl); }
  .typed { min-height:20px; color:var(--cy); font-size:14px; margin-bottom:12px; text-align:center; }
  .typed::after { content:'▌'; animation:blink 1s steps(1) infinite; }
  @keyframes blink { 50% { opacity:0; } }

  .links { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px; }
  .btn { position:relative; overflow:hidden; display:block; text-decoration:none; text-align:center; padding:14px 8px;
         border-radius:12px; border:1px solid var(--line); background:#0a0f16; color:var(--txt);
         font-weight:bold; font-size:14px; transition:transform .18s, box-shadow .18s, border-color .18s; }
  .btn small { display:block; color:var(--mut); font-weight:normal; margin-top:3px; font-size:11px; }
  .btn::after { content:''; position:absolute; top:0; left:-120%; width:60%; height:100%;
                background:linear-gradient(100deg, transparent, #ffffff22, transparent); transform:skewX(-20deg); transition:left .6s; }
  .btn:hover::after { left:140%; }
  .btn:hover { transform:translateY(-4px) scale(1.02); }
  .tg:hover { border-color:var(--cy); box-shadow:0 8px 26px rgba(57,208,224,.3); }
  .tt:hover { border-color:var(--pu); box-shadow:0 8px 26px rgba(196,155,255,.3); }

  .stats { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px; }
  .stat { background:#0a0f16; border:1px solid var(--line); border-radius:12px; padding:10px 12px; font-size:12px; color:var(--mut); }
  .stat b { display:block; font-size:20px; margin-top:4px; }
  .btc b { color:var(--ye); } .clk b { color:var(--gr); }
  .flash { animation:flash .9s; } @keyframes flash { 0%{color:#fff;text-shadow:0 0 14px var(--ye)} }

  .player { background:#0a0f16; border:1px solid var(--line); border-radius:12px; padding:10px 12px; }
  .np { font-size:11px; color:var(--mut); margin-bottom:6px; display:flex; justify-content:space-between; gap:8px; }
  .np b { color:var(--pk); font-weight:normal; }
  #eq { width:100%; height:56px; display:block; }
  .ctrl { display:flex; align-items:center; gap:10px; margin-top:8px; }
  .pbtn { background:#111823; color:var(--txt); border:1px solid var(--line); border-radius:8px; width:38px; height:32px;
          font-size:15px; cursor:pointer; font-family:inherit; }
  .pbtn:hover { border-color:var(--cy); }
  input[type=range] { flex:1; accent-color:var(--cy); height:4px; }
  .foot { margin-top:12px; font-size:11px; color:var(--mut); text-align:center; }

  @media (max-width:420px) { #logo { font-size:9px; } #earth { font-size:11px; } }
  @media (prefers-reduced-motion:reduce) { .nebula,.terminal,.glitch::before,.glitch::after { animation:none; } }
</style>
</head>
<body class="locked">
<div class="nebula"></div>
<canvas id="fx"></canvas>
<div class="scan"></div><div class="vig"></div>

<div id="intro">
  <div class="glitch" data-text="MANERA">MANERA</div>
  <div class="enter">[ НАЖМИ, ЧТОБЫ ВОЙТИ ]</div>
  <button class="silent" id="mute-enter">войти без звука</button>
</div>

<div class="wrap"><div class="tilt" id="tilt"><div class="terminal">
  <div class="bar"><div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
    <span><i class="live"></i>online · ~ $ curl manera</span></div>
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

  <div class="player">
    <div class="np"><span>♪ <b id="np-title">MANERA — live synthwave</b></span><span id="state">пауза</span></div>
    <canvas id="eq" width="520" height="56"></canvas>
    <div class="ctrl">
      <button class="pbtn" id="play" title="Играть / пауза">▶</button>
      <input type="range" id="vol" min="0" max="100" value="55" aria-label="Громкость">
      <span id="volv" style="font-size:11px;color:var(--mut);width:34px;text-align:right">55%</span>
    </div>
  </div>
  <div class="foot">музыка генерируется прямо в браузере · <code>curl</code> в терминале тоже даёт анимацию</div>
</div></div></div>

<audio id="track" loop preload="auto"></audio>
<script>
const worldMap = __MAP__;
const $ = id => document.getElementById(id);

/* ---------- глобус ---------- */
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
      const l = Math.max(.15, Math.min(1, nx * -.4 + ny * -.3 + nz * .85));
      out += `<span class="${worldMap[my][mx] === "1" ? "land" : "ocean"}">${shade[Math.floor(l * (shade.length - 1))]}</span>`;
    }
    out += "\n";
  }
  $("earth").innerHTML = out;
  angle += 0.12;
}
setInterval(renderEarth, 100); renderEarth();

/* ---------- часы и биткоин ---------- */
function tick() {
  $("clock").textContent = new Date().toLocaleTimeString("ru-RU", { timeZone: "Europe/Minsk", hour12: false });
}
setInterval(tick, 1000); tick();
async function refreshBtc() {
  try {
    const d = await (await fetch("/api/btc", { cache: "no-store" })).json();
    const el = $("btc");
    if (el.textContent !== d.text) { el.textContent = d.text; el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
  } catch (e) {}
}
setInterval(refreshBtc, 30000);

/* ---------- печатающаяся строка ---------- */
const phrases = ["> connecting to MANERA...", "> globe online ✔", "> добро пожаловать", "> выбирай ссылку ↓", "> музыка играет ♪"];
let pi = 0, ci = 0, del = false;
function type() {
  const p = phrases[pi]; $("typed").textContent = p.slice(0, ci);
  if (!del && ci < p.length) { ci++; setTimeout(type, 55); }
  else if (!del) { del = true; setTimeout(type, 1500); }
  else if (ci > 0) { ci--; setTimeout(type, 22); }
  else { del = false; pi = (pi + 1) % phrases.length; setTimeout(type, 300); }
}
type();

/* ---------- фон: звёзды + след курсора + клики ---------- */
const cv = $("fx"), cx = cv.getContext("2d");
let stars = [], parts = [], mx = 0, my = 0, pmx = 0, pmy = 0;

/* ---------- «матричный» дождь из иероглифов ---------- */
const GLY = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ日月火水木金土0123456789";
const FS = 16;
let cols = [];
const rg = () => GLY[(Math.random() * GLY.length) | 0];
function newCol(x, y) {
  return { x, y, sp: .12 + Math.random() * .3, len: 8 + ((Math.random() * 20) | 0),
           ch: Array.from({ length: 64 }, rg) };
}
function initRain() {
  const n = Math.ceil(cv.width / FS);
  cols = Array.from({ length: n }, (_, i) => newCol(i * FS, -Math.random() * cv.height / FS));
}
function drawRain() {
  const rows = cv.height / FS;
  cx.font = FS + "px monospace"; cx.textBaseline = "top";
  for (const c of cols) {
    c.y += c.sp * (1 + bass * 2.5);
    const head = Math.floor(c.y);
    if (head - c.len > rows) { Object.assign(c, newCol(c.x, -Math.random() * rows * .5)); continue; }
    if (Math.random() < .05) c.ch[(Math.random() * 64) | 0] = rg();
    for (let k = 0; k < c.len; k++) {
      const row = head - k;
      if (row < 0 || row > rows) continue;
      cx.globalAlpha = k === 0 ? .95 : .5 * (1 - k / c.len);
      cx.fillStyle = k === 0 ? "#eafff3" : (k < 3 ? "#5dffa0" : "#12b45a");
      cx.fillText(c.ch[((row % 64) + 64) % 64], c.x, row * FS);
    }
  }
  cx.globalAlpha = 1;
}

function resize() {
  cv.width = innerWidth; cv.height = innerHeight;
  stars = Array.from({ length: Math.min(260, Math.floor(cv.width * cv.height / 7000)) }, () => ({
    x: Math.random() * cv.width, y: Math.random() * cv.height,
    z: Math.random() * 1.6 + .3, p: Math.random() * 6.28 }));
  initRain();
}
addEventListener("resize", resize); resize();
const hues = [185, 270, 330];
function burst(x, y, n, speed) {
  for (let i = 0; i < n; i++) {
    const a = Math.random() * 6.283, s = Math.random() * speed;
    parts.push({ x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: 1, h: hues[(Math.random() * 3) | 0] });
  }
}
addEventListener("pointermove", e => {
  pmx = mx; pmy = my; mx = e.clientX; my = e.clientY;
  burst(mx, my, 1, .8);
  const tl = $("tilt");
  tl.style.transform = `rotateX(${((my / innerHeight) - .5) * -9}deg) rotateY(${((mx / innerWidth) - .5) * 11}deg)`;
});
addEventListener("pointerdown", e => burst(e.clientX, e.clientY, 26, 4.5));
let bass = 0;
function loop(t) {
  cx.clearRect(0, 0, cv.width, cv.height);
  drawRain();
  const ox = (mx - cv.width / 2) * .012, oy = (my - cv.height / 2) * .012;
  for (const s of stars) {
    s.y += s.z * (.15 + bass * 1.2); if (s.y > cv.height) { s.y = 0; s.x = Math.random() * cv.width; }
    cx.globalAlpha = .35 + .65 * Math.abs(Math.sin(t / 900 + s.p));
    cx.fillStyle = "#cfe8ff";
    cx.fillRect(s.x - ox * s.z, s.y - oy * s.z, s.z + bass * 1.2, s.z + bass * 1.2);
  }
  for (let i = parts.length - 1; i >= 0; i--) {
    const p = parts[i]; p.x += p.vx; p.y += p.vy; p.vy += .03; p.life -= .02;
    if (p.life <= 0) { parts.splice(i, 1); continue; }
    cx.globalAlpha = p.life; cx.fillStyle = `hsl(${p.h} 100% 65%)`;
    cx.beginPath(); cx.arc(p.x, p.y, 1.2 + p.life * 2, 0, 6.283); cx.fill();
  }
  cx.globalAlpha = 1;
  drawEq(t);
  requestAnimationFrame(loop);
}
/* запуск после полной инициализации скрипта (иначе TDZ-ошибка на const/let ниже) */
addEventListener("load", () => requestAnimationFrame(loop));

/* ---------- музыка (Web Audio, синтез в реальном времени) ---------- */
let ac, master, bus, dbus, analyser, noiseBuf, schedTimer, playing = false, started = false;
let vol = .55, nextBar = 0, barIdx = 0, useFile = false, mediaSrc = null;
const musicReady = fetch("/api/music", { cache: "no-store" }).then(r => r.json()).then(j => {
  if (j.has) { useFile = true; $("track").src = "/music"; $("np-title").textContent = j.title.toUpperCase(); }
}).catch(() => {});
const BPM = 96, beat = 60 / BPM, bar = beat * 4;
const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
const PADS = [[57, 60, 64], [53, 57, 60], [60, 64, 67], [55, 59, 62]];
const ROOTS = [45, 41, 48, 43];
const ARP = [0, 1, 2, 1, 0, 1, 2, 4];

function impulse(sec) {
  const r = ac.sampleRate, l = r * sec, b = ac.createBuffer(2, l, r);
  for (let c = 0; c < 2; c++) { const d = b.getChannelData(c); for (let i = 0; i < l; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / l, 2.6); }
  return b;
}
function tone(o) {
  const osc = ac.createOscillator(), g = ac.createGain(), fl = ac.createBiquadFilter();
  osc.type = o.type; osc.frequency.value = o.f; if (o.det) osc.detune.value = o.det;
  fl.type = "lowpass"; fl.frequency.value = o.lp || 2000; fl.Q.value = o.q || .7;
  const a = o.a || .01, r = o.r || .1;
  g.gain.setValueAtTime(0, o.t);
  g.gain.linearRampToValueAtTime(o.v, o.t + a);
  g.gain.setValueAtTime(o.v, o.t + Math.max(a, o.d));
  g.gain.linearRampToValueAtTime(0, o.t + o.d + r);
  osc.connect(fl); fl.connect(g); g.connect(o.out || bus);
  osc.start(o.t); osc.stop(o.t + o.d + r + .05);
}
function kick(t) {
  const o = ac.createOscillator(), g = ac.createGain();
  o.frequency.setValueAtTime(130, t); o.frequency.exponentialRampToValueAtTime(42, t + .16);
  g.gain.setValueAtTime(.9, t); g.gain.exponentialRampToValueAtTime(.001, t + .35);
  o.connect(g); g.connect(dbus); o.start(t); o.stop(t + .4);
}
function hat(t, v) {
  const s = ac.createBufferSource(), f = ac.createBiquadFilter(), g = ac.createGain();
  s.buffer = noiseBuf; f.type = "highpass"; f.frequency.value = 7500;
  g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(.001, t + .06);
  s.connect(f); f.connect(g); g.connect(dbus); s.start(t, Math.random() * .5); s.stop(t + .08);
}
function snare(t) {
  const s = ac.createBufferSource(), f = ac.createBiquadFilter(), g = ac.createGain();
  s.buffer = noiseBuf; f.type = "bandpass"; f.frequency.value = 1800; f.Q.value = .8;
  g.gain.setValueAtTime(.35, t); g.gain.exponentialRampToValueAtTime(.001, t + .22);
  s.connect(f); f.connect(g); g.connect(bus); g.connect(dbus); s.start(t, Math.random() * .5); s.stop(t + .25);
}
function playBar(t, i) {
  const pad = PADS[i], root = ROOTS[i], sweep = 900 + 700 * Math.sin(barIdx * .5);
  pad.forEach(n => {
    tone({ type: "sawtooth", f: mtof(n), t, d: bar * .96, v: .045, lp: sweep, a: .7, r: 1.2, det: -9 });
    tone({ type: "sawtooth", f: mtof(n), t, d: bar * .96, v: .045, lp: sweep, a: .7, r: 1.2, det: 9 });
  });
  for (let k = 0; k < 8; k++) {
    const bt = t + k * beat / 2;
    tone({ type: "sawtooth", f: mtof(root), t: bt, d: beat / 2 * .8, v: k % 2 ? .13 : .2, lp: 420, a: .005, r: .08, out: dbus });
    const n = (k < 7 ? pad[ARP[k] % 3] : pad[1]) + 12 + (ARP[k] > 2 ? 12 : 0);
    tone({ type: "triangle", f: mtof(n), t: bt, d: beat / 2 * .7, v: .07, lp: 3200, a: .005, r: .25 });
  }
  for (let b = 0; b < 4; b++) {
    kick(t + b * beat);
    hat(t + b * beat + beat / 2, .1);
    if (b === 1 || b === 3) snare(t + b * beat);
  }
  for (let k = 0; k < 8; k += 2) hat(t + k * beat / 2 + beat / 4, .035);
}
function sched() {
  while (nextBar < ac.currentTime + 1.4) { playBar(nextBar, barIdx % 4); nextBar += bar; barIdx++; }
}
function initAudio() {
  if (ac) return;
  ac = new (window.AudioContext || window.webkitAudioContext)();
  const comp = ac.createDynamicsCompressor();
  master = ac.createGain(); master.gain.value = 0;
  analyser = ac.createAnalyser(); analyser.fftSize = 128; analyser.smoothingTimeConstant = .8;
  const conv = ac.createConvolver(); conv.buffer = impulse(2.8);
  const wet = ac.createGain(); wet.gain.value = .45;
  bus = ac.createGain(); dbus = ac.createGain();
  bus.connect(conv); bus.connect(comp); conv.connect(wet); wet.connect(comp); dbus.connect(comp);
  comp.connect(master); master.connect(analyser); analyser.connect(ac.destination);
  mediaSrc = ac.createMediaElementSource($("track")); mediaSrc.connect(dbus);
  noiseBuf = ac.createBuffer(1, ac.sampleRate, ac.sampleRate);
  const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
}
function play() {
  initAudio(); ac.resume();
  if (useFile) { $("track").play().catch(() => {}); }
  else {
    if (!started) { nextBar = ac.currentTime + .15; started = true; }
    clearInterval(schedTimer); schedTimer = setInterval(sched, 250); sched();
  }
  master.gain.cancelScheduledValues(ac.currentTime);
  master.gain.setValueAtTime(master.gain.value, ac.currentTime);
  master.gain.linearRampToValueAtTime(vol, ac.currentTime + 2.5);
  playing = true; $("play").textContent = "❚❚"; $("state").textContent = "играет";
}
function pause() {
  if (!ac) return;
  master.gain.cancelScheduledValues(ac.currentTime);
  master.gain.setValueAtTime(master.gain.value, ac.currentTime);
  master.gain.linearRampToValueAtTime(0, ac.currentTime + .6);
  clearInterval(schedTimer);
  setTimeout(() => { if (!playing) { $("track").pause(); ac.suspend(); started = false; } }, 800);
  playing = false; $("play").textContent = "▶"; $("state").textContent = "пауза";
}
$("play").onclick = () => playing ? pause() : play();
$("vol").oninput = e => {
  vol = e.target.value / 100; $("volv").textContent = e.target.value + "%";
  if (ac && playing) master.gain.setTargetAtTime(vol, ac.currentTime, .05);
};

/* ---------- эквалайзер + реакция на бас ---------- */
const eq = $("eq"), ex = eq.getContext("2d");
function drawEq(t) {
  const w = eq.width, h = eq.height, n = 36, bw = w / n;
  ex.clearRect(0, 0, w, h);
  let data = null;
  if (analyser && playing) { data = new Uint8Array(analyser.frequencyBinCount); analyser.getByteFrequencyData(data); }
  const g = ex.createLinearGradient(0, h, 0, 0);
  g.addColorStop(0, "#39d0e0"); g.addColorStop(.6, "#c49bff"); g.addColorStop(1, "#ff5ea8");
  ex.fillStyle = g;
  for (let i = 0; i < n; i++) {
    const v = data ? data[Math.min(63, Math.floor(i * 1.5))] / 255 : .06 + .04 * Math.sin(t / 400 + i * .6);
    const bh = Math.max(2, v * h);
    ex.fillRect(i * bw + 1, h - bh, bw - 2, bh);
  }
  let b = 0;
  if (data) { b = (data[0] + data[1] + data[2] + data[3]) / (4 * 255); b = Math.pow(b, 2.2); }
  bass += (b - bass) * .25;
  document.documentElement.style.setProperty("--pulse", bass.toFixed(3));
}

/* ---------- вход ---------- */
function enter(withSound) {
  $("intro").classList.add("gone");
  document.body.classList.remove("locked");
  setTimeout(() => document.body.classList.add("in"), 150);
  burst(innerWidth / 2, innerHeight / 2, 80, 7);
  if (withSound) { initAudio(); ac.resume(); musicReady.then(play); }
}
$("intro").addEventListener("click", e => { if (e.target.id !== "mute-enter") enter(true); });
$("mute-enter").addEventListener("click", e => { e.stopPropagation(); enter(false); });
document.addEventListener("visibilitychange", () => { if (ac && playing) { document.hidden ? ac.suspend() : ac.resume(); } });
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

    def _serve_music(self):
        f = find_music()
        if not f:
            return self._send(404, "text/plain", "no music file")
        size = os.path.getsize(f)
        start, end, code = 0, size - 1, 200
        rng = self.headers.get("Range", "")
        if rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            try:
                start = int(a) if a else 0
                end = int(b) if b else size - 1
                code = 206
            except ValueError:
                start, end, code = 0, size - 1, 200
        end = min(end, size - 1)
        if start > end:
            return self._send(416, "text/plain", "bad range")
        ctype = mimetypes.guess_type(f)[0] or "audio/mpeg"
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        try:
            with open(f, "rb") as fh:
                fh.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = fh.read(min(65536, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/healthz":
            return self._send(200, "text/plain", "ok")
        if path == "/api/btc":
            return self._send(200, "application/json", json.dumps({"text": btc_text()}))
        if path == "/api/music":
            f = find_music()
            title = os.path.splitext(os.path.basename(f))[0] if f else ""
            return self._send(200, "application/json",
                              json.dumps({"has": bool(f), "title": title}, ensure_ascii=False))
        if path == "/music":
            return self._serve_music()
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
