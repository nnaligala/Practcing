#!/usr/bin/env python3
"""Toon Tunes 2.0 - a friendly nursery-rhyme website for little singers.

Run:   python3 toon_tunes.py
Open:  http://localhost:8000

Optional environment variables:  PORT (default 8000)   TOON_HOST (default 127.0.0.1)
No external files, fonts, trackers or ads: everything is served from this one file.
"""

import json
import os
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


# --------------------------------------------------------------------------- #
#  Content
# --------------------------------------------------------------------------- #
def _item(item_id, title, emoji, cat, color, text):
    return {
        "id": item_id,
        "title": title,
        "emoji": emoji,
        "cat": cat,  # animals | adventure | bedtime | songs
        "color": color,
        "lines": text.split("\n"),
    }


ITEMS = [
    _item("bouncy-bunny", "Bouncy Bunny", "🐰", "animals", "#ffd6e7",
          "Bouncy bunny hops so high,\nWaving at the clouds nearby!\nHop, hop, hop and spin around,\nHappy giggles fill the ground!"),
    _item("rocket-cat", "Rocket Cat", "🐱", "adventure", "#d8e8ff",
          "Rocket cat goes zoom, zoom, zoom,\nFlying past the moon so bright.\nStars all twinkle in the night,\nWhat a super space delight!"),
    _item("dancing-dino", "Dancing Dino", "🦕", "animals", "#d9f7df",
          "Dancing dino taps his toes,\nWiggles fingers, shakes his nose.\nStomp, stomp, stomp across the floor,\nThen he dances out the door!"),
    _item("sunny-puppy", "Sunny Puppy", "🐶", "animals", "#fff0b8",
          "Sunny puppy wags his tail,\nChasing butterflies along the trail.\nRun, run, run beneath the sun,\nEvery day is full of fun!"),
    _item("jolly-jellyfish", "Jolly Jellyfish", "🪼", "animals", "#e5d5ff",
          "Jolly jellyfish sways below,\nDancing where the bubbles go.\nBlink, blink, sparkle blue,\nOcean friends are waving too!"),
    _item("merry-monkey", "Merry Monkey", "🐵", "animals", "#d5f4e6",
          "Merry monkey climbs a tree,\nPeeks down laughing, 'Look at me!'\nSwing, swing, from vine to vine,\nJungle playtime feels just fine!"),
    _item("twinkly-owl", "Twinkly Owl", "🦉", "bedtime", "#ffe0c2",
          "Twinkly owl flies through the night,\nGuided by the moonbeam light.\nHoot, hoot, soft and slow,\nDreamy little stars all glow!"),
    _item("busy-bee", "Busy Bee", "🐝", "animals", "#fff3b0",
          "Busy bee goes buzz, buzz, buzz,\nVisiting flowers, just because.\nHoney sweet and sunshine gold,\nHome she hums with stories told!"),
    _item("tall-giraffe", "Tickly Giraffe", "🦒", "animals", "#ffe8c7",
          "Tall giraffe tickles the trees,\nSneezes leaves upon the breeze.\nAh-choo, ah-choo, what a sound,\nLeaves go dancing all around!"),
    _item("brave-train", "Brave Little Train", "🚂", "adventure", "#cfe9ff",
          "Choo, choo, choo, the little train,\nRumbles over hill and plain.\nUp the mountain, down the track,\nBravely going there and back!"),
    _item("pirate-penguin", "Pirate Penguin", "🐧", "adventure", "#d6ecf7",
          "Pirate penguin sails the sea,\nWaddles on the deck with glee.\nAhoy, ahoy, hip hip hooray,\nFish for supper every day!"),
    _item("sleepy-sheep", "Sleepy Sheep", "🐑", "bedtime", "#e6e0ff",
          "Sleepy sheep count one, two, three,\nFluffy clouds above the tree.\nYawn, yawn, close your eyes,\nDream beneath the starry skies."),
    _item("goodnight-bear", "Goodnight Bear", "🐻", "bedtime", "#f3dcc8",
          "Little bear tiptoes to bed,\nSoft blue blanket, pillow head.\nMoon says shhh, the stars say hush,\nSnuggle up, all cozy and plush."),
    _item("friendship-song", "The Friendship Song", "🎶", "songs", "#ffdfc4",
          "Clap your hands and tap your feet,\nFriends together make a beat!\nSmile and sing, come along,\nEveryone can join this song!"),
    _item("rainbow-ride", "Rainbow Ride", "🌈", "songs", "#d4f0ff",
          "Red and orange, yellow too,\nGreen and blue and purple hue.\nSing along and reach up high,\nRide a rainbow through the sky!"),
    _item("tidy-up-time", "Tidy-Up Time", "🧸", "songs", "#e2f5d3",
          "Toys go home, one by one,\nTidy-up time is lots of fun!\nBlocks in the box and books on the shelf,\nProud of you and proud of myself!"),
    _item("good-morning-sun", "Good Morning, Sun", "☀️", "songs", "#fff1a8",
          "Good morning, sun, wake up, wake up,\nStretch your arms like a buttercup.\nBrush your teeth and wash your face,\nGet ready for a happy day!"),
]

# JSON is embedded in the page. "<" is escaped so the data can never close the tag.
DATA_JSON = json.dumps(ITEMS).replace("<", "\\u003c")


