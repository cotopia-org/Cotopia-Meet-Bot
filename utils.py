from os import getenv

import discord
import psycopg2
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
