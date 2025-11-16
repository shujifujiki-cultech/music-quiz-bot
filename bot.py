#メインファイル
#Discordボットのエントリーポイント


import discord
from discord import app_commands
import os

# 設定をインポート
from config import MY_GUILD_ID

# 各クイズをインポート
from quizzes import music_history

# Discord設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

MY_GUILD = discord.Object(id=MY_GUILD_ID)


@client.event
async def on_ready():
    """ボット起動時の処理"""
    tree.copy_global_to(guild=MY_GUILD)
    await tree.sync(guild=MY_GUILD)
    print(f'{client.user} としてログインしました!')
    print('コマンドを同期しました!')


# 各クイズのコマンドを登録
music_history.register_commands(tree)


# ボットを起動
client.run(os.getenv('DISCORD_TOKEN'))