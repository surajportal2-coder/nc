from flask import Flask, render_template, request, jsonify
from instagrapi import Client
import threading
import time
import random
import os

app = Flask(__name__)
app.secret_key = "sujal_hawk_rename_fixed_2025"

state = {"running": False, "logs": [], "start_time": None}
cfg = {"sessionid": "", "thread_id": 0, "base_name": "", "delay": 60}

# Undetected devices rotation (login success ke liye must)
DEVICES = [
    {"phone_manufacturer": "Google", "phone_model": "Pixel 8 Pro", "android_version": 15, "android_release": "15.0.0", "app_version": "323.0.0.46.109"},
    {"phone_manufacturer": "Samsung", "phone_model": "SM-S928B", "android_version": 15, "android_release": "15.0.0", "app_version": "324.0.0.41.110"},
    {"phone_manufacturer": "OnePlus", "phone_model": "PJZ110", "android_version": 15, "android_release": "15.0.0", "app_version": "322.0.0.40.108"},
    {"phone_manufacturer": "Xiaomi", "phone_model": "23127PN0CC", "android_version": 15, "android_release": "15.0.0", "app_version": "325.0.0.42.111"},
]

def log(msg):
    entry = f"[{time.strftime('%H:%M:%S')}] {msg}"
    state["logs"].append(entry)
    if len(state["logs"]) > 500:
        state["logs"] = state["logs"][-500:]

def rename_loop():
    cl = Client()
    cl.delay_range = [8, 30]

    # Device rotation + user-agent (login success ke liye zaroori)
    device = random.choice(DEVICES)
    cl.set_device(device)
    cl.set_user_agent(f"Instagram {device['app_version']} Android (34/15.0.0; 480dpi; 1080x2340; {device['phone_manufacturer']}; {device['phone_model']}; raven; raven; en_US)")

    try:
        cl.login_by_sessionid(cfg["sessionid"])
        log("LOGIN SUCCESS — NAME CHANGE LOOP STARTED")
    except Exception as e:
        log(f"LOGIN FAILED → {str(e)[:80]}")
        return

    while state["running"]:
        try:
            new_name = cfg["base_name"]  # simple name, no extra text
            # New working method (private request for group title change)
            cl.private_request(
                f"direct_v2/threads/{cfg['thread_id']}/update_title/",
                data={"title": new_name}
            )
            log(f"NAME CHANGED TO → {new_name}")
        except Exception as e:
            log(f"Name change failed → {str(e)[:50]} — retrying next cycle")

        time.sleep(cfg["delay"])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    global state
    state["running"] = False
    time.sleep(1)
    state = {"running": True, "logs": ["RENAME STARTED"], "start_time": time.time()}

    cfg["sessionid"] = request.form["sessionid"].strip()
    cfg["thread_id"] = int(request.form["thread_id"])
    cfg["base_name"] = request.form["base_name"].strip()
    cfg["delay"] = float(request.form.get("delay", "60"))

    threading.Thread(target=rename_loop, daemon=True).start()
    log("RENAME THREAD STARTED")

    return jsonify({"ok": True})

@app.route("/stop")
def stop():
    state["running"] = False
    log("STOPPED BY USER")
    return jsonify({"ok": True})

@app.route("/status")
def status():
    uptime = "00:00:00"
    if state.get("start_time"):
        t = int(time.time() - state["start_time"])
        h, r = divmod(t, 3600)
        m, s = divmod(r, 60)
        uptime = f"{h:02d}:{m:02d}:{s:02d}"
    return jsonify({
        "running": state["running"],
        "uptime": uptime,
        "logs": state["logs"][-100:]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