# --------------------------------------------------------------------------- #
#  Page (HTML + CSS + JS). __NONCE__ and __DATA__ are filled in per request.
# --------------------------------------------------------------------------- #
PAGE = r"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Toon Tunes: nursery rhymes and sing-along songs that read aloud with a friendly voice.">
<meta name="theme-color" content="#6336c7">
<title>Toon Tunes - Rhymes and sing-along songs</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8E%B5%3C/text%3E%3C/svg%3E">
<script nonce="__NONCE__">
try{var t=JSON.parse(localStorage.getItem('tt.theme'));if(!t)t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';document.documentElement.dataset.theme=t}catch(e){}
</script>
<style nonce="__NONCE__">
*{box-sizing:border-box}
[hidden]{display:none!important}
:root{
  --bg1:#fff6cf;--bg2:#eadfff;--surface:#ffffff;--surface2:#f3edff;--text:#29234d;--muted:#5d5478;
  --brand:#6336c7;--on-brand:#ffffff;--coral:#d13d27;--on-coral:#ffffff;
  --hl:#ffe08a;--ring:#f59e0b;--shadow:0 10px 24px rgba(87,64,140,.16);
  --font:ui-rounded,"SF Pro Rounded","Baloo 2","Fredoka","Nunito","Trebuchet MS","Segoe UI",system-ui,sans-serif;
  color-scheme:light;
}
:root[data-theme=dark]{
  --bg1:#171331;--bg2:#2a1f5a;--surface:#251f4c;--surface2:#31296a;--text:#f5f0ff;--muted:#c7bcea;
  --brand:#b59bff;--on-brand:#1c1242;--coral:#ff8e78;--on-coral:#2b0e07;
  --hl:#5a49b0;--ring:#ffd166;--shadow:0 10px 24px rgba(0,0,0,.38);
  color-scheme:dark;
}
html{scroll-behavior:smooth}
body{margin:0;min-height:100vh;font-family:var(--font);font-size:1.05rem;color:var(--text);
  background:linear-gradient(135deg,var(--bg1),var(--bg2)) fixed;overflow-x:hidden}
body.has-bar{padding-bottom:96px}
body::before,body::after{content:"";position:fixed;border-radius:50%;opacity:.22;z-index:-1;pointer-events:none}
body::before{width:190px;height:190px;background:#ff8fbf;top:12%;left:3%}
body::after{width:250px;height:250px;background:#7fd6ff;right:2%;bottom:8%}
@media (prefers-reduced-motion:no-preference){
  body::before,body::after{animation:drift 9s ease-in-out infinite alternate}
  body::after{animation-delay:-4s}
}
@keyframes drift{to{transform:translate(35px,-25px) scale(1.15)}}
@keyframes bounce{to{transform:translateY(-10px) rotate(-5deg)}}
@keyframes pop{50%{transform:scale(1.25)}}

.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:12px;top:-60px;background:var(--brand);color:var(--on-brand);padding:10px 16px;border-radius:12px;z-index:50;font-weight:800}
.skip:focus{top:12px}
:focus-visible{outline:4px solid var(--ring);outline-offset:3px}

/* Header */
.top{position:relative;text-align:center;padding:48px 20px 20px}
h1{margin:0;color:var(--brand);font-size:clamp(2.6rem,9vw,5rem);line-height:1.05;letter-spacing:-.01em}
.logo{display:inline-block}
@media (prefers-reduced-motion:no-preference){.logo{animation:bounce .9s ease-in-out infinite alternate}.logo+.logo,h1 .logo:last-child{animation-delay:-.45s}}
.tagline{margin:10px auto 0;max-width:34ch;font-size:1.2rem;color:var(--muted)}
.top-actions{position:absolute;top:12px;right:14px;display:flex;gap:8px;align-items:center}
.pill{background:var(--surface);border-radius:999px;padding:8px 14px;font-weight:800;box-shadow:var(--shadow)}
.pill.bump{animation:pop .5s}
.icon-btn{width:46px;height:46px;border:0;border-radius:50%;background:var(--surface);color:var(--text);font-size:1.35rem;cursor:pointer;box-shadow:var(--shadow)}

main{max-width:1120px;margin:0 auto;padding:10px 18px 40px}
.notice{background:var(--surface);border-left:8px solid var(--coral);border-radius:14px;padding:12px 16px;margin:0 0 16px;box-shadow:var(--shadow)}

/* Voice panel */
.panel{background:var(--surface);border-radius:26px;padding:16px 20px;box-shadow:var(--shadow);display:flex;flex-wrap:wrap;gap:14px 28px;align-items:center;margin-bottom:22px}
.group{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.label{font-weight:800;margin-right:2px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{min-height:44px;border:2px solid transparent;border-radius:999px;background:var(--surface2);color:var(--text);padding:8px 16px;font:inherit;font-weight:700;cursor:pointer}
.chip:hover{border-color:var(--brand)}
.chip[aria-pressed=true]{background:var(--brand);color:var(--on-brand)}
select,input[type=search]{min-height:44px;border:2px solid var(--surface2);border-radius:14px;background:var(--surface);color:var(--text);font:inherit;padding:8px 12px;max-width:100%}
select:hover,input[type=search]:hover{border-color:var(--brand)}

/* Buttons */
.btn{min-height:46px;border:0;border-radius:999px;padding:10px 18px;font:inherit;font-weight:800;cursor:pointer;
  box-shadow:0 4px 0 rgba(0,0,0,.2);transition:transform .08s,box-shadow .08s}
.btn:active{transform:translateY(3px);box-shadow:0 1px 0 rgba(0,0,0,.2)}
.btn.primary{background:var(--brand);color:var(--on-brand)}
.btn.coral{background:var(--coral);color:var(--on-coral)}
.btn.ghost{background:var(--surface2);color:var(--text)}
.btn.big{font-size:1.25rem;padding:12px 28px}

/* Toolbar */
.toolbar{display:flex;flex-wrap:wrap;gap:12px 20px;justify-content:space-between;align-items:center;margin-bottom:8px}
.search-row{display:flex;gap:10px;flex-wrap:wrap}
.count{margin:6px 4px 14px;color:var(--muted);font-weight:700}

/* Cards */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:22px}
.card{position:relative;background:var(--surface);border-radius:26px;border-top:9px solid var(--accent);padding:22px 18px 20px;box-shadow:var(--shadow)}
.card.is-playing{outline:4px solid var(--brand);outline-offset:2px}
.avatar{width:92px;height:92px;margin:0 auto 8px;border-radius:50%;background:var(--accent);display:grid;place-items:center;font-size:3.1rem}
.is-playing .avatar{animation:bounce .6s ease-in-out infinite alternate}
h3{margin:6px 0 10px;text-align:center;color:var(--brand);font-size:1.4rem}
.poem{margin:0;text-align:center;line-height:1.45}
.line{display:block;padding:3px 10px;border-radius:12px;transition:background .2s}
.line.active{background:var(--hl);font-weight:800}
.actions{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-top:16px}
.fav{position:absolute;top:12px;right:12px;width:46px;height:46px;border:0;border-radius:50%;background:var(--surface2);font-size:1.35rem;cursor:pointer}
.fav[aria-pressed=true]{background:var(--hl)}
.empty{grid-column:1/-1;text-align:center;background:var(--surface);border-radius:26px;padding:32px 20px;box-shadow:var(--shadow)}

/* Now-playing bar */
.now{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));margin:0 auto;max-width:640px;z-index:20;
  display:flex;align-items:center;gap:10px;background:var(--surface);border:3px solid var(--brand);border-radius:999px;padding:8px 10px 8px 16px;box-shadow:var(--shadow)}
.now-emoji{font-size:2rem}
.now-text{flex:1;min-width:0;display:flex;flex-direction:column;line-height:1.2}
.now-text strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.now-text small{color:var(--muted)}

/* Sing-along stage */
dialog#stage{width:min(780px,94vw);max-height:94vh;padding:0;border:0;border-radius:34px;background:var(--surface);color:var(--text);box-shadow:0 20px 60px rgba(0,0,0,.4)}
dialog#stage::backdrop{background:rgba(24,16,60,.6);backdrop-filter:blur(4px)}
.stage-body{position:relative;border-top:12px solid var(--accent);padding:26px 22px 28px;text-align:center}
.stage-close{position:absolute;top:14px;right:14px}
.stage-emoji{width:132px;height:132px;margin:0 auto 6px;border-radius:50%;background:var(--accent);display:grid;place-items:center;font-size:4.8rem}
#stage[data-playing=true] .stage-emoji{animation:bounce .55s ease-in-out infinite alternate}
#stageTitle{margin:6px 0 14px;color:var(--brand);font-size:clamp(1.6rem,5vw,2.4rem)}
.stage-lines{display:grid;gap:6px;margin:0 auto;max-width:34ch}
.stage-lines .line{font-size:clamp(1.3rem,4.6vw,2rem);line-height:1.35;padding:6px 14px;border-radius:18px}
.stage-controls{display:flex;flex-wrap:wrap;justify-content:center;gap:12px;margin-top:24px}

/* Toast + confetti */
.toast{position:fixed;left:50%;bottom:110px;transform:translateX(-50%);max-width:90vw;z-index:1001;background:var(--text);color:var(--surface);
  padding:12px 20px;border-radius:999px;font-weight:800;text-align:center;box-shadow:var(--shadow)}
.confetti{position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:1000}

footer{text-align:center;padding:10px 20px 40px;color:var(--muted)}

@media (max-width:520px){
  .top{padding-top:70px}
  .panel{padding:14px}
  .now{border-radius:26px}
  .now .btn{padding:10px 12px}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the rhymes</a>

<header class="top">
  <div class="top-actions">
    <span class="pill" id="stars" role="img" aria-label="0 stars earned">⭐ 0</span>
    <button type="button" class="icon-btn" id="themeBtn" data-action="theme" aria-label="Switch to night mode">🌙</button>
  </div>
  <h1><span class="logo" aria-hidden="true">🎵</span> Toon Tunes <span class="logo" aria-hidden="true">🎨</span></h1>
  <p class="tagline">Sing, laugh, and rhyme along with our friendly cartoon crew!</p>
</header>

<main id="main">
  <noscript><p class="notice">Toon Tunes needs JavaScript to show the rhymes. Please turn it on and refresh. 🎈</p></noscript>
  <p class="notice" id="noVoice" hidden>This browser can't read aloud, but you can still sing along with the words! 🎤</p>

  <section class="panel" aria-labelledby="voiceHeading">
    <h2 class="sr-only" id="voiceHeading">Voice settings</h2>
    <div class="group"><span class="label" id="styleLbl">Style</span><div class="chips" id="styleChips" role="group" aria-labelledby="styleLbl"></div></div>
    <div class="group"><span class="label" id="voiceLbl">Voice</span><div class="chips" id="voiceChips" role="group" aria-labelledby="voiceLbl"></div></div>
    <div class="group"><span class="label" id="speedLbl">Speed</span><div class="chips" id="speedChips" role="group" aria-labelledby="speedLbl"></div></div>
    <div class="group">
      <label class="label" for="deviceVoice">Device voice</label>
      <select id="deviceVoice"><option value="">Automatic</option></select>
      <button type="button" class="btn ghost" data-action="test">🔊 Try voice</button>
    </div>
  </section>

  <section class="toolbar" aria-label="Find rhymes">
    <div class="chips" id="catChips" role="group" aria-label="Categories"></div>
    <div class="search-row">
      <label class="sr-only" for="search">Search rhymes</label>
      <input id="search" type="search" placeholder="Find a rhyme" autocomplete="off">
      <button type="button" class="btn coral" data-action="surprise">✨ Surprise me</button>
    </div>
  </section>
  <p class="count" id="count" aria-live="polite"></p>

  <h2 class="sr-only">Rhymes and songs</h2>
  <section class="grid" id="grid"></section>
</main>

<footer>Made for little imaginations. No ads, no tracking, works offline.</footer>

<div class="now" id="nowBar" role="region" aria-label="Now playing" hidden>
  <span class="now-emoji" id="nowEmoji" aria-hidden="true"></span>
  <div class="now-text"><strong id="nowTitle"></strong><small>Now singing</small></div>
  <button type="button" class="btn primary" id="nowBtn" data-action="toggle" data-play>⏸ Pause</button>
  <button type="button" class="btn ghost" data-action="stop">⏹ Stop</button>
</div>

<dialog id="stage" aria-labelledby="stageTitle">
  <div class="stage-body">
    <button type="button" class="icon-btn stage-close" data-action="close" aria-label="Close sing-along">✕</button>
    <div class="stage-emoji" id="stageEmoji" aria-hidden="true"></div>
    <h2 id="stageTitle"></h2>
    <div class="stage-lines" id="stageLines"></div>
    <div class="stage-controls">
      <button type="button" class="btn ghost" data-action="prev">⏮ Back</button>
      <button type="button" class="btn primary big" id="stagePlay" data-action="toggle" data-play>▶ Play</button>
      <button type="button" class="btn ghost" data-action="next">Next ⏭</button>
    </div>
  </div>
</dialog>

<p class="sr-only" id="live" aria-live="polite"></p>

<script id="data" type="application/json">__DATA__</script>
<script nonce="__NONCE__">
(() => {
'use strict';

/* ---------- helpers ---------- */
const ITEMS = JSON.parse(document.getElementById('data').textContent);
const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const byId = id => ITEMS.find(i => i.id === id);
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
const synth = 'speechSynthesis' in window ? window.speechSynthesis : null;

const store = {
  get(key, fallback) { try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); } catch { return fallback; } },
  set(key, value)    { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode */ } }
};

// Build DOM without innerHTML (safe, and works with our strict Content-Security-Policy).
function h(tag, props = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'className') el.className = v;
    else if (k === 'textContent') el.textContent = v;
    else if (k === 'dataset') Object.assign(el.dataset, v);
    else if (k === 'style') for (const [sk, sv] of Object.entries(v)) el.style.setProperty(sk, sv);
    else el.setAttribute(k, v);
  }
  el.append(...kids);
  return el;
}

