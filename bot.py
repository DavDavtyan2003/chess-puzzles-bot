import json
import os
import random
import chess
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]

TIERS = {
    "nivel1": {"chat_id_env": "NIVEL1_CHAT_ID", "label": "Nivel 1"},
    "nivel2": {"chat_id_env": "INTERMEDIATE_CHAT_ID", "label": "Nivel 2"},
    "nivel3": {"chat_id_env": "NIVEL3_CHAT_ID", "label": "Nivel 3"},
    "nivel4": {"chat_id_env": "NIVEL4_CHAT_ID", "label": "Nivel 4"},
}

STATE_FILE = "state.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})


def send_photo(chat_id, image_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as img:
        requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"photo": img})


def render_puzzle(fen, first_move_uci, out_path):
    board = chess.Board(fen)
    board.push_uci(first_move_uci)
    orientation = "white" if board.turn else "black"

    params = {"fen": board.fen(), "orientation": orientation, "size": 480}
    response = requests.get("https://backscattering.de/web-boardimage/board.png", params=params)
    with open(out_path, "wb") as f:
        f.write(response.content)

    return board, board.turn


def reveal_previous_solution(chat_id, tier_state):
    last = tier_state.get("last_puzzle")
    if not last:
        return
    board = chess.Board(last["fen"])
    board.push_uci(last["first_move"])
    san_moves = []
    for uci in last["solution_moves"]:
        move = chess.Move.from_uci(uci)
        san_moves.append(board.san(move))
        board.push(move)
    send_message(chat_id, "Yesterday's solution: " + " ".join(san_moves))


def pick_next_puzzle(tier_state, puzzles):
    if not tier_state["order"] or tier_state["position"] >= len(tier_state["order"]):
        order = list(range(len(puzzles)))
        random.shuffle(order)
        tier_state["order"] = order
        tier_state["position"] = 0

    idx = tier_state["order"][tier_state["position"]]
    tier_state["position"] += 1
    return puzzles[idx]


def process_tier(tier_key, tier_info, state):
    chat_id = os.environ[tier_info["chat_id_env"]]
    puzzles = load_json(f"puzzles/{tier_key}.json")

    tier_state = state.setdefault(tier_key, {"order": [], "position": 0, "last_puzzle": None})

    reveal_previous_solution(chat_id, tier_state)

    puzzle = pick_next_puzzle(tier_state, puzzles)
    first_move = puzzle["moves"][0]
    solution_moves = puzzle["moves"][1:]

    image_path = f"current_{tier_key}.png"
    board, orientation = render_puzzle(puzzle["fen"], first_move, image_path)
    side = "White" if orientation else "Black"

    caption = f"Puzzle of the day ({tier_info['label']}, rating {puzzle['rating']})\n{side} to move."
    send_photo(chat_id, image_path, caption)

    tier_state["last_puzzle"] = {
        "fen": puzzle["fen"],
        "first_move": first_move,
        "solution_moves": solution_moves
    }


def main():
    state = load_json(STATE_FILE) if os.path.exists(STATE_FILE) else {}

    for tier_key, tier_info in TIERS.items():
        process_tier(tier_key, tier_info, state)

    save_json(STATE_FILE, state)


if __name__ == "__main__":
    main()