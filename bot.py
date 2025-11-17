# メインファイル
# Discordボットのエントリーポイント
# (v20: ギルド固有コマンド登録の修正版)

import discord
from discord import app_commands
import os
from dotenv import load_dotenv 

# Flask をインポート
from flask import Flask

import asyncio 
import traceback 
import threading  # 🔽 追加: Flaskを別スレッドで起動するため

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

# Discord Developer Portal で3つのインテントをONにする
intents = discord.Intents.all() 

# --- Render (Web Service) 対応 ---
app = Flask('')
@app.route('/')
def health_check():
    print("[Web Server] Health check OK.")
    return "Bot is alive!"

def run_web_server():
    """ Flask サーバーを実行する関数 """
    port = int(os.environ.get('PORT', 10000))
    print(f"[Web Server] (v20) Flask を起動します (ポート: {port})...")
    app.run(host='0.0.0.0', port=port)
# --- Render対応ここまで ---


# --- メインのボットクラス ---
class MyClient(discord.Client):
    
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self) 

    def _create_quiz_callback(self, sheet_name: str, bot_title: str, allowed_channel_id: str):
        async def _actual_callback(interaction: discord.Interaction):
            await self.run_quiz_command(
                interaction=interaction,
                sheet_name=sheet_name,
                bot_title=bot_title,
                allowed_channel_id=allowed_channel_id
            )
        return _actual_callback

    async def setup_hook(self):
        """ 起動時、Discord接続「前」に実行される """
        print("[Bot] setup_hook: (v20) 処理を開始します (コマンドのロード)...")
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
                        # 🔽 修正 (v20): ギルド固有のコマンドとして登録
                        self.tree.add_command(
                            app_commands.Command(
                                name=command_name,
                                description=f"{bot_title} を開始します。",
                                callback=final_callback 
                            ),
                            guild=MY_GUILD  # ← ギルド固有として登録
                        )
                        successful_registrations += 1
                    except Exception as e:
                        print(f"[Bot] ERROR: クイズの登録に失敗: {bot_config} | Error: {e}")
                elif bot_type == '診断':
                    pass 
            
            print(f"[Bot] setup_hook: {successful_registrations} 件のクイズを .tree に登録しました。")
            print("[Bot] setup_hook: (v20) コマンドのロードが完了しました。")

        except Exception as e:
            print("=================================================================")
            print(" FATAL ERROR: [Bot] setup_hook が致命的なエラーでクラッシュしました")
            print("=================================================================")
            traceback.print_exc()
            print("=================================================================")
    
    async def run_quiz_command(self, interaction: discord.Interaction, sheet_name: str, bot_title: str, allowed_channel_id: str):
        try:
            await interaction.response.defer(ephemeral=True) 
            if allowed_channel_id and allowed_channel_id.strip() not in ['N/A', '0', '']:
                allowed_channel_id_str = allowed_channel_id.strip()
                if str(interaction.channel.id) != allowed_channel_id_str:
                    error_message = f"このコマンド（`/{interaction.command.name}`）は、このチャンネルでは実行できません。\n"
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

# --- ボットの実行 (v18) ---
client = MyClient(intents=intents)

@client.event
async def on_ready():
    """ Discord 接続「後」に実行される """
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    
    print("[Bot] on_ready: (v20) 処理を開始します (コマンドの同期)...")
    try:
        # 🔽 デバッグ: 登録されているコマンド数を確認
        commands_in_tree = client.tree.get_commands(guild=MY_GUILD)
        print(f"[Bot] on_ready: tree に登録されているコマンド数: {len(commands_in_tree)}")
        
        if MY_GUILD:
            print(f"[Bot] on_ready: ギルド {GUILD_ID} にコマンドを同期します...")
            # 🔽 修正: clear_commands() を削除（setup_hook で登録したコマンドを保持）
            synced = await client.tree.sync(guild=MY_GUILD)
            print(f"[Bot] on_ready: {len(synced)} 個のコマンドを同期しました")
        else:
            print("[Bot] on_ready: グローバルコマンドとして同期します...")
            synced = await client.tree.sync()
            print(f"[Bot] on_ready: {len(synced)} 個のコマンドを同期しました")
            
        print("[Bot] on_ready: (v20) ★★★ コマンドの同期が完了しました ★★★")
        
    except Exception as e:
        print("=================================================================")
        print(" FATAL ERROR: [Bot] on_ready がコマンド同期中にクラッシュしました")
        print("=================================================================")
        traceback.print_exc()
        print("=================================================================")

# 🔽 --- 修正 (v18): Threading で Flask を起動し、ボットをメインループで実行 --- 🔽
async def main():
    """
    Flask サーバーを daemon thread で起動し、
    ボットをメイン asyncio ループで実行する
    """
    print("[Main] (v20) Flask を daemon thread で起動し、ボットをメインループで実行します...")
    
    # Flask を別スレッドで起動（daemon=True で、ボット終了時に自動終了）
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("[Main] (v20) Flask サーバーを起動しました。")
    
    # ボットをメインループで実行
    async with client:
        await client.start(TOKEN)
# 🔼 --- 修正 (v18) ここまで --- 🔼

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot is shutting down...")
