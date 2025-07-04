from discord.ext import commands
from discord import Member, PermissionOverwrite

class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        # Get onboarding category from config
        config = await self.bot.db.get_config(member.guild.id)
        category_id = config["onboarding_category"] if config and "onboarding_category" in config else None
        if not category_id:
            return  # No category set, do nothing

        category = member.guild.get_channel(category_id)
        if not category:
            return  # Category was deleted

        # Set permissions: only new member and staff (admins) can see the channel
        overwrites = {
            member.guild.default_role: PermissionOverwrite(view_channel=False),
            member: PermissionOverwrite(view_channel=True, send_messages=True),
        }
        # Allow all roles with admin permissions
        for role in member.guild.roles:
            if role.permissions.administrator:
                overwrites[role] = PermissionOverwrite(view_channel=True, send_messages=True)

        # Create the private onboarding channel
        channel = await category.create_text_channel(
            name=f"welcome-{member.display_name}".lower(),
            overwrites=overwrites,
            topic=f"Private onboarding channel for {member.mention}"
        )

        await channel.send(
            f"Welcome {member.mention}! A staff member will help you get started. Please introduce yourself."
        )

async def setup(bot):
    await bot.add_cog(Onboarding(bot))

