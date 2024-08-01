# FOPS
# 2024, Fops Bot
# MIT License

import os
import discord
import logging
import aiohttp
from datetime import datetime
from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands, tasks
from utilities.database import retrieve_key, store_key
import imp

booru_scripts = imp.load_source("booru_scripts", "fops_bot/scripts/danbooru-scripts.py")


class BackgroundBooru(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Configure options and secrets
        self.api_key = os.environ.get("BOORU_KEY", "")
        self.api_user = os.environ.get("BOORU_USER", "")
        self.api_url = os.environ.get("BOORU_URL", "")

        # Start tasks
        self.update_status.start()

    def check_reply(self, message):
        if message.reference is None:
            logging.debug("Message is not a reference")
            return False
        referenced_message = message.reference.resolved
        if referenced_message is None:
            logging.debug("Referenced message is None")
            return False
        if referenced_message.author.id != self.bot.user.id:
            logging.debug("Referenced message is not the bot user")
            return False
        # Check if the message starts with a valid post ID (assuming it's a number)
        try:
            post_id = int(referenced_message.content.split()[0])
            return True
        except ValueError:
            logging.warning(
                f"Couldn't translate the first portion of message into an ID, issue was {int(referenced_message.content.split()[0])}"
            )
            return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.check_reply(message):
            logging.info("Checked reply")
            referenced_message = message.reference.resolved
            # Extract the post ID from the first line of the original message
            post_id_line = referenced_message.content.splitlines()[0]
            try:
                post_id = int(
                    post_id_line.split()[-1]
                )  # Assuming the post ID is the last part of the first line
            except ValueError:
                return  # Invalid post ID format

            # Extract tags from the user's reply
            tags = message.content.split()
            applied_tags = await self.append_tags(post_id, tags)

            # Thanks!
            await message.add_reaction("🙏")

            # No tagme? yayy
            if "tagme" not in booru_scripts.get_post_tags(
                post_id,
                self.api_url,
                self.api_key,
                self.api_user,
            ):
                await message.add_reaction("✨")

    async def append_tags(self, post_id, tags):
        real_tags = []

        for tag in tags:
            if booru_scripts.tag_exists(
                tag,
                self.api_url,
                self.api_key,
                self.api_user,
            ):
                real_tags.append(tag)

        booru_scripts.append_post_tags(
            post_id,
            real_tags,
            self.api_url,
            self.api_key,
            self.api_user,
        )

        logging.info(f"Added {real_tags} to {post_id}")

        # If the number of tags is over 20 we can clear the `tagme`
        if (
            len(
                booru_scripts.get_post_tags(
                    post_id,
                    self.api_url,
                    self.api_key,
                    self.api_user,
                )
            )
            > 20
        ):
            logging.info("Clearing tagme")
            booru_scripts.append_post_tags(
                post_id,
                real_tags,
                self.api_url,
                self.api_key,
                self.api_user,
                ["tagme"],
            )

        return real_tags

    @tasks.loop(minutes=30)
    async def update_status(self):
        channel = self.bot.get_channel(
            int(os.environ.get("BOORU_MAINTENANCE", "00000000000"))
        )

        if not channel:
            logging.warn(f"Could not get channel {channel}")  # Skip to next run

        r_post = booru_scripts.fetch_images_with_tag(
            "tagme",
            self.api_url,
            self.api_key,
            self.api_user,
            limit=1,
            random=True,
        )[0]

        await channel.send(
            f"{r_post['id']}\n\n{os.environ.get('BOORU_URL', '')}/posts/{r_post['id']}"
        )

        logging.info("waiting 30 minutes to post next tagme...")


async def setup(bot):
    await bot.add_cog(BackgroundBooru(bot))
