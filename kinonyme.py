import os
import discord
from discord.ext import commands
import asyncpg
from db.models import GuildConfigDB

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

TEST_GUILD_ID = 1389539957265399939 

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        guild = discord.Object(id=TEST_GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to test guild.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def setup_db():
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    bot.db = GuildConfigDB(pool)

async def main():
    await setup_db()
    await bot.load_extension("cogs.config")
    await bot.load_extension("cogs.onboarding")
    await bot.load_extension("cogs.GuildMemberCommand")
    await bot.load_extension("cogs.BossTimerRoleCog")
    await bot.load_extension("cogs.CommandDrops")
    await bot.load_extension("cogs.BossScheduleCog")
    await bot.load_extension("cogs.WeeklyGuideBoss")
    await bot.load_extension("cogs.BossReminderCogs")
    await bot.load_extension("cogs.GuildStatsCommand")
    # (load other cogs as you add them)
    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
