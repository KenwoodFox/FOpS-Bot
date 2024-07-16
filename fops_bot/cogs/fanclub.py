# 2023, Fops Bot
# MIT License


import discord
import logging
import asyncio
import pytz
import os
import python_weather


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands, tasks

from datetime import datetime, timedelta, time, timezone

from utilities.common import seconds_until


class FanclubCog(commands.Cog, name="FanclubCog"):
    def __init__(self, bot):
        self.bot = bot

        # timezone
        self.localtz = pytz.timezone("US/Eastern")

        datapath = "/app/data/data.yaml"

        self.tempList = {}

    def getStat(self, guild: int, addOne=False):
        """
        Tell me how many times a guild has been booped
        """

        if guild not in self.tempList.keys():
            self.tempList[guild] = 1

        if addOne:
            self.tempList[guild] += 1

        return self.tempList[guild]

    @commands.Cog.listener("on_message")
    async def boopListener(self, message: discord.Message):
        logging.debug(f"Boop Listener processing {message}")

        # Check for boops!
        boops = ["boop", "boops", "boop'd"]
        if (any(item in message.content.lower() for item in boops)) and (
            not message.author.bot
        ):
            logging.debug(f"Boop detected in {message}, guild was {message.guild}")
            await message.reply(f"{self.getStat(message.guild, True)} boops!")

    @commands.Cog.listener("on_message")
    async def holeInTheWallListener(self, msg: discord.Message):
        logging.debug(f"Hole In the wall got {msg}")

        chan = int(os.environ.get("HOLE_CHAN", ""))
        user = int(os.environ.get("HOLE_USER", ""))

        # Dont respond to ourself.
        if msg.author.bot:
            return

        if isinstance(msg.channel, discord.channel.DMChannel):
            "What to do if dm'd directly!"
            logging.info(f"Got a dm! {msg.content}")

            if msg.author.id == user:
                holeChan = self.bot.get_channel(chan)
                await holeChan.send(msg.content)
                await msg.add_reaction("📬")
            else:
                await msg.add_reaction("❌")
        elif msg.channel.id == chan:  # in the right channel
            # Extract the content
            ct = msg.content

            if ct[0] == "(":
                # Checks if the message is OOC, and if it is, skips it
                # await msg.add_reaction("🔇")
                pass
            else:
                # Time to actually forward a message!
                recipient = await self.bot.fetch_user(user)
                if recipient == None:
                    await msg.add_reaction("❌")
                    return
                else:
                    await recipient.send(f"*Somebody..*\n{ct}")
                    await msg.add_reaction("📬")


async def setup(bot):
    await bot.add_cog(FanclubCog(bot))
