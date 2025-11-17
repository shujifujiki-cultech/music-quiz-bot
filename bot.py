# メインファイル
# Discordボットのエントリーポイント
# (v16: 最終確定版 - Python 3.10.13)
# (v16: asyncio をメインにし、Flask を to_thread で実行)

import discord
from discord import app_commands
import os
from dotenv import load_dotenv 

# 🔽 --- 修正 (v16): Flask をインポート (Quart ではない) --- 🔽
from flask import Flask
# 🔼 --- 修正 (v16) --- 🔼

import asyncio 
import traceback 

from utils import sheets_loader  
from utils.quiz_view import QuizView, QuizData 

# --- 設定の読み込み ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID') 

if not TOKEN:
    print("ERROR: DISCORD_TOKEN が .env ファイルに設定されていません。")
    exit()

MY_GUILD = discord.Object(id=GUILD_ID) if GUILD_ID else None
if MY_GUILD:
    print(f"ターゲットサーバーID: {GUILD_ID} (テスト用)")
else:
    print("グローバルコマンドとして登録します (反映に時間がかかります)")

# v13 と同様に、Discord Developer Portal で3つのインテントをONにする
intents = discord.Intents.all() 

# --- Render (Web Service) 対応 (v16: Flask版) ---
app = Flask('')
@app.route('/')
def health_check():
    print("[Web Server] Health check OK.")
    return "Bot is alive!"

def run_web_server():
    """ (v16) Flask サーバーを「ブロッキング」で実行する関数 """
    port = int(os.environ.get('PORT', 10000))
    # app.run を直接呼び出す
    app.run(host='0.0.0.0', port=port)
# --- Render対応ここまで ---


# --- メインのボットクラス ---
class MyClient(discord.Client):
    
    # v12 と同様に __init__ を定義
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self) 

    def _create_quiz_callback(self, sheet_name: str, bot_title: str, allowed_channel_id: str):
        # (v12 と同様)
        async def _actual_callback(interaction: discord.Interaction):
            await self.run_quiz_command(
                interaction=interaction,
                sheet_name=sheet_name,
                bot_title=bot_title,
                allowed_channel_id=allowed_channel_id
            )
        return _actual_callback

    # v14 と同様に setup_hook を定義
    async def setup_hook(self):
        """ (v14) 起動時、Discord接続「前」に実行される """
        print("[Bot] setup_hook: (v16) 処理を開始します (コマンドのロード)...")
        try:
            print("[Bot] setup_hook: 'bot_master_list' の読み込みを別スレッドで開始...")
            bot_list = await asyncio.to_thread(
                sheets_loader.get_bot_master_list
            )
            print("[Bot] setup_hook: 'bot_master_list' の読み込み完了。")

            if not bot_list:
                print("[Bot] ERROR: bot_master_list が読み込めません。処理を中断します。")
                return

            print(f"[Bot] {len(bot_list)} 件のボット設定を読み込みました。")

            successful_registrations = 0
            for bot_config in bot_list:
                if str(bot_config.get('is_active')).upper() != 'TRUE':
                    continue
                bot_type = bot_config.get('type')
                if bot_type == 'クイズ':
                    try:
                        command_name = bot_config['command_name']
                        bot_title = bot_config['bot_title']
                        sheet_name = bot_config['sheet_questions']
                        allowed_channel_id = str(bot_config.get('allowed_channel_id', ''))
                        if not all([command_name, bot_title, sheet_name]):
                            print(f"[Bot] ERROR: クイズ設定に不備があります: {bot_config}")
                            continue
                        final_callback = self._create_quiz_callback(
                            sheet_name, bot_title, allowed_channel_id
                        )
                        self.tree.add_command(
                            app_commands.Command(
                                name=command_name,
                                description=f"{bot_title} を開始します。",
                                callback=final_callback 
                            )
                        )
                        successful_registrations += 1
                    except Exception as e:
                        print(f"[Bot] ERROR: クイズの登録に失敗: {bot_config} | Error: {e}")
                elif bot_type == '診断':
                    pass 
            
            print(f"[Bot] setup_hook: {successful_registrations} 件のクイズを .tree に登録しました。")
            print("[Bot] setup_hook: (v16) コマンドのロードが完了しました。")

        except Exception as e:
            print("=================================================================")
            print(" FATAL ERROR: [Bot] setup_hook が致命的なエラーでクラッシュしました")
            print("=================================================================")
            traceback.print_exc()
            print("=================================================================")
    
    async def run_quiz_command(self, interaction: discord.Interaction, sheet_name: str, bot_title: str, allowed_channel_id: str):
        # (v12 と同様)
        try:
            await interaction.response.defer(ephemeral=True) 
            if allowed_channel_id and allowed_channel_id.strip() not in ['N/A', '0', '']:
                allowed_channel_id_str = allowed_channel_id.strip()
                if str(interaction.channel.id) != allowed_channel_id_str:
                    error_message = f"このコマンド（`/ {interaction.command.name}`）は、このチャンネルでは実行できません。\n"
                    try:
                        channel_id_int = int(allowed_channel_id_str)
                        target_channel = self.get_channel(channel_id_int) 
                        if target_channel: error_message += f"（{target_channel.mention} でお試しください）"
                        else: error_message += f"（指定されたチャンネルでお試しください）"
                    except ValueError: error_message += f"（指定されたチャンネルでお試しください）"
                    await interaction.edit_original_response(content=error_message)
                    return
            print(f"[Bot] {interaction.user.name} のために {sheet_name} の読み込みを別スレッドで開始...")
            questions_data = await asyncio.to_thread(
                sheets_loader.get_quiz_data, sheet_name
            )
            print(f"[Bot] {sheet_name} の読み込み完了。")
            if not questions_data:
                await interaction.edit_original_response(content=f"エラー: クイズデータ（{sheet_name}）を読み込めませんでした。")
                return
            try: quiz_data_list = [QuizData(q) for q in questions_data]
            except Exception as e:
                await interaction.edit_original_response(content=f"エラー: クイズデータの形式が正しくありません。(sheet: {sheet_name}): {e}")
                return
            await interaction.channel.send(
                f"**{interaction.user.mention} が「{bot_title}」に挑戦します！** 🎵"
            )
            view = QuizView(quiz_data_list, bot_title)
            await view.start(interaction)
        except Exception as e:
            print(f"ERROR: run_quiz_command で予期せぬエラー: {e}")
            if interaction.response.is_done():
                try: await interaction.edit_original_response(content="予期せぬエラーが発生しました。")
                except: pass
            else:
                try: await interaction.response.send_message("予期せぬエラーが発生しました。", ephemeral=True)
                except: pass

