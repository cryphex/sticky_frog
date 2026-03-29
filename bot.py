import discord
from discord import app_commands
import sqlite3
import os
import asyncio
import time
from dotenv import load_dotenv

import webserver #required for render

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DB_PATH = os.path.join(os.path.dirname(__file__), "sticky.db")

message_cooldown = 3 #forced cooldown in secs

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

sticky_cache: dict[int, dict] = {}
channel_locks: dict[int, asyncio.Lock] = {}


def get_channel_lock(channel_id: int) -> asyncio.Lock:
    if channel_id not in channel_locks:
        channel_locks[channel_id] = asyncio.Lock()
    return channel_locks[channel_id]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sticky_messages (
            channel_id INTEGER PRIMARY KEY,
            server_id INTEGER NOT NULL,
            message_content TEXT NOT NULL,
            last_message_id INTEGER
        )
    """)
    conn.commit()
    conn.close()


def load_cache():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_id, server_id, message_content, last_message_id FROM sticky_messages")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        channel_id, server_id, message_content, last_message_id = row
        sticky_cache[channel_id] = {
            "server_id": server_id,
            "message_content": message_content,
            "last_message_id": last_message_id,
            "last_post_time": 0,
        }


def db_set_sticky(channel_id: int, server_id: int, message_content: str, last_message_id: int | None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO sticky_messages (channel_id, server_id, message_content, last_message_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(channel_id) DO UPDATE SET
            server_id = excluded.server_id,
            message_content = excluded.message_content,
            last_message_id = excluded.last_message_id
    """, (channel_id, server_id, message_content, last_message_id))
    conn.commit()
    conn.close()


def db_remove_sticky(channel_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sticky_messages WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()


@tree.command(name="stick", description="Stick a message to this channel")
async def stick(interaction: discord.Interaction, message: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("Permissions missing!", ephemeral=True)
        return

    channel_id = interaction.channel_id
    await interaction.response.defer(ephemeral=True)

    async with get_channel_lock(channel_id):
        if channel_id in sticky_cache and sticky_cache[channel_id].get("last_message_id"):
            try:
                old_msg = await interaction.channel.fetch_message(sticky_cache[channel_id]["last_message_id"])
                await old_msg.delete()
            except:
                pass

        sent = await interaction.channel.send(f"📌 **__Sticky:__** \n\n {message}")
        sticky_cache[channel_id] = {
            "server_id": interaction.guild_id,
            "message_content": message,
            "last_message_id": sent.id,
            "last_post_time": time.time()
        }
        db_set_sticky(channel_id, interaction.guild_id, message, sent.id)

    await interaction.followup.send("Sticky message set!", ephemeral=True)


@tree.command(name="stickstop", description="Stop stickying")
async def stickstop(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_messages: return

    channel_id = interaction.channel_id
    if channel_id not in sticky_cache:
        await interaction.response.send_message("No sticky here.", ephemeral=True)
        return

    async with get_channel_lock(channel_id):
        last_id = sticky_cache[channel_id].get("last_message_id")
        if last_id:
            try:
                msg = await interaction.channel.fetch_message(last_id)
                await msg.delete()
            except:
                pass
        del sticky_cache[channel_id]
        db_remove_sticky(channel_id)

    await interaction.response.send_message("Sticky removed.", ephemeral=True)


@client.event
async def on_ready():
    init_db()
    load_cache()
    await tree.sync()
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot or message.channel.id not in sticky_cache:
        return

    channel_id = message.channel.id
    current_time = time.time()
    entry = sticky_cache[channel_id]

    if current_time - entry["last_post_time"] < message_cooldown:
        return

    async with get_channel_lock(channel_id):
        if current_time - entry["last_post_time"] < message_cooldown:
            return

        if entry["last_message_id"]:
            try:
                old_msg = await message.channel.fetch_message(entry["last_message_id"])
                await old_msg.delete()
            except:
                pass

        new_msg = await message.channel.send(f"📌 **__Sticky:__** \n\n {entry['message_content']}")

        entry["last_message_id"] = new_msg.id
        entry["last_post_time"] = current_time
        db_set_sticky(channel_id, entry["server_id"], entry["message_content"], new_msg.id)


webserver.keep_alive() #keep alive
client.run(TOKEN)
