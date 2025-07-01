from discord.ext import commands
from discord import app_commands, Interaction, CategoryChannel

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_onboarding_category", description="Set the category for onboarding channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_onboarding_category(self, interaction: Interaction, category: CategoryChannel):
        await self.bot.db.set_config(interaction.guild.id, onboarding_category=category.id)
        await interaction.response.send_message(
            f"✅ Onboarding category set to {category.name}!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Config(bot))
