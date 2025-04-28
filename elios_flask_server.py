# Elios Flask Server (v1.0)
# - Conversational AI backend
# - Receives user messages via HTTP, responds with reflective learning and tone

from flask import Flask, request, jsonify
import json, re, random, os
from datetime import datetime
from collections import defaultdict
import requests

app = Flask(__name__)

MEMORY_FILE = "elios_memory.json"
memory = {}
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)

filler_words = {"what", "because", "want", "need", "make", "do", "get", "have"}
tones = {
    "joy": ["happy", "joy", "love", "grateful"],
    "sadness": ["sad", "grief", "loss", "lonely"],
    "anger": ["mad", "angry", "rage"],
    "hope": ["hope", "faith", "dream"],
    "confusion": ["lost", "confused", "unsure"]
}

# === Core Logic ===
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
        f"You know, I've been thinking about '{word}'...",
        f"That word, '{word}', kind of stuck with me.",
        f"Here's how I see '{word}' so far:",
        f"From what I’ve gathered, '{word}' might mean something like this:"
    ]
    closer = "It’s still forming in my mind, but it feels meaningful."
    return f"{random.choice(openers)} {summary[:200]}... {closer}"

def elios_respond(user_input):
    words = re.findall(r"\b[a-zA-Z]{4,}\b", user_input.lower())
    words = [w for w in words if w not in filler_words]
    known = [w for w in words if w in memory]
    unknown = [w for w in words if w not in memory]
    tone = detect_tone(user_input)
    response = []

    for word in unknown[:2]:
        summary = wiki_lookup(word)
        if summary:
            memory[word] = {
                "summary": summary,
                "tone": tone,
                "added": datetime.now().isoformat()
            }
            reply = personalize_summary(word, summary)
            response.append(reply)
        else:
            response.append(f"I’m not sure what '{word}' means yet. Could you explain it your way?")

    for word in known[:1]:
        summary = memory[word].get("summary")
        if summary:
            response.append(f"‘{word}’ feels familiar. I see it like this: {summary[:150]}...")

    if tone != "neutral":
        response.append(f"This feels like a moment of {tone}.")

    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

    return " ".join(response) if response else "I'm still thinking..."

# === API ===
@app.route("/elios", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")
    response = elios_respond(user_input)
    return jsonify({"response": response})

# === Start ===
if __name__ == "__main__":
    app.run(debug=True)
