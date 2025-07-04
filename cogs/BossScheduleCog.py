import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import pytz
import os
import asyncio



class BossScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boss_times = [
            (13, "2 Peace Boss, 1 Conflict Boss"),
            (16, "2 Peace Boss, 1 Conflict Boss"),
            (20, "4 Peace Boss, 3 Conflict Boss"),
            (22, "3 Peace Boss, 2 Conflict Boss"),
            (1, "2 Peace Boss, 2 Conflict Boss")
        ]
        self.tz = pytz.timezone('Europe/Berlin')
        self.archboss_cycle_state = None

    async def cog_load(self):
        await self.async_load_archboss_cycle_state()

    async def async_load_archboss_cycle_state(self):
        try:
            query = "SELECT cycle_state FROM archboss_cycle WHERE status = 1 LIMIT 1"
            record = await self.bot.db.pool.fetchrow(query)
            if record:
                self.archboss_cycle_state = record['cycle_state']
            else:
                # If no active cycle, activate the first row (default Conflict)
                await self.bot.db.pool.execute("UPDATE archboss_cycle SET status = 1 WHERE id = 1")
                self.archboss_cycle_state = "Conflict"
        except Exception as e:
            self.archboss_cycle_state = "Conflict"

    async def update_archboss_cycle_state(self, next_archboss_time):
        now = datetime.now(self.tz)
        if now >= next_archboss_time:
            try:
                query = "SELECT id FROM archboss_cycle WHERE status = 1 LIMIT 1"
                record = await self.bot.db.pool.fetchrow(query)
                if record:
                    current_id = record['id']
                    next_id = current_id + 1 if current_id < 4 else 1
                    # Deactivate the current one
                    await self.bot.db.pool.execute("UPDATE archboss_cycle SET status = 0 WHERE id = $1", current_id)
                    # Activate the next one
                    await self.bot.db.pool.execute("UPDATE archboss_cycle SET status = 1 WHERE id = $1", next_id)
                # Reload state after update
                await self.async_load_archboss_cycle_state()
            except Exception as e:
                print("Useless Printing we already know")

    async def get_guild_settings(self, guild_id):
        try:
            query = "SELECT channel_id, role_id FROM guild_settings WHERE guild_id = $1"
            record = await self.bot.db.pool.fetchrow(query, str(guild_id))
            if record:
                return dict(record)
            else:
                return None
        except Exception as e:
            print("Pffffufufufufufu.")
            return None

    def get_next_boss_info(self):
        now = datetime.now(self.tz)
        for hour, info in self.boss_times:
            boss_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if boss_time > now:
                return boss_time, info
        next_day = now + timedelta(days=1)
        midnight_boss = next((time for time in self.boss_times if time[0] == 0), None)
        if midnight_boss:
            return next_day.replace(hour=0, minute=0, second=0, microsecond=0), midnight_boss[1]
        return next_day.replace(hour=self.boss_times[0][0], minute=0, second=0, microsecond=0), self.boss_times[0][1]

    def get_next_archboss_info(self):
        now = datetime.now(self.tz)
        next_wednesday = now + timedelta((2 - now.weekday()) % 7)
        next_saturday = now + timedelta((5 - now.weekday()) % 7)
        if next_wednesday < next_saturday:
            next_archboss_date = next_wednesday
        else:
            next_archboss_date = next_saturday
        next_archboss_time = next_archboss_date.replace(hour=20, minute=0, second=0, microsecond=0)
        return next_archboss_time, self.archboss_cycle_state or "Conflict"

    @app_commands.command(name="boss_schedule", description="Displays the next boss schedule.")
    async def boss_schedule(self, interaction: discord.Interaction):
        next_boss_time, next_boss_info = self.get_next_boss_info()
        next_archboss_time, next_archboss_info = self.get_next_archboss_info()
        settings = await self.get_guild_settings(interaction.guild.id)
        role_mention = f"<@&{settings['role_id']}>" if settings else "No role configured."

        # Embed formatting with corrected newlines
        embed = discord.Embed(title="🕰 Next Boss Spawn Schedule", color=discord.Color.green())
        embed.add_field(
            name="Next Boss",
            value=f"**Time** : <t:{int(next_boss_time.timestamp())}:R>\n**Boss** : {next_boss_info}",
            inline=False
        )

        # Determine the emoji for the cycle
        archboss_emoji = "🔴" if "Conflict" in next_archboss_info else "🟢"
        if next_archboss_time and next_archboss_time < next_boss_time:
            embed.add_field(
                name=f"⚔️ Next Archboss (High Priority!) {archboss_emoji}",
                value=f"**Time** : <t:{int(next_archboss_time.timestamp())}:R>\n**Boss** : {next_archboss_info}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"Next Archboss {archboss_emoji}",
                value=f"**Time** : <t:{int(next_archboss_time.timestamp())}:R>\n**Boss** : {next_archboss_info}",
                inline=False
            )

        embed.add_field(
            name="Boss Spawn Reminder Role",
            value=(f"{role_mention}\nReact with the emoji below to get the reminder!"),
            inline=False
        )
        embed.set_thumbnail(url="https://i.postimg.cc/nhxm8mxd/photodeshrek.png")
        embed.set_footer(text="All times are in Berlin time (CET/CEST).")

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("⏰")
        reaction = discord.utils.get(message.reactions, emoji="⏰")
        if reaction and reaction.me:
            await reaction.remove(self.bot.user)

async def setup(bot):
    await bot.add_cog(BossScheduleCog(bot))