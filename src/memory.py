"""Conversation memory for the EnerTech chatbot.

Histories are kept in the Flask process and keyed by session id, so concurrent
visitors never share context. To move to Redis or a database later, keep this
public interface (``history``, ``append``, ``reset``) and swap the internals.
"""

import os
import re
import secrets
import threading
import time

from langchain_core.messages import AIMessage, HumanMessage

# Idle time after which a visitor's conversation is dropped.
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "1800"))

# Number of user+assistant exchanges replayed to the model. Caps token cost per
# request so a long chat does not get progressively more expensive.
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "6"))

# Upper bound on tracked sessions, so forged session ids cannot grow the process
# memory without limit.
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "5000"))

MAX_SESSION_ID_LENGTH = 128
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


def new_session_id():
    return secrets.token_urlsafe(24)


def normalize_session_id(raw):
    """Return a safe session id, or ``None`` if the client sent something odd."""
    candidate = (raw or "").strip()
    if not candidate or len(candidate) > MAX_SESSION_ID_LENGTH:
        return None
    if not _SESSION_ID_PATTERN.match(candidate):
        return None
    return candidate


class ConversationMemory:
    def __init__(
        self,
        ttl_seconds=SESSION_TTL_SECONDS,
        max_turns=MAX_HISTORY_TURNS,
        max_sessions=MAX_SESSIONS,
    ):
        self._ttl = ttl_seconds
        self._max_messages = max_turns * 2
        self._max_sessions = max_sessions
        self._lock = threading.Lock()
        # session_id -> {"messages": [(role, text), ...], "updated_at": float}
        self._sessions = {}

    def history(self, session_id):
        """Prior turns as LangChain messages, oldest first."""
        if not session_id:
            return []
        now = time.time()
        with self._lock:
            self._drop_expired(now)
            entry = self._sessions.get(session_id)
            if entry is None:
                return []
            entry["updated_at"] = now
            stored = list(entry["messages"])

        return [
            HumanMessage(content=text) if role == "human" else AIMessage(content=text)
            for role, text in stored
        ]

    def start_if_new(self, session_id, greeting):
        """Seed an unseen session with the greeting the UI already displayed.

        Without this the model sees an empty history on the first request and
        repeats the welcome menu instead of acting on the customer's choice.
        """
        if not session_id or not greeting:
            return
        now = time.time()
        with self._lock:
            self._drop_expired(now)
            if session_id in self._sessions:
                return
            self._enforce_capacity()
            self._sessions[session_id] = {
                "messages": [("ai", greeting)],
                "updated_at": now,
            }

    def append(self, session_id, user_message, bot_message):
        if not session_id:
            return
        now = time.time()
        with self._lock:
            self._drop_expired(now)
            entry = self._sessions.get(session_id)
            if entry is None:
                self._enforce_capacity()
                entry = {"messages": [], "updated_at": now}
                self._sessions[session_id] = entry
            entry["messages"].append(("human", user_message))
            entry["messages"].append(("ai", bot_message))
            if len(entry["messages"]) > self._max_messages:
                entry["messages"] = entry["messages"][-self._max_messages :]
            entry["updated_at"] = now

    def reset(self, session_id):
        if not session_id:
            return False
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def stats(self):
        with self._lock:
            return {
                "active_sessions": len(self._sessions),
                "ttl_seconds": self._ttl,
                "max_turns": self._max_messages // 2,
            }

    def _drop_expired(self, now):
        cutoff = now - self._ttl
        expired = [
            key
            for key, entry in self._sessions.items()
            if entry["updated_at"] < cutoff
        ]
        for key in expired:
            del self._sessions[key]

    def _enforce_capacity(self):
        overflow = len(self._sessions) + 1 - self._max_sessions
        if overflow <= 0:
            return
        oldest = sorted(self._sessions.items(), key=lambda item: item[1]["updated_at"])
        for key, _ in oldest[:overflow]:
            del self._sessions[key]


conversations = ConversationMemory()
