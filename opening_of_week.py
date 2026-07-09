import json
import os
import random
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
OPENINGS_FILE = "openings/openings.json"
STATE_FILE = "opening_state.json"

CHAT_IDS = {
    "nivel1": os.environ["NIVEL1_CHAT_ID"],
    "nivel2": os.environ["INTERMEDIATE_CHAT_ID"],
    "nivel3": os.environ["NIVEL3_CHAT_ID"],
    "nivel4": os.environ["NIVEL4_CHAT_ID"],
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})


def main():
    openings = load_json(OPENINGS_FILE)
    state = load_json(STATE_FILE) if os.path.exists(STATE_FILE) else {"order": [], "position": 0}

    if not state["order"] or state["position"] >= len(state["order"]):
        order = list(range(len(openings)))
        random.shuffle(order)
        state["order"] = order
        state["position"] = 0

    idx = state["order"][state["position"]]
    state["position"] += 1
    opening = openings[idx]

    text = f"📚 Apertura de la semana: {opening['name']}\n\n{opening['note']}\n\nEstudio: {opening['study_url']}"

    for chat_id in CHAT_IDS.values():
        send_message(chat_id, text)

    save_json(STATE_FILE, state)


if __name__ == "__main__":
    main()