import asyncio
import re
import time
import aiohttp
import discord
from discord.ext import commands

try:
    from curl_cffi.requests import AsyncSession
    _c_ws = AsyncSession.ws_connect
    def _patched_c_ws(self, *a, **kw):
        kw["max_message_size"] = 50 * 1024 * 1024
        return _c_ws(self, *a, **kw)
    AsyncSession.ws_connect = _patched_c_ws
except Exception:
    pass

_a_ws = aiohttp.ClientSession.ws_connect
def _patched_a_ws(self, *a, **kw):
    kw["max_msg_size"] = 0
    return _a_ws(self, *a, **kw)
aiohttp.ClientSession.ws_connect = _patched_a_ws

TOKEN = ""

GAMES_LIST = [
    "Resident Evil 0", "Resident Evil", "Resident Evil 2", "Resident Evil 3", "Resident Evil 4", "Resident Evil 5", "Resident Evil 6", "Resident Evil 7: Biohazard", "Resident Evil Village", "Resident Evil 2 Remake",
    "Resident Evil 3 Remake", "Resident Evil 4 Remake", "Resident Evil CODE: Veronica X", "Resident Evil: Revelations", "Resident Evil: Revelations 2", "Resident Evil Outbreak", "Resident Evil Outbreak: File #2", "Resident Evil: Operation Raccoon City", "Resident Evil: Resistance", "Resident Evil Re:Verse",
    "Resident Evil: Umbrella Corps", "Resident Evil: Dead Aim", "Resident Evil Survivor", "Resident Evil: The Umbrella Chronicles", "Resident Evil: The Darkside Chronicles", "Silent Hill", "Silent Hill 2", "Silent Hill 2 Remake", "Silent Hill 3", "Silent Hill 4: The Room",
    "Grand Theft Auto V", "Grand Theft Auto IV", "Grand Theft Auto: San Andreas", "Grand Theft Auto: Vice City", "Grand Theft Auto III", "Red Dead Redemption 2", "Red Dead Redemption", "Max Payne 3", "L.A. Noire", "Bully: Scholarship Edition",
    "Call of Duty: Warzone", "Call of Duty: Black Ops 6", "Call of Duty: Modern Warfare III", "Call of Duty: Modern Warfare II", "Call of Duty: Modern Warfare", "Call of Duty: Black Ops Cold War", "Call of Duty: Vanguard", "Call of Duty: Black Ops III", "Call of Duty: Black Ops II", "Call of Duty: Black Ops",
    "Call of Duty: WWII", "Call of Duty: Infinite Warfare", "Call of Duty: Advanced Warfare", "Call of Duty: Ghosts", "Call of Duty 4: Modern Warfare", "Call of Duty: Modern Warfare 2 (2009)", "Call of Duty: Modern Warfare 3 (2011)", "Call of Duty: World at War", "Call of Duty: Mobile", "Call of Duty: Roads to Victory",
    "Assassin's Creed Mirage", "Assassin's Creed Valhalla", "Assassin's Creed Odyssey", "Assassin's Creed Origins", "Assassin's Creed Syndicate", "Assassin's Creed Unity", "Assassin's Creed IV: Black Flag", "Assassin's Creed Rogue", "Assassin's Creed III", "Assassin's Creed Revelations",
    "Assassin's Creed Brotherhood", "Assassin's Creed II", "Assassin's Creed", "Far Cry 6", "Far Cry 5", "Far Cry 4", "Far Cry 3", "Far Cry 2", "Far Cry Primal", "Far Cry New Dawn",
    "Battlefield 2042", "Battlefield V", "Battlefield 1", "Battlefield 4", "Battlefield 3", "Battlefield Hardline", "Battlefield: Bad Company 2", "Battlefield 2", "Delta Force", "BattleBit Remastered",
    "EA Sports FC 25", "EA Sports FC 24", "FIFA 23", "FIFA 22", "FIFA 21", "eFootball 2025", "PES 2021", "Rocket League", "Rematch", "Football Manager 2024",
    "Need for Speed Unbound", "Need for Speed Heat", "Need for Speed Payback", "Need for Speed (2015)", "Need for Speed Rivals", "Need for Speed: Most Wanted", "Need for Speed: Carbon", "Need for Speed: Underground 2", "Need for Speed: Hot Pursuit", "Need for Speed: ProStreet",
    "Forza Horizon 5", "Forza Horizon 4", "Forza Motorsport", "Gran Turismo 7", "Assetto Corsa", "Assetto Corsa Competizione", "F1 24", "F1 23", "The Crew Motorfest", "The Crew 2",
    "Valorant", "Counter-Strike 2", "Counter-Strike: Source", "Counter-Strike 1.6", "Overwatch 2", "Apex Legends", "Fortnite", "PUBG: Battlegrounds", "Tom Clancy's Rainbow Six Siege", "THE FINALS",
    "League of Legends", "Dota 2", "World of Warcraft", "Diablo IV", "Diablo III", "Diablo II: Resurrected", "Hearthstone", "Team Fortress 2", "StarCraft II", "Heroes of the Storm",
    "Elden Ring", "Dark Souls: Remastered", "Dark Souls II", "Dark Souls III", "Sekiro: Shadows Die Twice", "Bloodborne", "Demon's Souls", "Armored Core VI: Fires of Rubicon", "Lies of P", "Lords of the Fallen",
    "God of War Ragnarök", "God of War", "God of War III", "Marvel's Spider-Man 2", "Marvel's Spider-Man Remastered", "Marvel's Spider-Man: Miles Morales", "Ghost of Tsushima", "The Last of Us Part I", "The Last of Us Part II", "Uncharted 4: A Thief's End",
    "Horizon Forbidden West", "Horizon Zero Dawn", "Days Gone", "Batman: Arkham Knight", "Batman: Arkham City", "Batman: Arkham Asylum", "Batman: Arkham Origins", "Suicide Squad: Kill the Justice League", "Gotham Knights", "Injustice 2",
    "The Witcher 3: Wild Hunt", "The Witcher 2", "The Witcher", "Cyberpunk 2077", "The Elder Scrolls V: Skyrim", "The Elder Scrolls IV: Oblivion", "The Elder Scrolls III: Morrowind", "Fallout 4", "Fallout: New Vegas", "Fallout 3",
    "Fallout 76", "Starfield", "Mass Effect Legendary Edition", "Mass Effect: Andromeda", "Dragon Age: The Veilguard", "Dragon Age: Inquisition", "Dragon Age: Origins", "Kingdom Come: Deliverance", "Mount & Blade II: Bannerlord", "Mount & Blade: Warband",
    "Final Fantasy XVI", "Final Fantasy VII Rebirth", "Final Fantasy VII Remake", "Final Fantasy XV", "Final Fantasy XIV Online", "Final Fantasy X/X-2 HD Remaster", "Final Fantasy XII", "Final Fantasy XIII", "Crisis Core: Final Fantasy VII", "Stranger of Paradise: Final Fantasy Origin",
    "Devil May Cry 5", "Devil May Cry 4", "Devil May Cry 3", "DmC: Devil May Cry", "Metal Gear Solid V: The Phantom Pain", "Metal Gear Solid V: Ground Zeroes", "Metal Gear Solid 3: Snake Eater", "Metal Gear Solid 2", "Metal Gear Solid", "Metal Gear Rising: Revengeance",
    "Monster Hunter: World", "Monster Hunter Rise", "Monster Hunter Wilds", "Persona 5 Royal", "Persona 3 Reload", "Persona 4 Golden", "Metaphor: ReFantazio", "Like a Dragon: Infinite Wealth", "Yakuza: Like a Dragon", "Yakuza 0",
    "Tekken 8", "Tekken 7", "Mortal Kombat 1", "Mortal Kombat 11", "Mortal Kombat X", "Street Fighter 6", "Street Fighter V", "Guilty Gear -Strive-", "Dragon Ball: Sparking! ZERO", "Dragon Ball FighterZ",
    "Dragon Ball Xenoverse 2", "Dragon Ball Z: Kakarot", "Naruto X Boruto Ultimate Ninja Storm Connections", "Naruto Shippuden: Ultimate Ninja Storm 4", "One Piece Odyssey", "One Piece: Pirate Warriors 4", "Demon Slayer: The Hinokami Chronicles", "Attack on Titan 2", "Genshin Impact", "Honkai: Star Rail",
    "Minecraft", "Roblox", "Terraria", "Rust", "ARK: Survival Ascended", "ARK: Survival Evolved", "DayZ", "Subnautica", "The Forest", "Sons of the Forest",
    "Valheim", "Palworld", "Enshrouded", "V Rising", "No Man's Sky", "Sea of Thieves", "Grounded", "Raft", "Don't Starve Together", "Astroneer",
    "Phasmophobia", "Lethal Company", "Dead by Daylight", "Outlast", "Outlast 2", "The Outlast Trials", "Alien: Isolation", "Amnesia: The Bunker", "Amnesia: The Dark Descent", "SOMA",
    "Dying Light 2 Stay Human", "Dying Light", "Dead Island 2", "Dead Island", "Left 4 Dead 2", "Left 4 Dead", "Back 4 Blood", "World War Z", "State of Decay 2", "7 Days to Die",
    "DOOM Eternal", "DOOM (2016)", "DOOM 3", "Wolfenstein II: The New Colossus", "Wolfenstein: The New Order", "Quake Champions", "Half-Life 2", "Half-Life", "Half-Life: Alyx", "Black Mesa",
    "Halo Infinite", "Halo: The Master Chief Collection", "Gears 5", "Gears of War 4", "Dead Space", "Dead Space 2", "Dead Space 3", "BioShock Infinite", "BioShock", "BioShock 2",
    "Crysis Remastered", "Crysis 2", "Crysis 3", "Metro Exodus", "Metro: Last Light Redux", "Metro 2033 Redux", "S.T.A.L.K.E.R. 2: Heart of Chornobyl", "S.T.A.L.K.E.R.: Shadow of Chernobyl", "Atomic Heart", "Chernobylite",
    "Borderlands 3", "Borderlands 2", "Borderlands", "Tiny Tina's Wonderlands", "Dishonored 2", "Dishonored", "Prey", "Deathloop", "Control", "Alan Wake 2",
    "Alan Wake", "Quantum Break", "Hitman World of Assassination", "Hitman: Absolution", "Hitman: Blood Money", "Shadow of the Tomb Raider", "Rise of the Tomb Raider", "Tomb Raider", "Mafia: Definitive Edition", "Mafia II",
    "Mafia III", "Watch Dogs: Legion", "Watch Dogs 2", "Watch Dogs", "Tom Clancy's The Division 2", "Tom Clancy's The Division", "Tom Clancy's Ghost Recon Breakpoint", "Tom Clancy's Ghost Recon Wildlands", "Tom Clancy's Splinter Cell: Blacklist", "Just Cause 4",
    "Just Cause 3", "Just Cause 2", "Saints Row", "Saints Row: The Third", "Saints Row IV", "Sleeping Dogs", "Payday 3", "Payday 2", "Mad Max", "Rage 2",
    "Star Wars Jedi: Survivor", "Star Wars Jedi: Fallen Order", "Star Wars Outlaws", "Star Wars Battlefront II", "Star Wars: Squadrons", "Hogwarts Legacy", "Middle-earth: Shadow of War", "Middle-earth: Shadow of Mordor", "Marvel's Guardians of the Galaxy", "Marvel's Avengers",
    "Baldur's Gate 3", "Divinity: Original Sin 2", "Path of Exile", "Path of Exile 2", "Pillars of Eternity II", "Disco Elysium", "Dragon's Dogma 2", "Dragon's Dogma: Dark Arisen", "NieR:Automata", "NieR Replicant",
    "Black Myth: Wukong", "Stellar Blade", "Nioh 2", "Nioh", "Wo Long: Fallen Dynasty", "Rise of the Ronin", "Code Vein", "Scarlet Nexus", "Tales of Arise", "Granblue Fantasy: Relink",
    "Sid Meier's Civilization VI", "Sid Meier's Civilization V", "Age of Empires IV", "Age of Empires II: Definitive Edition", "Age of Mythology: Retold", "Warcraft III: Reforged", "Command & Conquer Remastered", "Total War: WARHAMMER III", "Total War: ROME II", "Hearts of Iron IV",
    "Europa Universalis IV", "Crusader Kings III", "Stellaris", "Company of Heroes 3", "XCOM 2", "Frostpunk 2", "Frostpunk", "Manor Lords", "Anno 1800", "Tropico 6",
    "Cities: Skylines II", "Cities: Skylines", "The Sims 4", "The Sims 3", "Euro Truck Simulator 2", "American Truck Simulator", "Microsoft Flight Simulator", "Farming Simulator 22", "Planet Zoo", "Planet Coaster",
    "Factorio", "RimWorld", "Satisfactory", "Dyson Sphere Program", "Oxygen Not Included", "Prison Architect", "Two Point Hospital", "Two Point Campus", "PowerWash Simulator", "House Flipper 2",
    "Hollow Knight", "Celeste", "Cuphead", "Undertale", "Deltarune", "Hades", "Hades II", "Dead Cells", "Ori and the Will of the Wisps", "Ori and the Blind Forest",
    "Stardew Valley", "The Binding of Isaac: Rebirth", "Slay the Spire", "Balatro", "Vampire Survivors", "Risk of Rain 2", "Enter the Gungeon", "Darkest Dungeon", "Cult of the Lamb", "Dave the Diver",
    "Among Us", "Fall Guys", "Gang Beasts", "Party Animals", "Human: Fall Flat", "It Takes Two", "A Way Out", "Overcooked! 2", "Pummel Party", "Content Warning",
    "Escape from Tarkov", "Hunt: Showdown 1896", "Squad", "Arma 3", "Insurgency: Sandstorm", "Hell Let Loose", "Ready or Not", "Gray Zone Warfare", "SCUM", "Zero Hour",
    "Garry's Mod", "BeamNG.drive", "Teardown", "Kerbal Space Program", "Space Engineers", "People Playground", "Totally Accurate Battle Simulator", "Goat Simulator 3", "Portal 2", "Portal",
    "Detroit: Become Human", "Heavy Rain", "Beyond: Two Souls", "Until Dawn", "The Quarry", "Life is Strange", "The Walking Dead: The Telltale Series", "The Wolf Among Us", "Stray", "Outer Wilds",
    "Crash Bandicoot 4", "Spyro Reignited Trilogy", "Sonic Frontiers", "Sonic X Shadow Generations", "Little Nightmares II", "Little Nightmares", "INSIDE", "LIMBO", "Subway Surfers", "Brawl Stars",
    "NBA 2K25", "WWE 2K24", "Madden NFL 25", "EA Sports UFC 5", "Destiny 2", "Warframe", "Helldivers 2", "Warhammer 40,000: Space Marine 2", "For Honor", "Visual Studio Code"
]

