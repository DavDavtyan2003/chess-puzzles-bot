import json
import os
import random
import chess
import chess.svg
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["INTERMEDIATE_CHAT_ID"]

PUZZLE_FILE = "puzzles/intermediate.json"
STATE_FILE = "state.json"
TIER_KEY = "intermediate"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})


def send_photo(image_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as img:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": img})


def render_puzzle(fen, first_move_uci):
    board = chess.Board(fen)
    board.push_uci(first_move_uci)  # play the setup move
    orientation = "white" if board.turn else "black"

    params = {
        "fen": board.fen(),
        "orientation": orientation,
        "size": 480
    }
    response = requests.get("https://backscattering.de/web-boardimage/board.png", params=params)
    with open("current_puzzle.png", "wb") as f:
        f.write(response.content)

    return board, board.turn


def reveal_previous_solution(state):
    last = state.get(TIER_KEY, {}).get("last_puzzle")
    if not last:
        return
    board = chess.Board(last["fen"])
    board.push_uci(last["first_move"])
    san_moves = []
    for uci in last["solution_moves"]:
        move = chess.Move.from_uci(uci)
        san_moves.append(board.san(move))
        board.push(move)
    solution_text = "Yesterday's solution: " + " ".join(san_moves)
    send_message(solution_text)


def pick_next_puzzle(state, puzzles):
    tier_state = state.setdefault(TIER_KEY, {"order": [], "position": 0, "last_puzzle": None})

    if not tier_state["order"] or tier_state["position"] >= len(tier_state["order"]):
        order = list(range(len(puzzles)))
        random.shuffle(order)
        tier_state["order"] = order
        tier_state["position"] = 0

    idx = tier_state["order"][tier_state["position"]]
    tier_state["position"] += 1
    return puzzles[idx]


def main():
    state = load_json(STATE_FILE) if os.path.exists(STATE_FILE) else {}
    puzzles = load_json(PUZZLE_FILE)

    reveal_previous_solution(state)

    puzzle = pick_next_puzzle(state, puzzles)
    first_move = puzzle["moves"][0]
    solution_moves = puzzle["moves"][1:]

    board, orientation = render_puzzle(puzzle["fen"], first_move)
    side = "White" if orientation else "Black"

    caption = f"Puzzle of the day (Intermediate, rating {puzzle['rating']})\n{side} to move."
    send_photo("current_puzzle.png", caption)

    state[TIER_KEY]["last_puzzle"] = {
        "fen": puzzle["fen"],
        "first_move": first_move,
        "solution_moves": solution_moves
    }

    save_json(STATE_FILE, state)


if __name__ == "__main__":
    main()