from discord.ext import commands
from discord import app_commands, Interaction, TextChannel

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_welcome_channel", description="Set the channel for welcome messages")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_channel(self, interaction: Interaction, channel: TextChannel):
        await self.bot.db.set_config(interaction.guild.id, welcome_channel=channel.id)
        await interaction.response.send_message(
            f"✅ Welcome channel set to {channel.mention} for this server!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Config(bot))

