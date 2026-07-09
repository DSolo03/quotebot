import os
import random
import tempfile
import uuid
from asyncio import to_thread
from pathlib import Path

import emoji
import quote
import sqlite_utils
from sqlite_utils.db import Table
import yaml
from typing import cast
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types import Message, User
from quote import Quote
from text import character_filter

CONFIG_PATH = "config.yaml"

auth = dict()
config = dict()

with open(CONFIG_PATH, "r", encoding = "UTF-8") as file:
    config_file = yaml.safe_load(file)
    auth = config_file["auth"]
    config = config_file["config"]

cache_path = Path(config["cache_path"])

app = Client(
    auth["handler"],
    api_id = auth["api_id"],
    api_hash = auth["api_hash"],
    bot_token = auth["bot_token"]
)

db = sqlite_utils.Database("quotes.db")
DB = cast(Table, db.table("quotes"))

skin = quote.Skin(config["skin_path"])

async def userpic(user):
    match user:
        case int() | str():
            path = cache_path / f"{user}.png"
            if path.exists():
                return path
        case User():
            if user.photo:
                fresh_user = cast(User, await app.get_users(user.id))
                path = cache_path / f"{fresh_user.id}.png"
                await app.download_media(message = fresh_user.photo.big_file_id, file_name = str(path), block = True) # type: ignore
                return path
    return None

def load_pregenerated(path: Path):
    quotes = []
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding = "UTF-8") as file:
        quotes = yaml.safe_load(file)["quotes"]
    return quotes

pregenerated_quotes = load_pregenerated(config["pregenerated_path"])

@app.on_message(filters.command(["quote"]))
async def quoteHandler(_, message:Message):
    quote = Quote()
    if not (message.chat and message.from_user):
        return
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.chat:
        filename = os.path.join(tempfile.gettempdir(), '{}.png'.format(uuid.uuid4().hex))
        if message.reply_to_message.forward_from:
            message.reply_to_message.from_user = message.reply_to_message.forward_from

        text = message.reply_to_message.text or message.reply_to_message.caption or ""
        text = text.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")
        text = emoji.demojize(text)
        text = character_filter(skin.font_obj, text)
        quote.text = text

        if message.reply_to_message.forward_sender_name:
            quote.username = character_filter(skin.font_obj, message.reply_to_message.forward_sender_name)
            user_id = 0
        else:
            quote.username = message.reply_to_message.from_user.first_name or "User"
            quote.username = character_filter(skin.font_obj, quote.username) or message.reply_to_message.from_user.username or "User"
            quote.userpic = await userpic(message.reply_to_message.from_user)
            user_id = message.reply_to_message.from_user.id

        result = await to_thread(skin.render_quote, quote)

        DB.upsert({
            "chatID":message.reply_to_message.chat.id, 
            "messageID":message.reply_to_message.id, 
            "userID":user_id, 
            "userName": quote.username, 
            "text": quote.text
        }, pk = ("chatID", "messageID")) # type: ignore

        result.save(filename)
        await app.send_photo(chat_id = cast(int, message.chat.id), reply_to_message_id = message.reply_to_message.id, photo = filename)

    else:
        variants = list(DB.rows_where("chatID = ?", [message.chat.id]))
        if variants:
            choice = random.choice(variants)
            filename = os.path.join(tempfile.gettempdir(), '{}.png'.format(uuid.uuid4().hex))

            text = choice.get("text") or ""
            text = text.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")
            text = emoji.demojize(text)
            quote.text = text

            quote.username = choice.get("userName") or "User"
            quote.userpic = await userpic(choice.get("userID"))

            result = await to_thread(skin.render_quote, quote)

            result.save(filename)
            await app.send_photo(chat_id = cast(int, message.chat.id), reply_to_message_id = message.id, photo = filename)

@app.on_message(filters.command(["cache"]))
async def cacheLoader(_, message: Message):
    unique_users = [
        row["userID"] 
        for row in db.query("SELECT DISTINCT userID FROM quotes WHERE userID IS NOT NULL")
    ]
    counter = 0
    for user_id in unique_users:
        if user_id:
            counter += 1
            fresh_user = cast(User, await app.get_users(user_id))
            await userpic(fresh_user)
    await message.reply(f"Updated userpic cache for {counter} users!")

@app.on_message(filters.command(["wise"]))
async def wiseHandler(_, message: Message):
    quote = Quote()
    if message.from_user and message.chat:
        filename = os.path.join(tempfile.gettempdir(), '{}.png'.format(uuid.uuid4().hex))
        
        text = f"..{random.choice(pregenerated_quotes)}"
        text = text.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")
        text = emoji.demojize(text)
        quote.text = text

        result = await to_thread(skin.render_quote, quote, hide_userpic = True)

        result.save(filename)
        await app.send_photo(chat_id = cast(int, message.chat.id), reply_to_message_id = message.id, photo = filename)

app.run()