GAMES = {str(i): name for i, name in enumerate(GAMES_LIST, 1)}
APP_DB = []

bot = commands.Bot(
    command_prefix="&",
    self_bot=True,
    chunk_guilds_at_startup=False,
    help_command=None
)

state = {
    "game": "Dead by Daylight",
    "app_id": 381889378202451979,
    "active": False,
    "start_ts": 0
}

def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()

async def load_discord_apps():
    global APP_DB
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://discord.com/api/v9/applications/detectable", timeout=15) as r:
                if r.status == 200:
                    APP_DB = await r.json()
    except Exception:
        pass

def find_app_id(game_name):
    raw = game_name.lower().strip()
    clean = norm(game_name.replace("Remake", "").replace("Remastered", ""))

    for app in APP_DB:
        names = [app.get("name", "")] + app.get("aliases", [])
        if any(raw == n.lower() for n in names):
            return int(app["id"]), app["name"]

    for app in APP_DB:
        names = [app.get("name", "")] + app.get("aliases", [])
        if any(clean == norm(n) for n in names):
            return int(app["id"]), app["name"]

    candidates = []
    for app in APP_DB:
        names = [app.get("name", "")] + app.get("aliases", [])
        for n in names:
            nn = norm(n)
            if clean and clean in nn:
                candidates.append((len(nn), int(app["id"]), app["name"]))
    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1], candidates[0][2]

    return None, game_name

