# FOPS
# 2024, Fops Bot
# MIT License


import os
import discord
import logging
import requests


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands


# This is pretty cool, basically a popup UI
class TagModal(discord.ui.Modal, title="Enter Tags"):
    tags = discord.ui.TextInput(
        label="Tags",
        placeholder="Enter tags separated by spaces",
    )

    def __init__(self, attachment, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachment = attachment

    async def on_submit(self, interaction: discord.Interaction):
        tags = self.tags.value
        await self.attachment.save(f"./downloads/{self.attachment.filename}")
        await interaction.response.send_message(
            f"Image `{self.attachment.filename}` has been downloaded with tags: {tags}",
            ephemeral=True,
        )
        # Add your uploading logic here, using the tags


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
            modal = TagModal(attachment)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message(
                "The attachment is not an image.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Grab(bot))

    # for cmd in bot.tree.get_commands():
    #     print(f"Command available: {cmd.name}")
