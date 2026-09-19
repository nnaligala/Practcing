from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import html
import random


RHYMES = [
	("Bouncy Bunny", "🐰", "Bouncy bunny hops so high,\nWaving at the clouds nearby!\nHop, hop, hop and spin around,\nHappy giggles fill the ground!", "#ffd6e7"),
	("Rocket Cat", "🐱", "Rocket cat goes zoom, zoom, zoom,\nFlying past the moon so bright.\nStars all twinkle in the night,\nWhat a super space delight!", "#d8e8ff"),
	("Dancing Dino", "🦕", "Dancing dino taps his toes,\nWiggles fingers, shakes his nose.\nStomp, stomp, stomp across the floor,\nThen he dances out the door!", "#d9f7df"),
	("Sunny Puppy", "🐶", "Sunny puppy wags his tail,\nChasing butterflies along the trail.\nRun, run, run beneath the sun,\nEvery day is full of fun!", "#fff0b8"),
	("Jolly Jellyfish", "🪼", "Jolly jellyfish sways below,\nDancing where the bubbles go.\nBlink, blink, sparkle blue,\nOcean friends are waving too!", "#e5d5ff"),
	("Merry Monkey", "🐵", "Merry monkey climbs a tree,\nPeeks down laughing, 'Look at me!'\nSwing, swing, from vine to vine,\nJungle playtime feels just fine!", "#d5f4e6"),
	("Twinkly Owl", "🦉", "Twinkly owl flies through the night,\nGuided by the moonbeam light.\nHoot, hoot, soft and slow,\nDreamy little stars all glow!", "#ffe0c2"),
]


SONGS = [
	("The Friendship Song", "🎶", "Clap your hands and tap your feet,\nFriends together make a beat!\nSmile and sing, come along,\nEveryone can join this song!"),
	("Rainbow Ride", "🌈", "Red and orange, yellow too,\nGreen and blue and purple hue.\nSing along and reach up high,\nRide a rainbow through the sky!"),
]


HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Toon Tunes</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;color:#29234d;background:linear-gradient(135deg,#fff8d6,#e9ddff);background-size:200% 200%;animation:sky 12s ease-in-out infinite alternate;overflow-x:hidden}
body:before,body:after{content:"";position:fixed;border-radius:50%;opacity:.25;z-index:-1;filter:blur(2px);animation:float 8s ease-in-out infinite alternate}body:before{width:180px;height:180px;background:#ff9ec4;top:12%;left:4%}body:after{width:240px;height:240px;background:#8bdcff;right:3%;bottom:8%;animation-delay:-3s}
@keyframes sky{to{background-position:100% 100%}}@keyframes float{to{transform:translate(35px,-25px) scale(1.15)}}
header{text-align:center;padding:45px 20px 28px}h1{margin:0;color:#6336c7;font-size:clamp(2.5rem,8vw,5rem)}header p{font-size:1.2rem}
main{max-width:1100px;margin:auto;padding:10px 20px 50px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:22px}
.card{background:#fff;border-radius:24px;padding:24px;box-shadow:0 8px 20px #57408c25;border-top:9px solid var(--color);transition:.2s}.card:hover{transform:translateY(-6px)}
.character{text-align:center;font-size:4rem}h2{text-align:center;color:#6336c7;margin:8px 0 18px}pre{font:inherit;white-space:pre-wrap;line-height:1.7;margin:0}.songs{margin-top:35px}.song{background:#ffffffc9;border-radius:20px;padding:18px 24px;margin:14px 0;box-shadow:0 5px 14px #57408c20}.song h2{margin:0 0 8px}.song-icon{font-size:2rem;margin-right:8px}
.speak,.select-rhyme{display:inline-block;margin:18px 4px 0;padding:9px 16px;border:0;border-radius:20px;background:#6336c7;color:white;font-weight:bold;cursor:pointer}.speak:hover,.select-rhyme:hover{background:#4e27a5}.voice-controls{text-align:center;background:#ffffffc9;border-radius:20px;padding:16px;margin:0 auto 28px;max-width:650px}.voice-controls select{padding:9px;border:2px solid #d8caff;border-radius:12px;margin:4px}
.button{display:block;width:max-content;margin:28px auto 0;padding:13px 24px;border-radius:30px;background:#ff8066;color:white;font-weight:bold;text-decoration:none}
footer{text-align:center;padding:20px;color:#655c80}
</style></head><body><header><h1>🎵 Toon Tunes 🎨</h1>
<p>Sing, laugh, and rhyme along with our friendly cartoon crew!</p></header><main><section class="voice-controls"><label>Choose a voice: <select id="voiceSelect"><option value="auto">Automatic</option><option value="girl">Girl / Female</option><option value="boy">Boy / Male</option><option value="gents">Gents / Deep</option></select></label><br><button class="speak" id="playSelected" onclick="speakSelected()">🔊 Play selected rhyme</button></section><section class="grid">{cards}</section><section class="songs"><h2>🎤 Sing-Along Songs</h2>{songs}</section>
<a class="button" href="/random">✨ Pick a surprise rhyme</a></main><footer>Made for little imaginations · Keep singing!</footer>
<script>
let selectedText = '';
let currentButton = null;
let paused = false;
let availableVoices = [];

function loadVoices() { availableVoices = speechSynthesis.getVoices(); }
if (window.speechSynthesis) { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices; }

function selectRhyme(text, button) {
	selectedText = text;
	document.querySelectorAll('.select-rhyme').forEach(item => item.textContent = '🎵 Select rhyme');
	button.textContent = '✅ Selected';
}

function speakSelected() {
	if (!selectedText) { alert('Please select a rhyme first.'); return; }
	speak(selectedText, document.getElementById('playSelected'));
}

function speak(text, button) {
	if (!window.speechSynthesis) { button.textContent = 'Voice not supported'; return; }
	if (speechSynthesis.paused && currentButton === button) { speechSynthesis.resume(); paused = false; button.textContent = '⏸ Pause'; return; }
	speechSynthesis.cancel();
	const voice = new SpeechSynthesisUtterance(text);
	voice.rate = 0.9;
	const choice = document.getElementById('voiceSelect').value;
	const female = /female|woman|zira|samantha|karen|victoria|susan/i;
	const male = /male|man|david|daniel|mark|alex/i;
	const matches = choice === 'girl' ? female : choice === 'boy' ? male : choice === 'gents' ? male : null;
	if (matches) voice.voice = availableVoices.find(item => matches.test(item.name)) || null;
	currentButton = button; paused = false;
	button.textContent = '⏸ Pause';
	voice.onend = () => { button.textContent = '🔊 Read aloud'; currentButton = null; };
	speechSynthesis.speak(voice);
}

function pauseVoice(button) {
	if (speechSynthesis.speaking && !speechSynthesis.paused) { speechSynthesis.pause(); paused = true; button.textContent = '▶ Resume'; }
}
</script></body></html>"""


def page(rhymes):
	cards = "".join(
		f'<article class="card" style="--color:{color}"><div class="character">{emoji}</div>'
		f'<h2>{html.escape(title)}</h2><pre>{html.escape(words)}</pre>'
		f'<button class="select-rhyme" data-text="{html.escape(words, quote=True)}" '
		f'onclick="selectRhyme(this.dataset.text, this)">🎵 Select rhyme</button>'
		f'<button class="speak" data-text="{html.escape(words, quote=True)}" '
		f'onclick="speak(this.dataset.text, this)">🔊 Read aloud</button></article>'
		for title, emoji, words, color in rhymes
	)
	songs = "".join(f'<article class="song"><h2><span class="song-icon">{emoji}</span>{html.escape(title)}</h2><pre>{html.escape(words)}</pre></article>' for title, emoji, words in SONGS)
	return HTML.replace("{cards}", cards).replace("{songs}", songs).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		path = urlparse(self.path).path
		if path == "/":
			rhymes = RHYMES
		elif path == "/random":
			rhymes = [random.choice(RHYMES)]
		else:
			self.send_error(404)
			return
		content = page(rhymes)
		self.send_response(200)
		self.send_header("Content-Type", "text/html; charset=utf-8")
		self.send_header("Content-Length", str(len(content)))
		self.end_headers()
		self.wfile.write(content)

	def log_message(self, *_):
		pass


if __name__ == "__main__":
	server = HTTPServer(("localhost", 8000), Handler)
	print("Toon Tunes: http://localhost:8000")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		server.server_close()
