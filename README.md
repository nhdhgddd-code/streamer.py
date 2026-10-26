#!/usr/bin/env python3
"""
discord enterprise-grade continuous streaming spoofer.
optimized for stability, persistent state handling, and secure heartbeats.
revere group, 2026.
"""

from __future__ import annotations

import base64
import json
import logging
import sys
import time
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

# إعداد السجل (Logging) المتقدم لمتابعة حالة التشغيل بدقة
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("DiscordStreamer")

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "enterprise_stream_state.json"

ME_URL = "https://discord.com/api/v9/users/@me?with_analytics_token=true"
SCIENCE_URL = "https://discord.com/api/v9/science"
GAMES_CDN_URL = "https://cdn.discordapp.com/detectables/games.json"

CLIENT_VERSION = "1.0.9253"
CLIENT_BUILD_NUMBER = 594031
NATIVE_BUILD_NUMBER = 88414
OS_VERSION = "10.0.26200"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) discord/1.0.9253 Chrome/148.0.7778.280 "
    "Electron/42.7.1 Safari/537.36"
)

@dataclass
class State:
    token: str = ""
    voice_channel_id: str = ""
    analytics_token: str = ""
    fetched_at: int = 0
    total_heartbeats_sent: int = 0

    @classmethod
    def load(cls) -> "State":
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                return cls(**{k: data.get(k, v) for k, v in cls().__dict__.items()})
            except Exception as e:
                logger.warning(f"Failed to load state file, creating new: {e}")
        return cls()

    def save(self) -> None:
        try:
            STATE_FILE.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

def build_super_props(launch_signature: str, heartbeat_session: str) -> str:
    props = {
        "os": "Windows", "browser": "Discord Client", "release_channel": "stable",
        "client_version": CLIENT_VERSION, "os_version": OS_VERSION, "os_arch": "x64",
        "app_arch": "x64", "system_locale": "en-GB", "has_client_mods": False,
        "browser_user_agent": USER_AGENT, "browser_version": "42.7.1",
        "os_sdk_version": "26200", "client_build_number": CLIENT_BUILD_NUMBER,
        "native_build_number": NATIVE_BUILD_NUMBER, "client_event_source": None,
        "client_app_state": "focused", "client_launch_id": str(uuid.uuid4()),
        "launch_signature": launch_signature, "client_heartbeat_session_id": heartbeat_session
    }
    raw = json.dumps(props, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")

def fetch_analytics_token(auth_token: str, super_props: str) -> str:
    req = urllib.request.Request(ME_URL, headers={
        "authorization": auth_token, "user-agent": USER_AGENT, "x-super-properties": super_props
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Token rejected with HTTP code {exc.code}") from exc
    token = data.get("analytics_token")
    if not token:
        raise RuntimeError("Missing analytics_token in user profile response")
    return token

@dataclass(frozen=True)
class Session:
    heartbeat_session: str
    launch_signature: str
    super_props: str

    @classmethod
    def new(cls) -> "Session":
        hb = str(uuid.uuid4())
        sig = str(uuid.uuid4())
        return cls(hb, sig, build_super_props(sig, hb))

@dataclass(frozen=True)
class Game:
    id: str
    name: str
    exe: str

def fetch_primary_game() -> Game:
    try:
        request = urllib.request.Request(GAMES_CDN_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        for entry in data:
            gid = str(entry.get("id", ""))
            if gid.isdigit():
                for e in entry.get("executables", []):
                    if e.get("os") == "win32" and e.get("name"):
                        return Game(gid, entry.get("name", "Visual Studio Code"), e["name"])
    except Exception as e:
        logger.warning(f"Could not fetch CDN games, using fallback: {e}")
    return Game("469433659223531536", "Visual Studio Code", "code.exe")