# --- ボットの実行 (v16) ---
client = MyClient(intents=intents)

# v14 と同様に on_ready を定義
@client.event
async def on_ready():
    """ (v14) Discord 接続「後」に実行される """
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    
    print("[Bot] on_ready: (v16) 処理を開始します (コマンドの同期)...")
    try:
        if MY_GUILD:
            print(f"[Bot] on_ready: ギルド {GUILD_ID} のコマンドをクリアします...")
            client.tree.clear_commands(guild=MY_GUILD) 
            await client.tree.sync(guild=MY_GUILD)
        else:
            print("[Bot] on_ready: グローバルコマンドをクリアします...")
            client.tree.clear_commands(guild=None)
            await client.tree.sync()
            
        print("[Bot] on_ready: (v16) ★★★ コマンドの同期が完了しました ★★★")
        
    except Exception as e:
        print("=================================================================")
        print(" FATAL ERROR: [Bot] on_ready がコマンド同期中にクラッシュしました")
        print("=================================================================")
        traceback.print_exc()
        print("=================================================================")

# 🔽 --- 修正 (v16): asyncio メイン関数 (Flask/Thread ではない) --- 🔽
async def main():
    """
    ボット (client.start) と Webサーバー (to_thread(run_web_server)) を
    1つの asyncio イベントループで同時に実行する
    """
    print("[Main] (v16) Webサーバー(Flask) と Discordボット を asyncio で起動します...")
    
    # client.start() を直接 await するのではなく、
    # client.login() + client.connect() を使う (start() はブロッキングのため)
    
    async with client:
        # 1. Webサーバーをバックグラウンドスレッドで起動
        # (Render がポート 10000 をスキャンできるようにする)
        await asyncio.to_thread(run_web_server)
        
        # 2. ボット本体をメインスレッド (asyncio) で起動
        # (client.run() や client.start() ではなく、
        #  async with を使って login() と connect() を呼び出す)
        await client.login(TOKEN)
        await client.connect(reconnect=True)

if __name__ == "__main__":
    # 💥 v16: 実行方法を asyncio.run(main()) に変更
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot is shutting down...")
# 🔼 --- 修正 (v16) ここまで --- 🔼