async def update_rpc():
    if not state["active"]:
        await bot.change_presence(activity=None)
        return
    kwargs = {
        "type": discord.ActivityType.playing,
        "name": state["game"],
        "timestamps": {"start": int(state["start_ts"] * 1000)}
    }
    if state["app_id"]:
        kwargs["application_id"] = state["app_id"]
    await bot.change_presence(activity=discord.Activity(**kwargs))

@bot.event
async def on_ready():
    await load_discord_apps()
    app_id, official = find_app_id(state["game"])
    if app_id:
        state["app_id"] = app_id
        state["game"] = official
    print(f"Ready: {bot.user} | Games: {len(GAMES)} | Icons DB: {len(APP_DB)}")

@bot.before_invoke
async def auto_del(ctx):
    try:
        await ctx.message.delete()
    except Exception:
        pass

async def temp_msg(ctx, text, delay=6):
    try:
        m = await ctx.send(text)
        await asyncio.sleep(delay)
        await m.delete()
    except Exception:
        pass

@bot.command()
async def games(ctx, page: int = 1):
    per_page = 50
    total_pages = (len(GAMES_LIST) + per_page - 1) // per_page
    if page < 1 or page > total_pages:
        return
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    items = [f"`{i}` - {GAMES_LIST[i-1]}" for i in range(start_idx + 1, min(end_idx, len(GAMES_LIST)) + 1)]
    txt = f"**Page {page}/{total_pages}**\n" + "\n".join(items)
    await temp_msg(ctx, txt, 15)

