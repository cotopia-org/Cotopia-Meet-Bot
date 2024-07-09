import discord
import settings
from discord.ext import commands
import utils

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
    async def talk_with(
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

        # create voice channel
        channel = await ctx.guild.create_voice_channel(
            name=ctx.author.name + "'s meeting",
            category=utils.get_category(ctx.guild),
            overwrites=utils.create_channel_overwrites(guild=ctx.guild, members=members),
        )

        # move author to channel
        try:
            await ctx.author.move_to(channel)
            author_moved = True
        except:  # noqa: E722
            print("user is not connected to voice.")
            author_moved = False

        # view = TalkWithView()
        # view.author_id = ctx.author.id
        # view.voice_channel = channel

        # global temp_channels
        # temp_channels.append(channel)
        # print("temp_channels:   ")
        # print(temp_channels)

        # view.members = members

        # members_str = []
        # the_table = "\n\n--------------------"
        # for m in members:
        #     members_str.append(str(m))
        #     the_table = (
        #         the_table + "\n" + m.mention + ":   :hourglass_flowing_sand: pending"
        #     )
        # view.members_str = members_str

        # if description is not None:
        #     text = text + "\n\nDescription:\n" + description

        # the_message = await ctx.send(text + "\n\n" + channel.jump_url, view=view)

        # # play ring alarm when user sent the command

        # await play_ring_voice(discord, bot, ctx, member)
        # if member3 is not None and member3.voice.channel != member.voice.channel:
        #     # send bot to their channels and play ring voice
        #     await play_ring_voice(discord, bot, ctx, member3)

        # if member4 is not None and member4.voice.channel != member.voice.channel:
        #     # send bot to their channels and play ring voice
        #     await play_ring_voice(discord, bot, ctx, member4)

        # global temp_messages
        # temp_messages[channel] = the_message
        # print("temp_messages:   ")
        # print(temp_messages)

        # event_note = {}
        # event_note["members"] = members_str
        # event_note["channel"] = {"name": channel.name, "id": channel.id}
        # note = json.dumps(event_note)
        # log_processor.write_event_to_db(
        #     driver=ctx.guild.id,
        #     epoch=rightnow(),
        #     kind="ASK FOR TALK",
        #     doer=str(ctx.author.id),
        #     isPair=False,
        #     note=note,
        # )

        # # Now lets edit the message with what habibi wants
        # await the_message.edit(
        #     content=the_message.content + the_table + "\n--------------------"
        # )

        # if author_moved:
        #     talk_with_msg = await ctx.channel.fetch_message(the_message.id)
        #     c1 = talk_with_msg.content
        #     c2 = c1.replace(
        #         ctx.author.mention + ":   :hourglass_flowing_sand: pending",
        #         ctx.author.mention
        #         + ":   :green_circle: joined `"
        #         + datetime.datetime.now().strftime("%H:%M:%S")
        #         + "`",
        #         1,
        #     )
        #     await talk_with_msg.edit(content=c2)

        # # Handling No Response
        # async def write_no_response(msg_id: int):
        #     await asyncio.sleep(180)  # 3 minutes
        #     talk_with_msg = await ctx.channel.fetch_message(msg_id)
        #     c1 = talk_with_msg.content
        #     c2 = c1.replace(
        #         ":   :hourglass_flowing_sand: pending", ":   :interrobang: no response"
        #     )
        #     await talk_with_msg.edit(content=c2)

        # task_edit_msg = asyncio.create_task(
        #     write_no_response(the_message.id),
        #     name=f"editing talk_with msg with no response {the_message.id} at {ctx.guild.id}",
        # )
        # await task_edit_msg


    bot.run(settings.DISCORD_API_SECRET, root_logger=True)


if __name__ == "__main__":
    run()
