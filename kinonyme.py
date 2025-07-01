import os
import discord
from discord.ext import commands
import asyncpg
from db.models import GuildConfigDB

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def setup_db():
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    bot.db = GuildConfigDB(pool)

async def main():
    await setup_db()
    await bot.load_extension("cogs.config")
    await bot.load_extension("cogs.onboarding")
    # (load other cogs as you add them)
    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