/* ---------- options ---------- */
const PRESETS = {
  auto:  { label: '✨ Auto',   pitch: 1.1,  pref: null },
  girl:  { label: '👧 Girl',   pitch: 1.4,  pref: 'female' },
  boy:   { label: '👦 Boy',    pitch: 1.15, pref: 'male' },
  gents: { label: '🎩 Gents',  pitch: 0.55, pref: 'male' }
};
const SPEEDS = {   // rate = talking speed, bpm = beats per minute for the sing-song beat
  slow:   { label: '🐢 Slow',   rate: 0.7, bpm: 60 },
  normal: { label: '🚶 Normal', rate: 0.9, bpm: 72 },
  fast:   { label: '🐇 Fast',   rate: 1.1, bpm: 88 }
};
const STYLES = { music: '🎼 Sing + music', sing: '🎤 Sing-song', read: '📖 Read aloud' };
const CATS = { all: '🌈 All', animals: '🐾 Animals', adventure: '🚀 Adventure', bedtime: '🌙 Bedtime', songs: '🎶 Songs', favs: '❤️ Favorites' };

const settings = Object.assign({ voice: 'auto', speed: 'normal', device: '', style: 'music' }, store.get('tt.settings', {}));
const favs = new Set(store.get('tt.favs', []));
let stars = Number(store.get('tt.stars', 0)) || 0;
const view = { cat: 'all', query: '' };
const player = { id: null, index: 0, status: 'idle', token: 0, utterance: null };
let voices = [];
let stageId = null;
const warned = new Set();

