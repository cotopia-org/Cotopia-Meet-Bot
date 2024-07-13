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


async def del_temps(channel):
    print("del_temp_chan been called!")
    print("the channel is:  " + str(channel))
    await asyncio.sleep(180)  # 3 minutes
    global temp_channels
    if len(channel.members) == 0:
        try:
            print("trying to delete channel:    ")
            print(channel)
            await channel.delete()
            temp_channels.remove(channel.id)
            print("channel was removed")
        except Exception as e:
            print("Sorry couldn't delete the temp channel!")
            print(e)
        try:
            global temp_messages
            # msg = temp_messages[channel]
            msg = await temp_messages[channel.id].channel.fetch_message(
                temp_messages[channel.id].id
            )
            print("trying to edit text:   ")
            print(msg)
            msg_content = msg.content
            # getting the status part
            status_part = msg_content.split("--------------------")[1]
            # getting the author mention
            author_mention = msg_content.split(">,\n")[1]
            author_mention = author_mention.split(" wants to talk with you.")[0]
            # calculating the duration of the meeting
            msg_created_at = msg.created_at.timestamp()
            duration = (
                int(time.time()) - msg_created_at - 180
            )  # minus 180 seconds, time of waiting before deleting voice channel
            duration = int(round((duration / 60), 0))
            #
            # await msg.delete()
            # editing the message
            new_content = (
                author_mention
                + "'s meeting ended!\n"
                + "Duration: "
                + str(duration)
                + " minutes"
                + "\n--------------------"
                + status_part
                + "--------------------"
            )
            await msg.edit(content=new_content, view=None)
            del temp_messages[channel.id]
            print("message was edited")
        except Exception as e:
            print("Sorry couldn't edit the /talk_with message!")
            print(e)


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
        
        # calling the  del_temps(channel) func
        task_del_chan = None
        global temp_channels
        if before.channel.id in temp_channels:
            if len(before.channel.members) == 0:
                task_del_chan = asyncio.create_task(
                    del_temps(before.channel),
                    name=f"deleting temp channel {before.channel.id}",
                )
                await task_del_chan
        
        # When user joins a /talk_with channel
        global temp_messages
        if after.channel.id in temp_messages:
            await utils.edit_tw_text(member=member, temp_messages=temp_messages, after_channel=after.channel)

    
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
        await ctx.defer()
        
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
            category=await utils.get_category(ctx.guild),
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
        try:
            await utils.play_ring(member=member)
            if member3 is not None and member3.voice.channel != member.voice.channel:
                await utils.play_ring(member=member3)
            if member4 is not None and member4.voice.channel != member.voice.channel:
                await utils.play_ring(member=member4)
        except Exception as e:
            print("something went wrong while playying rings!")
            print(e)

        # Handling No Response
        task_edit_msg = asyncio.create_task(
            utils.write_no_response(ctx=ctx, msg_id=the_message.id),
            name=f"editing talk_with msg with no response {the_message.id} at {ctx.guild.id}",
        )
        await task_edit_msg

        print("talk_with is DONE!")

    bot.run(settings.DISCORD_API_SECRET, root_logger=True)


if __name__ == "__main__":
    run()
