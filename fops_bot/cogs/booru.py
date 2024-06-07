# FOPS
# 2024, Fops Bot
# MIT License


import os
import imp
import discord
import logging
import requests


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands

ui = imp.load_source("upload_image", "fops_bot/scripts/danbooru-scripts.py")
cp = imp.load_source("create_post", "fops_bot/scripts/danbooru-scripts.py")


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
        tags = self.tags.value
        rating = self.rating.value
        await self.attachment.save(f"./downloads/{self.attachment.filename}")

        # Get secrets
        api_key = os.environ.get("BOORU_KEY", "")
        api_user = os.environ.get("BOORU_USER", "")
        api_url = "https://booru.kitsunehosting.net"

        await self.message.add_reaction("⬇")
        await interaction.response.send_message(
            f"Got it! Please wait... tagging and sorting {self.attachment.filename}",
            ephemeral=True,
        )

        # Upload everything
        upload_id = ui.upload_image(
            api_key,
            api_user,
            api_url,
            f"./downloads/{self.attachment.filename}",
        )
        if upload_id:
            post_id = cp.create_post(
                api_key,
                api_user,
                api_url,
                upload_id,  # Passed from prev command
                tags,
                rating,
            )

            await self.message.add_reaction("⬆")
            await interaction.followup.send(
                f"Success!\nImage has been uploaded as {api_url}/posts/{post_id}",
                ephemeral=True,
            )


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
        await bot.tree.sync()

    async def grab_message_context(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        # Check if the message contains attachments
        if not message.attachments:
            await interaction.response.send_message(
                "The selected message does not contain any attachments.", ephemeral=True
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
            await interaction.response.send_message(
                "The attachment is not an image.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Grab(bot))

    # for cmd in bot.tree.get_commands():
    #     print(f"Command available: {cmd.name}")
