import discord
from discord import app_commands
from discord.ext import commands
import os
from collections import Counter
import asyncio
import logging

# Set up logging
#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger(__name__)7
#Deleted for production

class GuildStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def GetGuildMembers(self, guild_id):
        try:
            query = "SELECT * FROM guild_members WHERE guild_id = $1"
            records = await self.bot.db.pool.fetch(query, guild_id)
            # Return the records as a list of dictionaries
            return [dict(record) for record in records]
        except Exception as e:
            return []

    @app_commands.command(name="guild_stats", description="Display the statistics of the guild members.")
    async def GuildStats(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        members = await self.GetGuildMembers(guild_id)

        if not members:
            await interaction.response.send_message("No guild members found.", ephemeral=True)
            return

        # Calculate the statistics
        total_gear_score = sum(member['gear_score'] for member in members)
        average_gear_score = round(total_gear_score / len(members))
        class_counts = Counter(member['class'] for member in members)
        weapon_combos = Counter(
            tuple(sorted((member['main_hand'], member['offhand']))) for member in members
        )
        sorted_weapon_combos = sorted(weapon_combos.items())

        # Create the embed
        embed = discord.Embed(title=f"Guild statistics for {interaction.guild.name}", color=discord.Color.blue())
        embed.add_field(name="💡 Average gear score", value=f"{average_gear_score}", inline=False)
        embed.add_field(
            name=" 🏫 Class distribution",
            value=f"💖💚 Healers: {class_counts['Healer']}\n⚔️🏹 DPS: {class_counts['DPS']}\n🛡️🚛 Tanks: {class_counts['Tank']}",
            inline=False
        )
        weapon_combos_text = "\n".join([f"🏹 {main} & {offhand} : {count}" for (main, offhand), count in sorted_weapon_combos])
        embed.add_field(name="🗠 Weapon combinations", value=weapon_combos_text if weapon_combos_text else "None", inline=False)

        # Show the avatar of the member with the highest gear score (if exists)
        if members and 'avatar' in members[0] and members[0]['avatar']:
            embed.set_thumbnail(url=members[0]['avatar'])

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GuildStats(bot))
