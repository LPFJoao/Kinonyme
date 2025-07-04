import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import logging

# List of valid weapons
VALID_WEAPONS = [
    "Staff", "Dagger", "SwordAndShield", "Greatsword", "Long Bow", "Crossbow", "WandAndTome",
]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PagedGuildMembersView(discord.ui.View):
    def __init__(self, members, items_per_page=10):
        super().__init__()
        self.members = members
        self.items_per_page = items_per_page
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.previous_button.disabled = self.current_page <= 0
        self.next_button.disabled = self.current_page >= (len(self.members) - 1) // self.items_per_page

    def get_page_content(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_members = self.members[start:end]

        embed = discord.Embed(
            title="📋 Guild Members",
            color=discord.Color.purple()
        )
        embed.description = f"Page {self.current_page + 1} of {(len(self.members) - 1) // self.items_per_page + 1}"

        class_emojis = {
            "Healer": "💖💚",
            "DPS": "⚔️🏹",
            "Tank": "🛡️🚛"
        }

        for member in page_members:
            emoji = class_emojis.get(member['class'], "❔")
            name = member['ingame_name']
            gear_score = member['gear_score']
            classe = member['class']
            main_hand = member['main_hand']
            offhand = member['offhand']
            game_capture = member["game_capture"]
            value = (
                f"**Gear Score:** {gear_score}\n"
                f"**Class:** {emoji} {classe}\n"
                f"**Main:** {main_hand} | **Offhand:** {offhand}"
            )
            embed.add_field(name=f"{emoji} {name}", value=value, inline=False)
            embed.add_field(name="Game Capture", value=member['game_capture'])

        embed.set_footer(text=f"Use the buttons to navigate pages.")
        return embed, None

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed, _ = self.get_page_content()
            await interaction.response.edit_message(content=None, embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < (len(self.members) - 1) // self.items_per_page:
            self.current_page += 1
            self.update_buttons()
            embed, _ = self.get_page_content()
            await interaction.response.edit_message(content=None, embed=embed, view=self)

class GuildMemberGear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def add_member_db(self, discord_id, guild_id, ingame_name, gear_score, guild_class, main_hand, offhand, avatar_url, game_capture):
        try:
            query = """
                INSERT INTO guild_members (discord_id, guild_id, ingame_name, gear_score, class, main_hand, offhand, avatar, game_capture)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (discord_id, guild_id)
                DO UPDATE SET ingame_name = $3, gear_score = $4, class = $5, main_hand = $6, offhand = $7, avatar = $8, game_capture = $9
            """
            await self.bot.db.pool.execute(query, str(discord_id), guild_id, ingame_name, gear_score, guild_class, main_hand, offhand, avatar_url, game_capture)
            return True
        except Exception as e:
            logger.error(f"Database error (add_member_db): {e}")
            return False

    async def get_guildmembers_db(self, guild_id):
        try:
            query = "SELECT * FROM guild_members WHERE guild_id = $1 ORDER BY gear_score DESC"
            records = await self.bot.db.pool.fetch(query, guild_id)
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Database error (get_guildmembers_db): {e}")
            return []

    async def find_member_db(self, ingame_name, guild_id):
        try:
            query = "SELECT * FROM guild_members WHERE ingame_name = $1 AND guild_id = $2"
            record = await self.bot.db.pool.fetchrow(query, ingame_name, guild_id)
            return record is not None
        except Exception as e:
            logger.error(f"Database error (find_member_db): {e}")
            return False

    async def remove_member_db(self, ingame_name, guild_id):
        try:
            query = "DELETE FROM guild_members WHERE ingame_name = $1 AND guild_id = $2"
            await self.bot.db.pool.execute(query, ingame_name, guild_id)
            return True
        except Exception as e:
            logger.error(f"Database error (remove_member_db): {e}")
            return False

    @app_commands.command(name="add_member", description="Add or update your guild member gear information.")
    @app_commands.describe(
        ingame_name="Your in-game name",
        gear_score="Your current gear score",
        guild_class="Choose your class",
        main_hand="Main weapon",
        offhand="Offhand weapon",
        game_capture="(Optional) Upload a game capture image"
    )
    @app_commands.choices(
        guild_class=[
            app_commands.Choice(name="Healer", value="Healer"),
            app_commands.Choice(name="DPS", value="DPS"),
            app_commands.Choice(name="Tank", value="Tank"),
        ],
        main_hand=[app_commands.Choice(name=w, value=w) for w in VALID_WEAPONS],
        offhand=[app_commands.Choice(name=w, value=w) for w in VALID_WEAPONS],
    )
    async def add_member(
        self,
        interaction: discord.Interaction,
        ingame_name: str,
        gear_score: int,
        guild_class: str,
        main_hand: str,
        offhand: str,
        game_capture: discord.Attachment = None
    ):
        guild_id = str(interaction.guild.id)
        avatar_url = interaction.user.display_avatar.url
        success = await self.add_member_db(
            interaction.user.id,
            guild_id,
            ingame_name,
            gear_score,
            guild_class,
            main_hand,
            offhand,
            avatar_url,
            game_capture.url if game_capture else None
        )
        if success:
            await interaction.response.send_message("Your guild member information has been successfully added/updated.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred while accessing the database. Please try again later.", ephemeral=True)

    @app_commands.command(name="guildmembers", description="Show a paginated list of guild members sorted by gear score, or search by Discord ID.")
    @app_commands.describe(discord_id="(Optional) The Discord ID of the member to search for.")
    async def guildmembers(self, interaction: discord.Interaction, discord_id: str = None):
        guild_id = str(interaction.guild.id)
        if discord_id:
            try:
                query = "SELECT * FROM guild_members WHERE discord_id = $1 AND guild_id = $2"
                record = await self.bot.db.pool.fetchrow(query, discord_id, guild_id)
                if not record:
                    await interaction.response.send_message("No member found with this Discord ID.", ephemeral=True)
                    return
                member = dict(record)
                embed = discord.Embed(
                    title=f"Member info {member['ingame_name']}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Gear Score", value=member['gear_score'])
                embed.add_field(name="Class", value=member['class'])
                embed.add_field(name="Main", value=member['main_hand'])
                embed.add_field(name="Offhand", value=member['offhand'])
                embed.add_field(name="Game Capture", value=member['game_capture'])
                if member.get('avatar'):
                    embed.set_thumbnail(url=member['avatar'])
                await interaction.response.send_message(embed=embed)
            except Exception as e:
                await interaction.response.send_message("Error while searching for the member.", ephemeral=True)
            return
        # Otherwise, classic paginated behavior
        members = await self.get_guildmembers_db(guild_id)
        if not members:
            await interaction.response.send_message("No members found in the database.", ephemeral=True)
            return
        view = PagedGuildMembersView(members)
        embed, _ = view.get_page_content()
        await interaction.response.send_message(content=None, embed=embed, view=view)

    @app_commands.command(name="remove_member", description="Remove a guild member (server owner only).")
    @app_commands.describe(ingame_name="The in-game name of the member to remove.")
    async def remove_member(self, interaction: discord.Interaction, ingame_name: str):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                "You do not have permission to use this command. Only the server owner can remove members.",
                ephemeral=True
            )
            return
        guild_id = str(interaction.guild.id)
        found = await self.find_member_db(ingame_name, guild_id)
        if not found:
            await interaction.response.send_message(
                f"No member found with the in-game name '{ingame_name}' in this guild.",
                ephemeral=True
            )
            return
        success = await self.remove_member_db(ingame_name, guild_id)
        if success:
            await interaction.response.send_message(f"The member '{ingame_name}' was successfully removed.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred while accessing the database. Please try again later.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GuildMemberGear(bot))
