import os
import discord
from discord.ext import commands, tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime, timedelta
import unicodedata
import asyncio
import asyncpg

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
scheduler = AsyncIOScheduler(timezone="Europe/Paris")

def default_event_status():
    return {
        "boonstone": False,
        "riftstone": False,
        "siege": False,
        "tax": False
    }

event_status = default_event_status()

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS event_status (
            event TEXT PRIMARY KEY,
            enabled BOOLEAN NOT NULL
        )
    """)
    for event, enabled in default_event_status().items():
        await conn.execute(
            """
            INSERT INTO event_status(event, enabled)
            VALUES($1,$2) ON CONFLICT(event) DO NOTHING
            """, event, enabled
        )
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS vote_results (
            id SERIAL PRIMARY KEY,
            type TEXT NOT NULL,
            option TEXT NOT NULL,
            count INTEGER NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await conn.close()

async def load_event_status():
    global event_status
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT event, enabled FROM event_status")
    await conn.close()
    event_status = {r['event']: r['enabled'] for r in rows}

async def save_event_status():
    conn = await asyncpg.connect(DATABASE_URL)
    for event, enabled in event_status.items():
        await conn.execute("UPDATE event_status SET enabled=$1 WHERE event=$2", enabled, event)
    await conn.close()

@bot.command()
async def activate(ctx, event: str):
    key = event.lower()
    if key in event_status:
        event_status[key] = True
        await save_event_status()
        await ctx.send(f"Activated {key} reminders.")
    else:
        await ctx.send("Unknown event. Options: boonstone, riftstone, siege, tax.")

@bot.command()
async def deactivate(ctx, event: str):
    key = event.lower()
    if key in event_status:
        event_status[key] = False
        await save_event_status()
        await ctx.send(f"Deactivated {key} reminders.")
    else:
        await ctx.send("Unknown event. Options: boonstone, riftstone, siege, tax.")

@bot.command()
async def status(ctx):
    lines = [f"{e.capitalize()}: {'ON' if state else 'OFF'}" for e, state in event_status.items()]
    await ctx.send("Reminder Status\n" + "\n".join(lines))

@bot.command()
async def testsend(ctx):
    ch = bot.get_channel(ctx.channel.id)
    await ch.send("testsend: send perms are good!")
    await ctx.send("and I just tested it.")

@bot.event
async def on_member_join(member):
    guild = member.guild
    staff_role = discord.utils.get(guild.roles, name="Staff")
    if not staff_role:
        return
    category = discord.utils.get(guild.categories, name="O N B O A R D I N G")
    if not category:
        category = await guild.create_category("O N B O A R D I N G")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
        staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True)
    }
    safe = unicodedata.normalize("NFKD", member.name).encode('ascii','ignore').decode().lower()
    channel = await guild.create_text_channel(
        name=f"build-{safe}", category=category,
        overwrites=overwrites,
        topic=f"Private channel for {member.display_name} gear review"
    )
    await channel.send(f"Welcome {member.mention}!\nPlease share a screenshot of your current gear and build.\nThis channel will remain open for questions related to your build or requests for items from guild storage.")

from discord import ButtonStyle, Interaction
from discord.ui import View, Button

class PollButton(Button):
    def __init__(self, label: str, counts: dict, voters: dict):
        super().__init__(style=ButtonStyle.primary, label=label)
        self.counts = counts
        self.voters = voters

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        prev = self.voters.get(user_id)
        if prev:
            self.counts[p]()