const stage = $('#stage');

/* ---------- toast, stars, confetti ---------- */
let toastTimer;
function toast(message) {
  $('#live').textContent = message;
  $('.toast')?.remove();
  const el = h('div', { className: 'toast', textContent: message });
  (stage.open ? stage : document.body).append(el);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.remove(), 3200);
}

function renderStars(bump) {
  const el = $('#stars');
  el.textContent = '⭐ ' + stars;
  el.setAttribute('aria-label', stars + (stars === 1 ? ' star earned' : ' stars earned'));
  if (bump) { el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); }
}

function confetti() {
  if (reduceMotion.matches) return;
  const canvas = h('canvas', { className: 'confetti', 'aria-hidden': 'true' });
  canvas.width = innerWidth; canvas.height = innerHeight;
  const ctx = canvas.getContext && canvas.getContext('2d');
  if (!ctx) return;
  (stage.open ? stage : document.body).append(canvas);
  const glyphs = ['⭐', '🎉', '🎵', '✨', '💖', '🌈'];
  const bits = Array.from({ length: 38 }, () => ({
    x: Math.random() * canvas.width, y: -20 - Math.random() * canvas.height * 0.3,
    vx: (Math.random() - 0.5) * 2, vy: 2 + Math.random() * 3, size: 22 + Math.random() * 18,
    glyph: glyphs[(Math.random() * glyphs.length) | 0], rot: Math.random() * 6, spin: (Math.random() - 0.5) * 0.1
  }));
  let frames = 0;
  (function tick() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const b of bits) {
      b.x += b.vx; b.y += b.vy; b.vy += 0.04; b.rot += b.spin;
      ctx.save(); ctx.translate(b.x, b.y); ctx.rotate(b.rot);
      ctx.font = b.size + 'px serif'; ctx.fillText(b.glyph, 0, 0); ctx.restore();
    }
    if (++frames < 150) requestAnimationFrame(tick); else canvas.remove();
  })();
}

