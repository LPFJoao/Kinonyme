import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from collections import Counter
import string

class WeeklyGuildBoss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bosses = [
            "Morokai",
            "Excavator-9",
            "Chernobog",
            "Talus",
            "Malakar",
            "Cornelius",
            "Ahzreil",
            "Minezerok",
            "Kowazan",
            "Adentus",
            "Junobote",
            "Grand Aelon",
            "Nirma",
            "Aridus"
            "Queen Bellanir",
            "Tevent"
        ]
        self.votes = Counter()
        self.emoji_list = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟",
            "🆔", "🆒", "🆕", "🆓", "🆗"
        ]

    @app_commands.command(name="post_weekly_bosses", description="Post a message for users to vote for weekly guild bosses.")
    async def post_weekly_bosses(self, interaction: discord.Interaction):
        """
        Post a message for users to vote for weekly guild bosses.
        """
        description = "React with the emoji corresponding to the boss you want to vote for. You can vote for multiple bosses."
        boss_list = "\n".join([f"{self.emoji_list[i]} {boss}" for i, boss in enumerate(self.bosses)])
        embed = discord.Embed(title="Weekly Guild Boss Voting", description=f"{description}\n\n{boss_list}")
        await interaction.response.send_message(embed=embed)
        vote_message = await interaction.original_response()

        # Add reactions for each boss using the emojis
        for i in range(len(self.bosses)):
            await vote_message.add_reaction(self.emoji_list[i])

    @app_commands.command(name="results_weekly_bosses", description="Get the results of the weekly guild boss voting.")
    async def results_weekly_bosses(self, interaction: discord.Interaction, message_id: str):
        """
        Display the results of the weekly guild boss voting.
        """
        try:
            channel = interaction.channel
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            await interaction.response.send_message("Message not found.", ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.response.send_message("Failed to retrieve the message.", ephemeral=True)
            return

        # Get reactions from the vote message
        self.votes.clear()
        for reaction in message.reactions:
            if reaction.emoji in self.emoji_list:
                index = self.emoji_list.index(reaction.emoji)
                if 0 <= index < len(self.bosses):
                    self.votes[self.bosses[index]] += reaction.count - 1  # Subtract bot's own reaction

        # Prepare and send the results in an embed
        total_votes = sum(self.votes.values())
        result_lines = []
        for boss, votes in self.votes.items():
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            bar_length = int(percentage / 5)  # Create a bar out of 20 blocks
            bar = "{}{}".format("\u2588" * bar_length, "\u2591" * (20 - bar_length))  # Using Unicode escape codes for █ and ░
            result_lines.append(f"{boss}\n{bar} {percentage:.2f}% ({votes} votes)")

        result_message = "\n\n".join(result_lines)
        embed = discord.Embed(title="Weekly Boss Voting Results", description=result_message)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(WeeklyGuildBoss(bot))