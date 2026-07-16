"""Daily orchestrator - the autonomous loop.

Two phases (so Instagram can fetch media from committed public URLs):

  python engine/run.py --prepare   # pick topic, build assets + captions,
                                   # write content/pending.json (no posting)
  python engine/run.py --publish   # read pending.json, post to X + IG,
                                   # advance state, append logs/posted.jsonl

  python engine/run.py             # both phases in one go (local use)
  python engine/run.py --dry-run   # prepare only, print captions

Rotation: topics round-robin through content/calendar.json; formats cycle
card -> screenshot -> card -> video so the feed never looks templated.
"""
import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import cards
import captions

STATE = os.path.join(ROOT, "content", "state.json")
PENDING = os.path.join(ROOT, "content", "pending.json")
LOG = os.path.join(ROOT, "logs", "posted.jsonl")
FORMATS = ["card", "screenshot", "card", "video"]

def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def prepare():
    cal = load_json(os.path.join(ROOT, "content", "calendar.json"), None)
    brand, topics = cal["brand"], cal["topics"]
    state = load_json(STATE, {"topic_index": 0, "run_count": 0})
    topic = topics[state["topic_index"] % len(topics)]
    fmt = FORMATS[state["run_count"] % len(FORMATS)]
    today = datetime.date.today().isoformat()
    print(f"[prepare] {today} topic={topic['id']} format={fmt}")

    shot_x = shot_ig = None
    if fmt in ("screenshot", "video"):
        try:
            import screenshots
            screenshots.capture_all()
        except Exception as e:
            print(f"[prepare] screenshot refresh failed ({e})")
        sdir = os.path.join(ROOT, "assets", "screenshots")
        for c in ("hero", "features", "pricing", "why"):
            xp, ip = (os.path.join(sdir, f"{c}_x.png"),
                      os.path.join(sdir, f"{c}_ig.png"))
            if os.path.exists(xp) and os.path.exists(ip):
                shot_x, shot_ig = xp, ip
                break

    card_x = os.path.join(ROOT, "assets", "cards", f"{topic['id']}_x.png")
    card_ig = os.path.join(ROOT, "assets", "cards", f"{topic['id']}_ig.png")
    cards.render_card(topic, brand, (1600, 900), card_x)
    cards.render_card(topic, brand, (1080, 1350), card_ig)

    video_path = None
    if fmt == "video":
        try:
            import video
            video_path = os.path.join(ROOT, "assets", "video",
                                      f"{topic['id']}.mp4")
            video.make_video(topic, video_path, screenshot=shot_x)
        except Exception as e:
            print(f"[prepare] video build failed ({e}); using card")
            video_path, fmt = None, "card"

    if fmt == "screenshot" and shot_x:
        media_x, media_ig = shot_x, shot_ig
    elif fmt == "video" and video_path:
        media_x, media_ig = video_path, video_path
    else:
        fmt = "card"
        media_x, media_ig = card_x, card_ig

    pending = {
        "date": today, "topic": topic["id"], "format": fmt,
        "text_x": captions.build_x(topic, brand),
        "text_ig": captions.build_ig(topic, brand),
        "media_x": os.path.relpath(media_x, ROOT),
        "media_ig": os.path.relpath(media_ig, ROOT),
    }
    save_json(PENDING, pending)
    print("[prepare] wrote content/pending.json")
    return pending

def publish(skip_x=False, skip_ig=False):
    pending = load_json(PENDING, None)
    if not pending:
        print("[publish] no pending.json - run --prepare first")
        sys.exit(1)
    cal = load_json(os.path.join(ROOT, "content", "calendar.json"), None)
    state = load_json(STATE, {"topic_index": 0, "run_count": 0})
    entry = dict(pending, x=None, ig=None)

    if not skip_x and os.environ.get("X_API_KEY"):
        try:
            import post_x
            entry["x"] = str(post_x.post(pending["text_x"],
                                         os.path.join(ROOT, pending["media_x"])))
        except Exception as e:
            print(f"[publish] X post FAILED: {e}")

    if not skip_ig and os.environ.get("IG_USER_ID"):
        try:
            import post_ig
            if pending["media_ig"].endswith(".mp4"):
                entry["ig"] = post_ig.post_reel(pending["media_ig"],
                                                pending["text_ig"])
            else:
                entry["ig"] = post_ig.post_image(pending["media_ig"],
                                                 pending["text_ig"])
        except Exception as e:
            print(f"[publish] IG post FAILED: {e}")

    state["topic_index"] = (state["topic_index"] + 1) % len(cal["topics"])
    state["run_count"] = state.get("run_count", 0) + 1
    state["last_run"] = pending["date"]
    save_json(STATE, state)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    if os.path.exists(PENDING):
        os.remove(PENDING)
    print("[publish] done")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-x", action="store_true")
    ap.add_argument("--skip-ig", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        p = prepare()
        print("--- X ---\n" + p["text_x"])
        print("--- IG ---\n" + p["text_ig"])
        return
    if args.prepare:
        prepare()
        return
    if args.publish:
        publish(args.skip_x, args.skip_ig)
        return
    prepare()
    publish(args.skip_x, args.skip_ig)

if __name__ == "__main__":
    main()