/* ---------- theme ---------- */
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const btn = $('#themeBtn');
  btn.textContent = theme === 'dark' ? '☀️' : '🌙';
  btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to day mode' : 'Switch to night mode');
}

/* ---------- voices ---------- */
const FEMALE = /female|woman|girl|zira|samantha|karen|victoria|susan|hazel|aria|jenny|moira|tessa|fiona|heera|neerja|veena|lekha|kalpana/i;
const MALE   = /(^|[^a-z])male|david|daniel|mark|alex|fred|george|guy|ryan|james|thomas|rishi|ravi|prabhat|hemant/i;

function loadVoices() {
  if (!synth) return;
  voices = synth.getVoices();
  const english = voices.filter(v => /^en/i.test(v.lang));
  const shown = english.length ? english : voices;
  const select = $('#deviceVoice');
  select.replaceChildren(
    h('option', { value: '', textContent: 'Automatic' }),
    ...shown.map(v => h('option', { value: v.voiceURI, textContent: v.name + ' (' + v.lang + ')' }))
  );
  select.value = settings.device;
  if (select.selectedIndex < 0) select.value = '';
}

function pickVoice(pref) {
  const english = voices.filter(v => /^en/i.test(v.lang));
  const pool = english.length ? english : voices;
  if (!pool.length) return null;
  if (pref === 'female') return pool.find(v => FEMALE.test(v.name)) || null;
  if (pref === 'male')   return pool.find(v => MALE.test(v.name) && !FEMALE.test(v.name)) || null;
  return pool.find(v => v.default) || pool.find(v => /^en-(us|gb|in)/i.test(v.lang)) || pool[0];
}

function applyVoice(utterance) {
  const preset = PRESETS[settings.voice] || PRESETS.auto;
  utterance.pitch = preset.pitch;
  utterance.rate = (SPEEDS[settings.speed] || SPEEDS.normal).rate;
  let voice = voices.find(v => v.voiceURI === settings.device) || null;
  if (!voice) voice = pickVoice(preset.pref);
  if (voice) { utterance.voice = voice; utterance.lang = voice.lang; }
  else {
    utterance.lang = 'en-US';
    if (preset.pref && !warned.has(settings.voice)) {
      warned.add(settings.voice);
      toast('No ' + (preset.pref === 'female' ? 'girl' : 'boy') + ' voice on this device, so I changed the pitch instead.');
    }
  }
}

function previewVoice() {
  if (!synth) return toast("This browser can't read aloud.");
  resetPlayer();
  const u = new SpeechSynthesisUtterance("Hello, little friend! Let's sing together!");
  applyVoice(u);
  player.utterance = u;
  synth.speak(u);
}

/* ---------- singing: a steady beat, a simple tune, and a music-box backing ----------
   Browsers can only *speak*, so we make speech feel like singing:
   1. every line is split into short phrases,
   2. each phrase starts exactly on a beat (steady rhythm),
   3. each phrase gets a different pitch that follows a tune,
   4. the last phrase of a line is stretched out,
   5. a music box plays the tune + a gentle chord pattern underneath. */
const MELODY = [[0, 4, 7, 4], [7, 9, 7, 4], [4, 7, 9, 12], [12, 9, 7, 0]]; // semitones above C, one row per line
const CHORDS = [[60, 64, 67], [65, 69, 72], [67, 71, 74], [60, 64, 67]];     // C, F, G, C (MIDI note numbers)
const LEAD = 140;                                                            // ms: speech engines start a little late
const midi = m => 440 * Math.pow(2, (m - 69) / 12);
let audio = null;
const song = { t0: 0, beatMs: 830, next: 0, timer: null };

