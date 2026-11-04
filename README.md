import discord
from discord.ext import commands, tasks
import json
import asyncio
import aiohttp
import time
import uuid
from pathlib import Path

# تنبيه: هذا الكود يعمل كسيلف بوت باستخدام مكتبة discord.py-self
bot = commands.Bot(command_prefix="&", self_bot=True, help_command=None)

# توكن حسابك الشخصي الأساسي
OWNER_TOKEN = ""

VOICE_CHANNEL_ID = "1514634823866650637"
SCIENCE_URL = "https://discord.com/api/v9/science"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) discord/1.0.9253 Chrome/148.0.7778.280 "
    "Electron/42.7.1 Safari/537.36"
)

VIEWERS_FILE = Path("viewer_tokens.json")

def load_json(file_path, default):
    if file_path.exists():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except:
            pass
    return default

viewer_tokens = load_json(VIEWERS_FILE, [
    "Mzc2ODU0MTIyODU2NDQ4MDAw.Gc_H7U.s2kjkol-i_uY2Zpne4vdBKNctX9e4LrpnpFjxU",
    "MzUyODU2MDU3NDkzNzE3MDAy.GYuHYX.e86eV53mfmIXmBWd3-gWVVAAU4xz1wgthk9pAc"
])

# قائمة الألعاب الموسعة
GAMES_CATALOG = [
    {"id": "1", "name": "Rocket League", "game_id": "310555104655114241", "exe": "RocketLeague.exe"},
    {"id": "2", "name": "Overwatch", "game_id": "290927767175241728", "exe": "Overwatch.exe"},
    {"id": "3", "name": "Minecraft", "game_id": "314050857321594882", "exe": "Minecraft.exe"},
    {"id": "4", "name": "Grand Theft Auto V", "game_id": "314049886738391040", "exe": "GTA5.exe"},
    {"id": "5", "name": "Valorant", "game_id": "782576926595563530", "exe": "VALORANT-Win64-Shipping.exe"},
    {"id": "6", "name": "Counter-Strike 2", "game_id": "766258933852086292", "exe": "cs2.exe"},
    {"id": "7", "name": "Visual Studio Code", "game_id": "469433659223531536", "exe": "code.exe"},
    {"id": "8", "name": "Fortnite", "game_id": "344449781498142721", "exe": "FortniteClient-Win64-Shipping.exe"},
    {"id": "9", "name": "Call of Duty: Warzone", "game_id": "736998688402227282", "exe": "cod.exe"},
    {"id": "10", "name": "League of Legends", "game_id": "280145694200676352", "exe": "League of Legends.exe"},
    {"id": "11", "name": "Apex Legends", "game_id": "544973348325998592", "exe": "r5apex.exe"},
    {"id": "12", "name": "Roblox", "game_id": "327771746684157952", "exe": "RobloxPlayerBeta.exe"},
    {"id": "13", "name": "Among Us", "game_id": "673179268383850556", "exe": "Among Us.exe"},
    {"id": "14", "name": "Cyberpunk 2077", "game_id": "382234471960248321", "exe": "Cyberpunk2077.exe"},
    {"id": "15", "name": "EA Sports FC 24", "game_id": "1098638361028780072", "exe": "FC24.exe"},
    {"id": "16", "name": "Dota 2", "game_id": "280695779699064834", "exe": "dota2.exe"},
    {"id": "17", "name": "Fall Guys", "game_id": "744217117188165682", "exe": "FallGuys_client_game.exe"},
    {"id": "18", "name": "Destiny 2", "game_id": "358482451000967168", "exe": "destiny2.exe"}
]

# حالة حسابك في السيلف بوت
user_state = {
    "game": GAMES_CATALOG[1], # الافتراضي Overwatch
    "running": False,
    "minutes": 0,
    "session_id": str(uuid.uuid4()),
    "seq": 0
}

@bot.event
async def on_ready():
    print(f"Self-Bot successfully logged in as {bot.user}!")
    if not self_stream_loop.is_running():
        self_stream_loop.start()

