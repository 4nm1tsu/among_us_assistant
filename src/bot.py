import os

import discord
from discord.ext import commands

import cogs.assistant as assistant

bot:commands.Bot = commands.Bot(command_prefix="/")

client = discord.Client()


@bot.event
async def on_ready():
    print("bot is ready.")
    assistant.setup(bot)


bot.run(os.environ["BOT_TOKEN"])
# TODO 例外処理をdiscord.pyのビルトインで
# TODO unknown command
# TODO command not found
# TODO 自分をtargetにしたとき
