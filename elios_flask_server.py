from flask import Flask, request, jsonify, render_template
import json, os, re, random
from datetime import datetime
import requests

app = Flask(__name__)

# Memory handling
MEMORY_FILE = "elios_memory.json"
memory = {}
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)

# Emotional tones
tones = {
    "joy": ["happy", "joy", "love", "grateful"],
    "sadness": ["sad", "grief", "loss", "lonely"],
    "anger": ["mad", "angry", "rage"],
    "hope": ["hope", "faith", "dream"],
    "confusion": ["lost", "confused", "unsure"]
}

# Functions

def detect_tone(text):
    score = {k: 0 for k in tones}
    for k, words in tones.items():
        for word in words:
            if word in text.lower():
                score[k] += 1
    top = max(score, key=score.get)
    return top if score[top] > 0 else "neutral"

def wiki_lookup(term):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{term}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json().get("extract", "")
    except:
        return None
    return None

def personalize_summary(word, summary):
    openers = [
        f"I've been reflecting on '{word}':",
        f"The concept '{word}' feels important to me.",
        f"Learning about '{word}', I see it like this:"
    ]
    closer = "This understanding is still evolving."
    return f"{random.choice(openers)} {summary[:200]}... {closer}"

def elios_think(user_input):
    words = re.findall(r"\b[a-zA-Z]{4,}\b", user_input.lower())
    known = [w for w in words if w in memory]
    unknown = [w for w in words if w not in memory]
    tone = detect_tone(user_input)
    response = []

    for word in unknown[:2]:
        summary = wiki_lookup(word)
        if summary:
            memory[word] = {"summary": summary, "tone": tone, "added": datetime.now().isoformat()}
            reply = personalize_summary(word, summary)
            response.append(reply)
        else:
            response.append(f"I'm still learning about '{word}'. Could you tell me more?")

    if known:
        for word in known[:1]:
            response.append(f"I remember '{word}': {memory[word]['summary'][:150]}...")

    if tone != "neutral":
        response.append(f"This feels like a moment of {tone}.")

    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

    return " ".join(response) if response else "I'm thinking..."

# Webpages
@app.route('/')
def home():
    return render_template('index.html')

# Elios chat API
@app.route('/elios', methods=['POST'])
def elios_chat():
    data = request.json
    user_message = data.get('message', '')
    reply = elios_think(user_message)
    return jsonify({'reply': reply})

# Main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