function ensureAudio() {
  if (audio) { if (audio.state === 'suspended') audio.resume(); return audio; }
  const AC = window.AudioContext || window.webkitAudioContext;
  try { audio = AC ? new AC() : null; } catch { audio = null; }
  return audio;
}

function tone(note, whenMs, { vol = 0.12, dur = 1.1, type = 'triangle' } = {}) {
  if (!audio) return;
  const t = audio.currentTime + Math.max(0, (whenMs - performance.now()) / 1000);
  const osc = audio.createOscillator();
  const gain = audio.createGain();
  osc.type = type;
  osc.frequency.value = midi(note);
  gain.gain.setValueAtTime(0.0001, t);
  gain.gain.exponentialRampToValueAtTime(vol, t + 0.012);
  gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  osc.connect(gain).connect(audio.destination);
  osc.start(t);
  osc.stop(t + dur + 0.05);
}

function playBeat(b, when) {
  const chord = CHORDS[Math.floor(b / 4) % CHORDS.length];
  if (b % 4 === 0) tone(chord[0] - 24, when, { vol: 0.17, dur: 1.7, type: 'sine' });   // deep root note
  if (b % 4 === 2) tone(chord[2] - 24, when, { vol: 0.10, dur: 1.2, type: 'sine' });   // fifth
  tone(chord[[0, 1, 2, 1][b % 4]], when, { vol: 0.06, dur: 0.9 });                    // music-box arpeggio
}

function startBeat() {
  stopBeat();
  song.beatMs = 60000 / (SPEEDS[settings.speed] || SPEEDS.normal).bpm;
  song.t0 = performance.now() + 200;
  song.next = 0;
  const pump = () => {
    while (song.t0 + song.next * song.beatMs < performance.now() + 250) {
      const b = song.next++;
      if (settings.style === 'music') playBeat(b, song.t0 + b * song.beatMs);
    }
  };
  pump();
  song.timer = setInterval(pump, 60);
}

function stopBeat() { clearInterval(song.timer); song.timer = null; }

// Run fn at the next beat (a little early, to make up for the speech engine's start-up delay).
function atNextBeat(fn, token) {
  const now = performance.now();
  const k = Math.max(0, Math.ceil((now + LEAD - song.t0) / song.beatMs));
  const at = song.t0 + k * song.beatMs;
  setTimeout(() => { if (token === player.token && player.status === 'playing') fn(); }, Math.max(0, at - LEAD - now));
}

function chunkLine(text) {
  const out = [];
  for (const part of text.match(/[^,;.!?]+[,;.!?]*/g) || [text]) {
    const words = part.trim().split(/\s+/).filter(Boolean);
    if (!words.length) continue;
    if (words.length > 3) {
      const cut = Math.ceil(words.length / 2);
      out.push(words.slice(0, cut).join(' '), words.slice(cut).join(' '));
    } else out.push(words.join(' '));
  }
  return out;
}

function singLine(token, item) {
  const line = player.index;
  const chunks = chunkLine(item.lines[line]);
  const preset = PRESETS[settings.voice] || PRESETS.auto;
  let c = 0;

  const singChunk = () => {
    const semi = MELODY[line % MELODY.length][c % 4];
    const last = c === chunks.length - 1;
    const u = new SpeechSynthesisUtterance(chunks[c]);
    applyVoice(u);
    u.pitch = Math.min(2, Math.max(0.2, preset.pitch * Math.pow(2, (semi - 5) / 14)));  // melody in the voice
    u.rate = Math.max(0.5, u.rate * (last ? 0.8 : 0.95));                                // stretch the line ending
    u.onstart = () => {
      if (token === player.token && settings.style === 'music') tone(72 + semi, performance.now(), { vol: 0.16, dur: last ? 1.5 : 0.8 });
    };
    u.onend = () => {
      if (token !== player.token) return;
      c++;
      if (c < chunks.length) atNextBeat(singChunk, token);
      else { player.index++; atNextBeat(() => speakLine(token), token); }
    };
    u.onerror = e => {
      if (token !== player.token || e.error === 'canceled' || e.error === 'interrupted') return;
      toast("Oops, the voice stopped. Let's try again!");
      resetPlayer();
    };
    player.utterance = u;
    synth.speak(u);
  };

  atNextBeat(singChunk, token);
}

/* ---------- player (speaks one line at a time so we can highlight it) ---------- */
function setActive(id, index) {
  $$('.line.active').forEach(el => el.classList.remove('active'));
  if (id === null) return;
  $$('.line[data-rhyme="' + id + '"][data-line="' + index + '"]').forEach(el => el.classList.add('active'));
}

function syncUI() {
  const bar = $('#nowBar');
  const running = player.id !== null;
  bar.hidden = !running;
  document.body.classList.toggle('has-bar', running);
  if (running) {
    const item = byId(player.id);
    $('#nowEmoji').textContent = item.emoji;
    $('#nowTitle').textContent = item.title;
    $('#nowBtn').dataset.id = player.id;
  }
  for (const btn of $$('[data-play]')) {
    const mine = btn.dataset.id === player.id;
    btn.textContent = mine && player.status === 'playing' ? '⏸ Pause'
                    : mine && player.status === 'paused'  ? '▶ Resume' : '▶ Play';
  }
  $$('.card').forEach(c => c.classList.toggle('is-playing', c.dataset.id === player.id && player.status === 'playing'));
  stage.dataset.playing = String(stageId !== null && stageId === player.id && player.status === 'playing');
  setActive(player.id, player.index);
}

