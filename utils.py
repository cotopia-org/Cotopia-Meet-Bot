import discord


async def get_category(guild):
    category = discord.utils.get(guild.categories, name="MEETINGS")
    if category is None:
        category = await guild.create_category("MEETINGS")
    return category


def create_channel_overwrites(guild, members: list):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=False),
    }
    for each in members:
        overwrites[each] = discord.PermissionOverwrite(connect=True, view_channel=True)
