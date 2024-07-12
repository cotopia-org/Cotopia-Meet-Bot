import asyncio
import json
import time

import discord
from discord.ext import commands

import settings
import utils
from view import TalkWithView

logger = settings.logging.getLogger("bot")

temp_channels = []
temp_messages = {}


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
        # for cmd_file in settings.CMDS_DIR.glob("*.py"):
        #     if cmd_file.name != "__init__.py":
        #         await bot.load_extension(f"commands.{cmd_file.name[:-3]}")

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

    @bot.hybrid_command()
    async def test(
        ctx,
        member: discord.Member,
        description: str | None = None,
        member3: discord.Member | None = None,
        member4: discord.Member | None = None,
    ):
        # create members list
        members = []
        members.append(ctx.author)
        members.append(member)
        if member3 is not None:
            members.append(member3)
        if member4 is not None:
            members.append(member4)
        members_str = []
        for m in members:
            members_str.append(str(m))

        # create voice channel
        channel = await ctx.guild.create_voice_channel(
            name=ctx.author.name + "'s meeting",
            category=utils.get_category(ctx.guild),
            overwrites=utils.create_channel_overwrites(
                guild=ctx.guild, members=members
            ),
        )

        # write event to db
        event_note = {}
        event_note["members"] = members_str
        event_note["channel"] = {"name": channel.name, "id": channel.id}
        note = json.dumps(event_note)
        utils.write_event_to_db(
            driver=ctx.guild.id,
            epoch=int(time.time()),
            kind="ASK FOR TALK",
            doer=str(ctx.author.id),
            isPair=False,
            note=note,
        )

        # move author to channel
        try:
            await ctx.author.move_to(channel)
            author_moved = True
        except:  # noqa: E722
            print("user is not connected to voice.")
            author_moved = False

        global temp_channels
        temp_channels.append(channel.id)
        print("temp_channels:   ")
        print(temp_channels)

        # create view
        view = TalkWithView()
        view.author_id = ctx.author.id
        view.voice_channel = channel
        view.members = members
        view.members_str = members_str

        # send message
        the_message = await ctx.send(
            utils.gen_text(
                author=ctx.author,
                member2=member,
                member3=member3,
                member4=member4,
                description=description,
                jump_url=channel.jump_url,
                author_moved=author_moved,
            ),
            view=view,
        )

        global temp_messages
        temp_messages[channel.id] = the_message
        print("temp_messages:   ")
        print(temp_messages)

        # play ring alarm
        await utils.play_ring(member=member)
        if member3 is not None and member3.voice.channel != member.voice.channel:
            await utils.play_ring(member=member3)
        if member4 is not None and member4.voice.channel != member.voice.channel:
            await utils.play_ring(member=member4)

        # Handling No Response
        task_edit_msg = asyncio.create_task(
            utils.write_no_response(ctx=ctx, msg_id=the_message.id),
            name=f"editing talk_with msg with no response {the_message.id} at {ctx.guild.id}",
        )
        await task_edit_msg

        print("DONE!")

    bot.run(settings.DISCORD_API_SECRET, root_logger=True)


if __name__ == "__main__":
    run()