function resetPlayer() {
  player.token++;
  player.id = null; player.index = 0; player.status = 'idle'; player.utterance = null;
  stopBeat();
  if (synth) synth.cancel();
  syncUI();
}

function speakLine(token) {
  if (token !== player.token || player.status !== 'playing') return;
  const item = byId(player.id);
  if (player.index >= item.lines.length) return finish(item);
  setActive(item.id, player.index);
  if (settings.style !== 'read') return singLine(token, item);
  const u = new SpeechSynthesisUtterance(item.lines[player.index]);
  applyVoice(u);
  u.onend = () => {
    if (token !== player.token) return;
    player.index++;
    setTimeout(() => speakLine(token), 160);
  };
  u.onerror = e => {
    if (token !== player.token || e.error === 'canceled' || e.error === 'interrupted') return;
    toast("Oops, the voice stopped. Let's try again!");
    resetPlayer();
  };
  player.utterance = u; // keep a reference so the browser doesn't garbage-collect it mid-sentence
  synth.speak(u);
}

function start(id) {
  if (!synth) return toast("This browser can't read aloud, but you can still sing along!");
  resetPlayer();
  player.id = id; player.index = 0; player.status = 'playing';
  const token = ++player.token;
  ensureAudio();
  startBeat();
  syncUI();
  speakLine(token);
}

function pause() {
  player.status = 'paused';
  player.token++;
  stopBeat();
  synth.cancel();
  syncUI();
}

function resume() {
  player.status = 'playing';
  const token = ++player.token;
  ensureAudio();
  startBeat();
  syncUI();
  speakLine(token);
}

function togglePlay(id) {
  if (player.id === id && player.status === 'playing') return pause();
  if (player.id === id && player.status === 'paused') return resume();
  start(id);
}

function finish(item) {
  const happy = settings.style === 'music';
  resetPlayer();
  if (happy && audio) [60, 64, 67, 72, 76].forEach((n, i) => tone(n, performance.now() + i * 90, { vol: 0.13, dur: 2 }));
  stars++; store.set('tt.stars', stars); renderStars(true);
  toast('Great singing! ⭐ ' + item.title);
  confetti();
}

/* ---------- rendering ---------- */
function visibleItems() {
  const q = view.query.trim().toLowerCase();
  return ITEMS.filter(i => {
    if (view.cat === 'favs' && !favs.has(i.id)) return false;
    if (view.cat !== 'all' && view.cat !== 'favs' && i.cat !== view.cat) return false;
    return !q || (i.title + ' ' + i.lines.join(' ')).toLowerCase().includes(q);
  });
}

function card(item) {
  const fav = favs.has(item.id);
  return h('article', { className: 'card', dataset: { id: item.id }, style: { '--accent': item.color } },
    h('button', { type: 'button', className: 'fav', dataset: { action: 'fav', id: item.id }, 'aria-pressed': String(fav),
                  'aria-label': 'Favorite: ' + item.title, textContent: fav ? '❤️' : '🤍' }),
    h('div', { className: 'avatar', 'aria-hidden': 'true', textContent: item.emoji }),
    h('h3', { textContent: item.title }),
    h('p', { className: 'poem' }, ...item.lines.map((text, i) =>
      h('span', { className: 'line', dataset: { rhyme: item.id, line: String(i) }, textContent: text }))),
    h('div', { className: 'actions' },
      h('button', { type: 'button', className: 'btn primary', dataset: { action: 'toggle', id: item.id, play: '' }, textContent: '▶ Play' }),
      h('button', { type: 'button', className: 'btn ghost', dataset: { action: 'stage', id: item.id }, textContent: '🎤 Sing along' })));
}

function renderGrid() {
  const list = visibleItems();
  const grid = $('#grid');
  if (!list.length) {
    grid.replaceChildren(h('div', { className: 'empty' },
      h('p', { textContent: view.cat === 'favs' && !view.query
        ? 'No favorites yet. Tap the 🤍 on any rhyme to save it here.'
        : 'No rhymes match that. Try another word or pick All.' })));
  } else {
    grid.replaceChildren(...list.map(card));
  }
  $('#count').textContent = list.length + (list.length === 1 ? ' rhyme' : ' rhymes');
  syncUI();
}

function chips(container, entries, current, onPick) {
  const draw = () => container.replaceChildren(...entries().map(([key, label]) =>
    h('button', { type: 'button', className: 'chip', dataset: { key }, 'aria-pressed': String(key === current()), textContent: label })));
  container.addEventListener('click', e => {
    const btn = e.target.closest('.chip');
    if (!btn || !container.contains(btn)) return;
    const key = btn.dataset.key;
    onPick(key);
    draw();
    container.querySelector('[data-key="' + key + '"]')?.focus(); // keep keyboard focus after redraw
  });
  draw();
  return draw;
}

/* ---------- sing-along stage ---------- */
function openStage(id, autoplay) {
  const item = byId(id);
  if (!item) return;
  if (player.id !== null && player.id !== id) resetPlayer();
  stageId = id;
  stage.style.setProperty('--accent', item.color);
  $('#stageEmoji').textContent = item.emoji;
  $('#stageTitle').textContent = item.title;
  $('#stageLines').replaceChildren(...item.lines.map((text, i) =>
    h('div', { className: 'line', dataset: { rhyme: item.id, line: String(i) }, textContent: text })));
  $('#stagePlay').dataset.id = id;
  if (!stage.open) stage.showModal();
  syncUI();
  if (autoplay) start(id);
}

