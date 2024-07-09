import discord
import settings
from discord.ext import commands

logger = settings.logging.getLogger("bot")


def run():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.presences = True
    intents.members = True
    intents.reactions = True

    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"User: {bot.user} (ID: {bot.user.id})")
        for cmd_file in settings.CMDS_DIR.glob("*.py"):
            if cmd_file.name != "__init__.py":
                await bot.load_extension(f"commands.{cmd_file.name[:-3]}")

        await bot.tree.sync()

    @bot.event
    async def on_guild_join(guild):
        print(f"joined guild {guild.id}")

    @bot.event
    async def on_message(message):
        
        # Ignoring Bots
        if message.author == bot.user:
            return

    @bot.event
    async def on_voice_state_update(member, before, after):

        # Ignoring Bots
        if member.bot:
            return

    @bot.hybrid_command(description="Replies with pong!")
    async def ping(ctx):
        print("this is ping. the server is:")
        print(ctx.guild.id)
        await ctx.send("Your Discord ID is " + str(ctx.author.id), ephemeral=True)

    bot.run(settings.DISCORD_API_SECRET, root_logger=True)


if __name__ == "__main__":
    run()
