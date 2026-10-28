#!/usr/bin/env python3
"""
discord ultimate precise streaming spoofer - v5.0
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

# إعداد السجل (Logging) للمتابعة الدقيقة على الخادم
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("PreciseStreamer")

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "precise_stream_state.json"

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
    total_minutes: int = 0

    @classmethod
    def load(cls) -> "State":
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                return cls(**{k: data.get(k, v) for k, v in cls().__dict__.items()})
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

def fetch_analytics_token(auth_token: str, super_props: str) -> str:
    # تنظيف التوكن من أي مسافات أو علامات تنصيص عن طريق الخطأ
    clean_token = auth_token.strip().strip('"').strip("'")
    req = urllib.request.Request(ME_URL, headers={
        "authorization": clean_token, "user-agent": USER_AGENT, "x-super-properties": super_props
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Token rejected (HTTP {exc.code})") from exc
    token = data.get("analytics_token")
    if not token:
        raise RuntimeError("Missing analytics_token in response")
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
    except Exception:
        pass
    return Game("469433659223531536", "Visual Studio Code", "code.exe")

class StreamEngine:
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
                "voice_channel_id": self.state.voice_channel_id if self.state.voice_channel_id else None,
                "voice_channel_type": "guild_voice",
                "is_streaming": True,
                "video_enabled": True,
                "viewer_count": 2,
                "launch_signature": self.session.launch_signature,
                "client_app_state": "focused",
                "client_send_timestamp": now
            }
        }
        
        payload = {"token": self.state.analytics_token, "events": [event]}
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
    logger.info("Initializing Precise Discord Stream Spoofer...")
    state = State.load()
    
    if not state.token:
        token_input = input("Enter your Discord Token: ").strip()
        if not token_input:
            logger.error("Token is required.")
            sys.exit(1)
        state.token = token_input
        state.save()

    if not state.voice_channel_id:
        vc_input = input("Enter Voice Channel ID: ").strip()
        if vc_input:
            state.voice_channel_id = vc_input
            state.save()

    session = Session.new()
    try:
        logger.info("Authenticating with Discord API...")
        state.analytics_token = fetch_analytics_token(state.token, session.super_props)
        state.save()
        logger.info("Authentication successful!")
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        logger.info("Tip: Please check if your token is valid or update it.")
        sys.exit(1)

    game = fetch_primary_game()
    engine = StreamEngine(state, session, game)
    
    logger.info(f"Stream simulation started successfully for game: {game.name}")
    logger.info("Running loop... Press Ctrl+C to stop safely.")

    try:
        while True:
            status = engine.send_heartbeat(60000)
            if status == 204:
                state.total_minutes += 1
                state.save()
                logger.info(f"Heartbeat sent (204). Total tracked minutes: {state.total_minutes}")
            elif status == 401:
                logger.error("Token rejected (401 Unauthorized). Please update your token.")
                break
            else:
                logger.warning(f"Received status code {status}. Retrying next cycle...")
            
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopped by user. State saved successfully.")

if __name__ == "__main__":
    main()
