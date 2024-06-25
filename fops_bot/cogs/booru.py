# FOPS
# 2024, Fops Bot
# MIT License

import os
import imp
import discord
import logging
import requests
import aiohttp

from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands


booru_scripts = imp.load_source("booru_scripts", "fops_bot/scripts/danbooru-scripts.py")


# This is pretty cool, basically a popup UI
class TagModal(discord.ui.Modal, title="Enter Tags"):
    tags = discord.ui.TextInput(
        label="Tags",
        placeholder="Enter tags separated by spaces",
    )

    rating = discord.ui.TextInput(
        label="Rating",
        placeholder="Rating s, q or e",
    )

    def __init__(self, attachment, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachment = attachment
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        tags = self.tags.value
        rating = self.rating.value

        await self.attachment.save(f"./downloads/{self.attachment.filename}")

        # Get secrets
        api_key = os.environ.get("BOORU_KEY", "")
        api_user = os.environ.get("BOORU_USER", "")
        api_url = "https://booru.kitsunehosting.net"

        await self.message.add_reaction("⬇")

        # Upload everything
        upload_id = booru_scripts.upload_image(
            api_key,
            api_user,
            api_url,
            f"./downloads/{self.attachment.filename}",
        )
        if upload_id:
            post_id = booru_scripts.create_post(
                api_key,
                api_user,
                api_url,
                upload_id,  # Passed from prev command
                tags,
                rating,
            )

            # if post_id != None:
            #     await self.message.add_reaction("⬆")

            #     for num in number_to_words(post_id):
            #         await self.message.add_reaction(num)

            #     await interaction.followup.send(
            #         f"Success!\nImage has been uploaded as {api_url}/posts/{post_id}",
            #         ephemeral=True,
            #     )
            # else:  # Image must have already been posted
            #     await self.message.add_reaction("white_check_mark")
            #     await interaction.followup.send(
            #         f"Looks like this image has already been tracked!",
            #         ephemeral=True,
            #     )


class Grab(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.ctx_menu = app_commands.ContextMenu(
            name="Upload to BixiBooru",
            callback=self.grab_message_context,  # set the callback of the context menu to "grab_message_context"
        )
        self.bot.tree.add_command(self.ctx_menu)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()

    async def grab_message_context(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        # Check if the message contains attachments
        if not message.attachments:
            await interaction.response.send_message(
                "The message you selected dosn't contain directly embedded images! (but i will support linked images in the future.)",
                ephemeral=True,
            )
            return

        # Download the first attachment
        attachment = message.attachments[0]

        # Check if the attachment is an image
        if attachment.content_type.startswith("image/"):
            # Ensure the downloads directory exists
            os.makedirs("./downloads", exist_ok=True)
            # Show modal to collect tags
            modal = TagModal(attachment, message)
            await message.add_reaction("🤔")
            await interaction.response.send_modal(modal)
        else:
            await interaction.followup.send(
                "The attachment is not an image.", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message has exactly one attachment and is an image
        if len(message.attachments) == 0:
            logging.info("No attachments")
            return

        if len(message.attachments) > 1:
            logging.info("Too many attachments")
            await message.add_reaction("🤹‍♂️")
            return

        if not message.attachments[0].content_type.startswith("image/"):
            logging.warn("Attachment is not an image?")
            await message.add_reaction("❌")
            return

        # Get secrets
        api_key = os.environ.get("BOORU_KEY", "")
        api_user = os.environ.get("BOORU_USER", "")
        api_url = "https://booru.kitsunehosting.net"

        # Get attachment
        attachment = message.attachments[0]
        file_path = f"/tmp/{attachment.filename}"

        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await resp.read())

        # Call the get_post_id function
        post_id = booru_scripts.check_image_exists(
            file_path, api_url, api_key, api_user
        )

        # Check if a valid number was returned
        if post_id is not None and isinstance(post_id, int):
            post_id_str = str(post_id)

            # Check for duplicate digits
            if self.has_duplicates(post_id_str):
                logging.warn(f"Duplicated digits for post {post_id_str}")
                await message.add_reaction("🔢")
            else:
                for digit in post_id_str:
                    # React with the corresponding emoji
                    await message.add_reaction(self.get_emoji(digit))
        else:
            await message.add_reaction("💎")

        # Clean up the download
        os.remove(file_path)

    def get_emoji(self, digit):
        # Map digit to corresponding emoji
        emoji_map = {
            "0": "0️⃣",
            "1": "1️⃣",
            "2": "2️⃣",
            "3": "3️⃣",
            "4": "4️⃣",
            "5": "5️⃣",
            "6": "6️⃣",
            "7": "7️⃣",
            "8": "8️⃣",
            "9": "9️⃣",
        }
        return emoji_map[digit]

    def has_duplicates(self, s):
        # Check for duplicate characters in the string
        return len(s) != len(set(s))


async def setup(bot):
    await bot.add_cog(Grab(bot))

    # for cmd in bot.tree.get_commands():
    #     print(f"Command available: {cmd.name}")
