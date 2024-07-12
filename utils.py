import datetime
from os import getenv

import discord
import psycopg2
from dotenv import load_dotenv
from asyncio import sleep



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




async def play_ring(member, voice='assets/sounds/ring3.mp3'):
    if member.voice is not None:
        if not member.voice.self_deaf:
            voice_channel = member.voice.channel
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(voice))
            while vc.is_playing():
                await sleep(0.5)
            await vc.disconnect()

    return 'Ok'