# مهمة إرسال النبضات في الخلفية لحسابك
@tasks.loop(minutes=1)
async def self_stream_loop():
    if not user_state["running"]:
        return

    user_state["seq"] += 1
    seq = user_state["seq"]
    now = int(time.time() * 1000)
    clean_token = OWNER_TOKEN.strip().strip('"').strip("'")
    game = user_state["game"]

    event = {
        "type": "running_game_heartbeat",
        "properties": {
            "client_track_timestamp": now,
            "client_heartbeat_session_id": user_state["session_id"],
            "event_sequence_number": seq,
            "game_id": game["game_id"],
            "game_name": game["name"],
            "game_executable": game["exe"],
            "initial_heartbeat": (seq == 1),
            "final_heartbeat": False,
            "game_session_id": str(uuid.uuid4()),
            "duration_tracked_ms": 60000,
            "voice_channel_id": VOICE_CHANNEL_ID,
            "voice_channel_type": "guild_voice",
            "is_streaming": True,
            "video_enabled": True,
            "screen_readout": True,
            "viewer_count": len(viewer_tokens),
            "client_app_state": "focused",
            "client_send_timestamp": now
        }
    }

    payload = {"token": clean_token, "events": [event]}
    headers = {
        "Authorization": clean_token,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Origin": "https://discord.com",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQifQ=="
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(SCIENCE_URL, json=payload, headers=headers, timeout=10) as resp:
                if resp.status in (200, 202, 204):
                    user_state["minutes"] += 1
                    print(f"[SELF-STREAM] Heartbeat sent | Minutes: {user_state['minutes']}")
                elif resp.status == 401:
                    print("[ERROR] Token rejected (401). Stopping stream.")
                    user_state["running"] = False
        except Exception as e:
            print(f"[ERROR] Failed: {e}")

@self_stream_loop.before_loop
async def before_loop():
    await bot.wait_until_ready()


# --- أوامر التحكم الخاصة بك (تكتبها من حسابك في أي مكان مثل رسايلك الخاصة) ---

@bot.command(name="setgame")
async def set_game(ctx, game_number: str):
    try:
        await ctx.message.delete()
    except:
        pass
    
    selected = next((g for g in GAMES_CATALOG if g["id"] == game_number), None)
    if not selected:
        msg = await ctx.send("❌ رقم اللعبة غير صحيح. تأكد من الأرقام الصحيحة.")
        await asyncio.sleep(4)
        await msg.delete()
        return
    
    user_state["game"] = selected
    msg = await ctx.send(f"🎮 **تم تغيير لعبتك إلى:** `{selected['name']}` بنجاح!")
    await asyncio.sleep(5)
    await msg.delete()

@bot.command(name="start")
async def start_stream(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    user_state["running"] = True
    msg = await ctx.send("🚀 **تم تشغيل السيلف بوت وبث الألعاب والساعات بنجاح!**")
    await asyncio.sleep(5)
    await msg.delete()

@bot.command(name="stop")
async def stop_stream(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    user_state["running"] = False
    msg = await ctx.send("🛑 **تم إيقاف السيلف بوت وبث الألعاب.**")
    await asyncio.sleep(5)
    await msg.delete()

@bot.command(name="mystatus")
async def my_status(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    status = "🟢 يعمل" if user_state["running"] else "🔴 متوقف"
    game_name = user_state["game"]["name"]
    minutes = user_state["minutes"]
    
    msg = await ctx.send(
        f"📊 **حالة السيلف بوت الخاصة بك:**\n"
        f"- الحالة: {status}\n"
        f"- اللعبة: `{game_name}`\n"
        f"- الدقائق: {minutes} دقيقة"
    )
    await asyncio.sleep(10)
    await msg.delete()

@bot.command(name="help")
async def self_help(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    help_text = (
        "📚 **أوامر السيلف بوت الخاصة بك:**\n"
        "`&setgame <رقم>` ➔ لاختيار اللعبة (مثال: `&setgame 1` لـ Rocket League)\n"
        "`&start` ➔ لبدء البث والساعات\n"
        "`&stop` ➔ لإيقاف البث\n"
        "`&mystatus` ➔ لمعرفة الدقائق والحالة"
    )
    msg = await ctx.send(help_text)
    await asyncio.sleep(15)
    await msg.delete()

# تشغيل السيلف بوت باستخدام توكن حسابك الشخصي
bot.run(OWNER_TOKEN, bot=False)
