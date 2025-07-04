from discord import app_commands
from discord.ext import commands
from collections import defaultdict
import discord

item_reactions = defaultdict(list)

class Drops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post_drops", description="Post the weekly guild boss drops.")
    @app_commands.describe(
        item1="Item 1",
        item2="Item 2",
        item3="Item 3",
        item4="Item 4",
        item5="Item 5",
        item6="Item 6",
        item7="Item 7"
    )
    async def post_drops(self, interaction: discord.Interaction, item1: str, item2: str, item3: str, item4: str, item5: str, item6: str, item7: str):
        items = [item1, item2, item3, item4, item5, item6, item7]
        emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣'] 

        embed = discord.Embed(
            title="Weekly Guild Boss Drops",
            description="React to the items you need!",
            color=discord.Color.blue()
        )

        # Add items to a single field with extra spacing
        item_list = "\n\n".join([f"{emoji} **{item}**" for emoji, item in zip(emoji_numbers, items)])
        embed.add_field(name="Items", value=item_list, inline=False)

        # Send the embed message
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # Adding reactions (use emoji numbers 1-7)
        for emoji in emoji_numbers:
            await message.add_reaction(emoji)

        # Storing message ID and reactions for reference
        item_reactions[message.id] = items

    @app_commands.command(name="get_votes", description="Get the votes for each item.")
    @app_commands.describe(message_id="The ID of the message to get votes from")
    async def get_votes(self, interaction: discord.Interaction, message_id: str):
        await interaction.response.defer()  # Acknowledge interaction to prevent timeout

        try:
            message_id = int(message_id)
            message = await interaction.channel.fetch_message(message_id)
        except ValueError:
            await interaction.followup.send("Please enter a valid message ID (a numeric ID).", ephemeral=True)
            return
        except discord.NotFound:
            await interaction.followup.send("Message not found. Please make sure the ID is correct.", ephemeral=True)
            return

        if message.id not in item_reactions:
            await interaction.followup.send("This message ID has no associated reactions recorded.", ephemeral=True)
            return

        items = item_reactions[message.id]
        results = defaultdict(list)
        emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣']

        for reaction in message.reactions:
            if reaction.emoji in emoji_numbers:
                item_index = emoji_numbers.index(reaction.emoji)
                if item_index >= len(items):
                    continue

                users = [user async for user in reaction.users()]
                for user in users:
                    if user != self.bot.user:
                        member = interaction.guild.get_member(user.id)
                        results[items[item_index]].append(member.display_name if member else user.name)

        results_text = "\n".join([f"**{item}**: {', '.join(users) if users else 'No votes'}" for item, users in results.items()])
        await interaction.followup.send(f"Reaction results:\n{results_text if results_text else 'No votes yet!'}")

async def setup(bot):
    await bot.add_cog(Drops(bot))
