import asyncio
import datetime
import re
from asyncio import sleep
from os import getenv

import discord
import psycopg2
import requests
from dotenv import load_dotenv


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

    return overwrites


def write_event_to_db(
    driver: str, epoch: int, kind: str, doer: str, isPair: bool, note: str
):
    load_dotenv()
    conn = psycopg2.connect(
        host=getenv("DB_HOST"),
        dbname=getenv("DB_NAME"),
        user=getenv("DB_USER"),
        password=getenv("DB_PASSWORD"),
        port=getenv("DB_PORT"),
    )
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO discord_event (driver, epoch, kind, doer, isPair, note) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;",
        (driver, epoch, kind, doer, isPair, note),
    )
    id_of_added_row = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return id_of_added_row


def create_header_text(author, member2, member3, member4):
    text = (
        "Hey " + member2.mention + ",\n" + author.mention + " wants to talk with you."
    )
    if member3 is not None:
        split = text.split(",\n", 1)
        text = split[0] + ", " + member3.mention + ",\n" + split[1]

    if member4 is not None:
        split = text.split(",\n", 1)
        text = split[0] + ", " + member4.mention + ",\n" + split[1]

    return text


def create_status_table(author, member2, member3, member4, author_moved):
    the_table = "--------------------"
    if author_moved:
        the_table = (
            the_table
            + "\n"
            + author.mention
            + ":   :green_circle: joined `"
            + datetime.datetime.now().strftime("%H:%M:%S")
            + "`"
        )
    else:
        the_table = (
            the_table + "\n" + author.mention + ":   :hourglass_flowing_sand: pending"
        )
    the_table = (
        the_table + "\n" + member2.mention + ":   :hourglass_flowing_sand: pending"
    )
    if member3 is not None:
        the_table = (
            the_table + "\n" + member3.mention + ":   :hourglass_flowing_sand: pending"
        )
    if member4 is not None:
        the_table = (
            the_table + "\n" + member4.mention + ":   :hourglass_flowing_sand: pending"
        )
    the_table = the_table + "\n--------------------"

    return the_table


def gen_text(author, member2, member3, member4, description, jump_url, author_moved):
    text = jump_url + "\n\n" + create_header_text(author, member2, member3, member4)
    if description is not None:
        text = text + "\n\n**Description:**\n" + description
    text = (
        text
        + "\n\n"
        + create_status_table(author, member2, member3, member4, author_moved)
    )
    return text


async def play_ring(member, voice="assets/sounds/ring3.mp3"):
    if member.voice is not None:
        if not member.voice.self_deaf:
            voice_channel = member.voice.channel
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(voice))
            while vc.is_playing():
                await sleep(0.5)
            await vc.disconnect()
    return "Ok"


def find_unresponsives(text: str):
    the_table = text.split("--------------------")
    the_table = the_table[1]
    lines = the_table.split("\n")
    unresponsives = []
    for each in lines:
        if ":interrobang: no response" in each:
            sub1 = "<@"
            sub2 = ">:"
            s = str(re.escape(sub1))
            e = str(re.escape(sub2))
            res = re.findall(s + "(.*)" + e, each)[0]
            unresponsives.append(int(res))

    return unresponsives


async def handle_no_response(ctx, msg_id: int):
    await asyncio.sleep(180)  # 3 minutes
    talk_with_msg = await ctx.channel.fetch_message(msg_id)
    c1 = talk_with_msg.content
    c2 = c1.replace(
        ":   :hourglass_flowing_sand: pending", ":   :interrobang: no response"
    )
    await talk_with_msg.edit(content=c2)

    # finding and kicking unresponsives
    unresponsives = find_unresponsives(c2)
    for each in unresponsives:
        try:
            member = ctx.guild.get_member(each)
            await member.move_to(
                None, reason="You have been unresponsives to a /talk_with!"
            )
        except Exception as e:
            print("problem kicking the user out of voice!")
            print(e)