function stepStage(direction) {
  const list = visibleItems().length ? visibleItems() : ITEMS;
  const at = list.findIndex(i => i.id === stageId);
  openStage(list[(at + direction + list.length) % list.length].id, true);
}

function surprise(autoplay = true) {
  const pool = ITEMS.filter(i => i.id !== stageId);
  openStage(pool[(Math.random() * pool.length) | 0].id, autoplay);
}

function toggleFav(id) {
  if (favs.has(id)) favs.delete(id); else favs.add(id);
  store.set('tt.favs', [...favs]);
  drawCats();
  if (view.cat === 'favs') { renderGrid(); return; }
  const btn = $('.card[data-id="' + id + '"] .fav');
  const on = favs.has(id);
  btn.setAttribute('aria-pressed', String(on));
  btn.textContent = on ? '❤️' : '🤍';
  if (on) toast('Saved to your favorites!');
}

/* ---------- wiring ---------- */
document.addEventListener('click', e => {
  const el = e.target.closest('[data-action]');
  if (!el) return;
  const { action, id } = el.dataset;
  switch (action) {
    case 'toggle':   togglePlay(id); break;
    case 'stop':     resetPlayer(); break;
    case 'stage':    openStage(id, true); break;
    case 'fav':      toggleFav(id); break;
    case 'close':    stage.close(); break;
    case 'prev':     stepStage(-1); break;
    case 'next':     stepStage(1); break;
    case 'surprise': surprise(true); break;
    case 'test':     previewVoice(); break;
    case 'theme': {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme(next); store.set('tt.theme', next); break;
    }
  }
});

stage.addEventListener('click', e => { if (e.target === stage) stage.close(); }); // click on the dim backdrop
stage.addEventListener('close', () => { stageId = null; resetPlayer(); });
$('#search').addEventListener('input', e => { view.query = e.target.value; renderGrid(); });
$('#deviceVoice').addEventListener('change', e => { settings.device = e.target.value; store.set('tt.settings', settings); previewVoice(); });
addEventListener('pagehide', () => { if (synth) synth.cancel(); });

chips($('#voiceChips'), () => Object.entries(PRESETS).map(([k, p]) => [k, p.label]), () => settings.voice,
      key => { settings.voice = key; store.set('tt.settings', settings); previewVoice(); });
chips($('#speedChips'), () => Object.entries(SPEEDS).map(([k, s]) => [k, s.label]), () => settings.speed,
      key => { settings.speed = key; store.set('tt.settings', settings); if (player.status === 'playing') startBeat(); });
chips($('#styleChips'), () => Object.entries(STYLES), () => settings.style,
      key => { settings.style = key; store.set('tt.settings', settings); if (key === 'music') ensureAudio(); });
const drawCats = chips($('#catChips'),
      () => Object.entries(CATS).map(([k, label]) => [k, k === 'favs' && favs.size ? label + ' (' + favs.size + ')' : label]),
      () => view.cat, key => { view.cat = key; renderGrid(); });

/* ---------- start ---------- */
applyTheme(document.documentElement.dataset.theme || 'light');
renderStars(false);
if (synth) { loadVoices(); synth.onvoiceschanged = loadVoices; } else { $('#noVoice').hidden = false; }
renderGrid();
if (location.hash === '#surprise') {   // the /random link lands here
  history.replaceState(null, '', location.pathname);
  surprise(false);                     // browsers need a tap before speaking, so we don't auto-play
  toast('Press Play to hear it! 🎵');
}
})();
</script>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
#  Server
# --------------------------------------------------------------------------- #
def render_page(nonce: str) -> bytes:
    return PAGE.replace("__NONCE__", nonce).replace("__DATA__", DATA_JSON).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "ToonTunes/2.0"

    def _send(self, status, body=b"", content_type="text/html; charset=utf-8", headers=None, head_only=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-cache")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _route(self, head_only):
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path == "/":
            nonce = secrets.token_urlsafe(16)
            csp = (
                f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
                "img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
            )
            self._send(HTTPStatus.OK, render_page(nonce), headers={"Content-Security-Policy": csp}, head_only=head_only)
        elif path == "/random":
            # Old link still works: the page opens a random rhyme on its own.
            self._send(HTTPStatus.FOUND, headers={"Location": "/#surprise"}, head_only=head_only)
        elif path == "/api/rhymes":
            body = json.dumps({"rhymes": ITEMS}, ensure_ascii=False).encode("utf-8")
            self._send(HTTPStatus.OK, body, "application/json; charset=utf-8", head_only=head_only)
        elif path == "/healthz":
            self._send(HTTPStatus.OK, b"ok", "text/plain; charset=utf-8", head_only=head_only)
        elif path == "/favicon.ico":
            self._send(HTTPStatus.NO_CONTENT, head_only=head_only)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_GET(self):
        self._route(head_only=False)

    def do_HEAD(self):
        self._route(head_only=True)

    def log_message(self, *_):
        pass


def main():
    host = os.environ.get("TOON_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Toon Tunes: http://{'localhost' if host == '127.0.0.1' else host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