@bot.command()
async def search(ctx, *, query: str):
    q = query.lower()
    matches = [f"`{k}` - {v}" for k, v in GAMES.items() if q in v.lower()]
    if not matches:
        await temp_msg(ctx, "No match.")
        return
    await temp_msg(ctx, "\n".join(matches[:30]), 15)

@bot.command()
async def setgame(ctx, *, arg: str):
    chosen = GAMES.get(arg, arg)
    app_id, official_name = find_app_id(chosen)
    state["game"] = official_name if app_id else chosen
    state["app_id"] = app_id
    if state["active"]:
        await update_rpc()
    icon_state = "Icon OK" if app_id else "No Icon"
    await temp_msg(ctx, f"Game: `{state['game']}` ({icon_state})")

@bot.command()
async def settime(ctx, minutes: int):
    state["start_ts"] = time.time() - (minutes * 60)
    if state["active"]:
        await update_rpс() if 'update_rpс' in globals() else await update_rpc()
    await temp_msg(ctx, f"Timer: `{minutes}m`")

@bot.command()
async def start(ctx):
    state["active"] = True
    if state["start_ts"] == 0:
        state["start_ts"] = time.time()
    await update_rpc()
    await temp_msg(ctx, f"Started: `{state['game']}`")

@bot.command()
async def stop(ctx):
    state["active"] = False
    state["start_ts"] = 0
    await update_rpc()
    await temp_msg(ctx, "Stopped.")

@bot.command()
async def status(ctx):
    st = "ON" if state["active"] else "OFF"
    mins = int((time.time() - state["start_ts"]) // 60) if state["active"] else 0
    await temp_msg(ctx, f"State: `{st}` | Game: `{state['game']}` | Time: `{mins}m`", 8)

@bot.command()
async def help(ctx):
    txt = (
        "**Games Commands:**\n"
        "`&games <1-10>`\n"
        "`&search <name>`\n"
        "`&setgame <num or name>`\n"
        "`&settime <minutes>`\n"
        "`&start` | `&stop` | `&status`"
    )
    await temp_msg(ctx, txt, 10)

bot.run(TOKEN)
