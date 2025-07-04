import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import pytz
import os
import asyncio



class BossReminderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tz = pytz.timezone('UTC')  # Setting timezone to UTC
        self.reminders_sent = {}  # Track sent reminders per guild and boss type
        self.boss_reminder_task.start()

    def cog_unload(self):
        self.boss_reminder_task.cancel()

    async def get_guild_settings(self, guild_id):
        try:
            query = "SELECT channel_id, role_id FROM guild_settings WHERE guild_id = $1"
            record = await self.bot.db.pool.fetchrow(query, str(guild_id))
            if record:
                return dict(record)
            else:
                return None
        except Exception as e:
            return None

    def get_next_boss_time(self):
        now = datetime.now(self.tz)
        daily_spawn_times = [12, 15, 19, 21, 0]  # Original spawn times for normal bosses
        for hour in daily_spawn_times:
            boss_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if boss_time > now:
                return boss_time, "Normal Boss"
        next_day = now + timedelta(days=1)
        next_boss_time = next_day.replace(hour=0, minute=0, second=0, microsecond=0)
        return next_boss_time, "Normal Boss"

    def get_next_archboss_time(self):
        now = datetime.now(self.tz)
        next_wednesday = now + timedelta((2 - now.weekday()) % 7)
        next_saturday = now + timedelta((5 - now.weekday()) % 7)
        archboss_times = [
            next_wednesday.replace(hour=19, minute=0, second=0, microsecond=0),
            next_saturday.replace(hour=19, minute=0, second=0, microsecond=0)
        ]
        for archboss_time in archboss_times:
            if archboss_time > now:
                return archboss_time, "Archboss"
        next_week_wednesday = next_wednesday + timedelta(weeks=1)
        return next_week_wednesday.replace(hour=19, minute=0, second=0, microsecond=0), "Archboss"

    @tasks.loop(minutes=1)
    async def boss_reminder_task(self):
        now = datetime.now(self.tz)
        next_boss_time, boss_type = self.get_next_boss_time()
        next_archboss_time, archboss_type = self.get_next_archboss_time()

        for guild in self.bot.guilds:
            guild_settings = await self.get_guild_settings(guild.id)

            # Skip if the guild hasn't set up the channel and role in the database
            if not guild_settings:
                continue

            channel_id = guild_settings.get("channel_id")
            role_id = guild_settings.get("role_id")
            
            channel = guild.get_channel(channel_id) if channel_id else None
            role = guild.get_role(role_id) if role_id else None

            if guild.id not in self.reminders_sent:
                self.reminders_sent[guild.id] = {"Normal Boss": False, "Archboss": False}

            # Normal Boss Reminder
            if (next_boss_time - now).total_seconds() <= 900:  # 15 minutes before the spawn
                if not self.reminders_sent[guild.id]["Normal Boss"]:
                    self.reminders_sent[guild.id]["Normal Boss"] = True
                    if channel:
                        try:
                            await channel.send(f"{role.mention if role else ''} Rappel : Un **{boss_type}** apparaîtra dans 15 minutes à <t:{int(next_boss_time.timestamp())}:t>.")
                        except discord.Forbidden:
                            logger.error(f"[ERROR] Accès refusé au salon {channel.id} dans la guilde {guild.id}.")
                        except discord.HTTPException as e:
                            logger.error(f"[ERROR] Échec de l'envoi du message dans la guilde {guild.id} : {e}")
            else:
                self.reminders_sent[guild.id]["Normal Boss"] = False

            # Archboss Reminder
            if (next_archboss_time - now).total_seconds() <= 900:  # 15 minutes before the spawn
                if not self.reminders_sent[guild.id]["Archboss"]:
                    self.reminders_sent[guild.id]["Archboss"] = True
                    if channel:
                        try:
                            await channel.send(f"{role.mention if role else ''} Rappel : Un **{archboss_type}** apparaîtra dans 15 minutes à <t:{int(next_archboss_time.timestamp())}:t>.")
                        except discord.Forbidden:
                            logger.error(f"[ERROR] Accès refusé au salon {channel.id} dans la guilde {guild.id}.")
                        except discord.HTTPException as e:
                            logger.error(f"[ERROR] Échec de l'envoi du message dans la guilde {guild.id} : {e}")
            else:
                self.reminders_sent[guild.id]["Archboss"] = False

    @boss_reminder_task.before_loop
    async def before_boss_reminder_task(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="set_boss_channel", description="Set the channel and role for the boss reminder.")
    async def set_boss_channel(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
        try:
            query = """
                INSERT INTO guild_settings (guild_id, channel_id, role_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id)
                DO UPDATE SET channel_id = $2, role_id = $3
            """
            await self.bot.db.pool.execute(query, str(interaction.guild.id), channel.id, role.id)
            await interaction.response.send_message(f"The boss reminder channel is set to {channel.mention} with the role {role.mention}.")
        except Exception as e:
            logger.error(f"[ERROR] PostgreSQL set_boss_channel: {e}")
            await interaction.response.send_message("Failed to configure the boss reminder channel (database error).", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BossReminderCog(bot))