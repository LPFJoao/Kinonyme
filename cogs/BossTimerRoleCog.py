import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BossTimerRoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_role_id(self, guild_id):
        try:
            query = "SELECT role_id FROM guild_settings WHERE guild_id = $1"
            record = await self.bot.db.pool.fetchrow(query, str(guild_id))
            if record and record['role_id']:
                return int(record['role_id'])
            else:
                return None
        except Exception as e:
            logger.error(f"Error : {e}")
            return None

    @app_commands.command(name="subscribe", description="Subscribe to boss timer")
    async def subscribe(self, interaction: discord.Interaction):
        # Get the role ID for the server from the database
        role_id = await self.get_role_id(interaction.guild.id)
        if not role_id:
            await interaction.response.send_message("The role is not configured. Check database and settings.", ephemeral=True)
            return

        # Get the role from the guild
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("Role does not exist.", ephemeral=True)
            return

        # Add the role to the user if they don't already have it
        if role in interaction.user.roles:
            await interaction.response.send_message("You are already subscribed to the Boss Timer.", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role, reason="Subscribed to Boss Timer role")
                await interaction.response.send_message("You have been subscribed to the Boss Timer.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("I do not have permission to manage roles. Please check my permissions and try again.", ephemeral=True)
            except discord.HTTPException:
                await interaction.response.send_message("An error occurred while assigning the role. Please try again later.", ephemeral=True)

    @app_commands.command(name="unsubscribe", description="Unsubscribe from the Boss Timer role")
    async def unsubscribe(self, interaction: discord.Interaction):
        # Get the role ID for the server from the database
        role_id = await self.get_role_id(interaction.guild.id)
        if not role_id:
            await interaction.response.send_message("The Boss Timer role is not configured on this server.", ephemeral=True)
            return

        # Get the role from the guild
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("Role not found. Please contact an administrator.", ephemeral=True)
            return

        # Remove the role from the user if they have it
        if role in interaction.user.roles:
            try:
                await interaction.user.remove_roles(role, reason="Unsubscribed from Boss Timer role")
                await interaction.response.send_message("You have been unsubscribed from the Boss Timer.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("I do not have permission to manage roles. Please check my permissions and try again.", ephemeral=True)
            except discord.HTTPException:
                await interaction.response.send_message("An error occurred while removing the role. Please try again later.", ephemeral=True)
        else:
            await interaction.response.send_message("You are not subscribed to the Boss Timer.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BossTimerRoleCog(bot))