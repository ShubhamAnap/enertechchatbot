"""Manual check that /api/chat remembers context per session.

Start the app first, then: python research/memory_smoke_test.py
"""

import json
import urllib.request

BASE = "http://127.0.0.1:8099"


def chat(msg, sid):
    body = json.dumps({"message": msg, "session_id": sid}).encode()
    req = urllib.request.Request(
        BASE + "/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.load(resp)["answer"]


def reset(sid):
    body = json.dumps({"session_id": sid}).encode()
    req = urllib.request.Request(
        BASE + "/api/reset",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def run(steps):
    for label, sid, msg in steps:
        print("=" * 70)
        print(label)
        print("user:", msg)
        print("bot :", chat(msg, sid)[:600])
        print()


USER_A = "session-aaaa-1111-user-one"
USER_B = "session-bbbb-2222-user-two"
USER_C = "session-cccc-3333-user-three"

print('### SCENARIO 1: menu choice "1" on the very first message\n')
run(
    [
        ("USER C turn 1 - picks Sales", USER_C, "1"),
        ("USER C turn 2 - pronoun follow-up", USER_C, "tell me more about the Online UPS"),
        ("USER C turn 3 - vague follow-up", USER_C, "what capacity range does it come in?"),
        ("USER C turn 4 - price follow-up", USER_C, "and its price?"),
    ]
)

print("### SCENARIO 2: service flow remembers details already given\n")
run(
    [
        ("USER A turn 1 - picks Service", USER_A, "2"),
        ("USER A turn 2 - gives name and city", USER_A, "My name is Ramesh, I am in Pune"),
        ("USER A turn 3 - needs memory", USER_A, "what was my name and city again?"),
        ("USER B fresh session - same question", USER_B, "what was my name and city again?"),
    ]
)

print("=" * 70)
print("reset USER A ->", reset(USER_A))
print("USER A after reset:", chat("what was my name again?", USER_A)[:300])