async def edit_tw_text(member, temp_messages, after_channel):
    talk_with_msg = await temp_messages[after_channel.id].channel.fetch_message(
        temp_messages[after_channel.id].id
    )
    talk_with_text = talk_with_msg.content
    if member.mention + ":   :hourglass_flowing_sand: pending" in talk_with_text:
        c2 = talk_with_text.replace(
            member.mention + ":   :hourglass_flowing_sand: pending",
            member.mention
            + ":   :green_circle: joined `"
            + datetime.datetime.now().strftime("%H:%M:%S")
            + "`",
            1,
        )
    elif member.mention + ":   :red_circle: declined `" in talk_with_text:
        c2 = talk_with_text.replace(
            member.mention + ":   :red_circle: declined",
            member.mention + ":   :green_circle: joined",
            1,
        )
        # now we need to update the timestamp
        split = c2.split(member.mention + ":   :green_circle: joined `", 1)
        d0 = split[0]
        d1 = member.mention + ":   :green_circle: joined `"
        d2 = datetime.datetime.now().strftime("%H:%M:%S") + "`"
        d3 = split[1].split("`", 1)[1]
        c2 = d0 + d1 + d2 + d3
    elif member.mention + ":   :orange_circle: will join in 5 mins `" in talk_with_text:
        c2 = talk_with_text.replace(
            member.mention + ":   :orange_circle: will join in 5 mins",
            member.mention + ":   :green_circle: joined",
            1,
        )
        # now we need to update the timestamp
        split = c2.split(member.mention + ":   :green_circle: joined `", 1)
        d0 = split[0]
        d1 = member.mention + ":   :green_circle: joined `"
        d2 = datetime.datetime.now().strftime("%H:%M:%S") + "`"
        d3 = split[1].split("`", 1)[1]
        c2 = d0 + d1 + d2 + d3
    elif (
        member.mention + ":   :orange_circle: will join in 15 mins `" in talk_with_text
    ):
        c2 = talk_with_text.replace(
            member.mention + ":   :orange_circle: will join in 15 mins",
            member.mention + ":   :green_circle: joined",
            1,
        )
        # now we need to update the timestamp
        split = c2.split(member.mention + ":   :green_circle: joined `", 1)
        d0 = split[0]
        d1 = member.mention + ":   :green_circle: joined `"
        d2 = datetime.datetime.now().strftime("%H:%M:%S") + "`"
        d3 = split[1].split("`", 1)[1]
        c2 = d0 + d1 + d2 + d3
    else:
        c2 = "farghi nakarde ke baba"

    if c2 != "farghi nakarde ke baba":
        await talk_with_msg.edit(content=c2)


def check_schedule(guild_id: int, member2, member3, member4):
    result = ""
    REQUEST_URL = "http://tooljet.cotopia.social:8084/availability"
    params = {
        "id_server": guild_id,
        "id_discord": member2.id,
    }
    if member2.voice is None:
        r = requests.get(url=REQUEST_URL, params=params)
        if r.status_code == 200:
            status = r.json()["available_status"]
            if "online until " in status:
                result = ":warning: " + (
                    member2.mention
                    + f" is not in the voice channels right now, but is scheduled to be `{status}`\n"
                )
                result = result.replace("T", "  ")
            elif "will be available in " in status:
                result = ":warning: " + (
                    member2.mention
                    + f" is not in the voice channels right now, but is scheduled to be `{status}`\n"
                )
                result = result.replace("will be ", "")
                result = result.replace("T", "  ")
            elif "not set" in status:
                result = ":warning: " + (
                    member2.mention
                    + " is not in the voice channels right now, and has no scheduled time!\n"
                )
    if member3 is not None:
        if member3.voice is None:
            params["id_discord"] = member3.id
            r = requests.get(url=REQUEST_URL, params=params)
            if r.status_code == 200:
                status = r.json()["available_status"]
                if "online until " in status:
                    result = (
                        result
                        + ":warning: "
                        + (
                            member3.mention
                            + f" is not in the voice channels right now, but is scheduled to be `{status}`\n"
                        )
                    )
                    result = result.replace("T", "  ")
                elif "will be available in " in status:
                    result = (
                        result
                        + ":warning: "
                        + (
                            member3.mention
                            + f" is not in the voice channels right now, but is scheduled to be `{status}`\n"
                        )
                    )
                    result = result.replace("will be ", "")
                    result = result.replace("T", "  ")
                elif "not set" in status:
                    result = (
                        result
                        + ":warning: "
                        + (
                            member3.mention
                            + " is not in the voice channels right now, and has no scheduled time!\n"
                        )
                    )
    if member4 is not None:
        if member4.voice is None:
            params["id_discord"] = member4.id
            r = requests.get(url=REQUEST_URL, params=params)
            if r.status_code == 200:
                status = r.json()["available_status"]
                if "online until " in status:
                    result = (
                        result
                        + ":warning: "
                        + (
                            member4.mention
                            + f" is not in the voice channels right now, but is scheduled to be `{status}`\n"
                        )
                    )
                    result = result.replace("T", "  ")
                elif "will be available in " in status:
                    result = (
                        result
                        + ":warning: "
                        + (
                            member4.mention
                            + f" is not in the voice channels right now, but is scheduled to be `{status}`\n"
                        )
                    )
                    result = result.replace("will be ", "")
                    result = result.replace("T", "  ")
                elif "not set" in status:
                    result = (
                        result
                        + ":warning: "
                        + (
                            member4.mention
                            + " is not in the voice channels right now, and has no scheduled time!\n"
                        )
                    )

    return result
