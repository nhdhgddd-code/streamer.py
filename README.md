#!/usr/bin/env python3
"""
discord direct stream spoofer - v7.0 (final & autonomous)
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

# إعداد السجل (Logging) للمتابعة الدقيقة
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("AutonomousStreamer")

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "autonomous_stream_state.json"

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

# الثوابت الخاصة بك لضمان التشغيل التلقائي الكامل دون سؤال متكرر
FIXED_VOICE_CHANNEL_ID = "1514634823866650637"

@dataclass
class State:
    token: str = ""
    voice_channel_id: str = FIXED_VOICE_CHANNEL_ID
    total_minutes: int = 0

    @classmethod
    def load(cls) -> "State":
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                obj = cls()
                obj.token = data.get("token", "")
                obj.voice_channel_id = data.get("voice_channel_id", FIXED_VOICE_CHANNEL_ID)
                obj.total_minutes = data.get("total_minutes", 0)
                return obj
            except Exception:
                pass
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
    except Exception:
        pass
    return Game("469433659223531536", "Visual Studio Code", "code.exe")

class AutonomousStreamEngine:
    def __init__(self, state: State, session: Session, game: Game) -> None:
        self.state = state
        self.session = session
        self.game = game
        self._seq = 0

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def send_heartbeat(self, duration_ms: int = 60000) -> int:
        now = int(time.time() * 1000)
        sid = str(uuid.uuid4())
        clean_token = self.state.token.strip().strip('"').strip("'")
        
        event = {
            "type": "running_game_heartbeat",
            "properties": {
                "client_track_timestamp": now,
                "client_heartbeat_session_id": self.session.heartbeat_session,
                "event_sequence_number": self._next_seq(),
                "game_id": self.game.id,
                "game_name": self.game.name,
                "game_executable": self.game.exe,
                "initial_heartbeat": False,
                "final_heartbeat": False,
                "game_session_id": sid,
                "duration_tracked_ms": duration_ms,
                "voice_channel_id": self.state.voice_channel_id,
                "voice_channel_type": "guild_voice",
                "is_streaming": True,
                "video_enabled": True,
                "viewer_count": 2,
                "launch_signature": self.session.launch_signature,
                "client_app_state": "focused",
                "client_send_timestamp": now
            }
        }
        
        payload = {"token": None, "events": [event]}
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "authorization": clean_token,
            "content-type": "application/json",
            "origin": "https://discord.com",
            "user-agent": USER_AGENT,
            "x-super-properties": self.session.super_props,
        }
        
        request = urllib.request.Request(SCIENCE_URL, data=body, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code
        except Exception:
            return 0

def main() -> None:
    logger.info("Initializing Autonomous Discord Stream Spoofer...")
    state = State.load()
    
    # إذا لم يكن التوكن مخزناً، سيطلبه منك مرة واحدة فقط ويقوم بحفظه أوتوماتيكياً
    if not state.token:
        token_input = input("Enter your Discord Token: ").strip()
        if not token_input:
            logger.error("Token is required.")
            sys.exit(1)
        state.token = token_input
        state.voice_channel_id = FIXED_VOICE_CHANNEL_ID
        state.save()
        logger.info("Token and Voice Channel ID saved successfully.")

    session = Session.new()
    game = fetch_primary_game()
    engine = AutonomousStreamEngine(state, session, game)
    
    logger.info(f"Stream simulation loop started for game: {game.name}")
    logger.info(f"Target Voice Channel ID: {state.voice_channel_id}")
    logger.info("Running loop with viewer simulation... Press Ctrl+C to stop safely.")

    try:
        while True:
            status = engine.send_heartbeat(60000)
            if status in (200, 202, 204):
                state.total_minutes += 1
                state.save()
                logger.info(f"Heartbeat sent successfully ({status}). Total tracked minutes: {state.total_minutes}")
            elif status == 401:
                logger.error("Token rejected (401 Unauthorized). Please check your token.")
                break
            else:
                logger.warning(f"Received status code {status}. Retrying next cycle...")
            
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopped by user. State saved successfully.")

if __name__ == "__main__":
    main()
