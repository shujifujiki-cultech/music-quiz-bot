# メインファイル
# Discordボットのエントリーポイント
# (v11: setup_hook 全体を try...except で囲み、エラーを特定する)

import discord
from discord import app_commands
import os
from dotenv import load_dotenv 
from flask import Flask
from threading import Thread
import asyncio 

# 🔽 --- 修正 (v11): トレースバック（詳細なエラー）を
# 🔽 ログに出力するためにインポート --- 🔽
import traceback
# 🔼 --- 修正 (v11) --- 🔼

from utils import sheets_loader  
from utils.quiz_view import QuizView, QuizData 

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

intents = discord.Intents.default()

# (Flask Webサーバーのコード ... )
app = Flask('')
@app.route('/')
def health_check():
    print("[Web Server] Health check OK.")
    return "Bot is alive!"
def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
# ( ... Webサーバーここまで)


class MyClient(discord.Client):
    
    def _create_quiz_callback(self, sheet_name: str, bot_title: str, allowed_channel_id: str):
        async def _actual_callback(interaction: discord.Interaction):
            await self.run_quiz_command(
                interaction=interaction,
                sheet_name=sheet_name,
                bot_title=bot_title,
                allowed_channel_id=allowed_channel_id
            )
        return _actual_callback

    # 🔽 --- 修正 (v11): setup_hook 全体を try...except で囲む --- 🔽
    async def setup_hook(self):
        print("[Bot] setup_hook: (v11) 処理を開始します...")
        
        try:
            # 1. 最初に、現在のコマンド登録をすべてクリアする (v10のロジック)
            if MY_GUILD:
                print(f"[Bot] setup_hook: ギルド {GUILD_ID} の古いコマンドをクリアします...")
                self.tree.clear_commands(guild=MY_GUILD)
                await self.tree.sync(guild=MY_GUILD)
            else:
                print("[Bot] setup_hook: 古いグローバルコマンドをクリアします...")
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
            print("[Bot] setup_hook: コマンドのクリアが完了しました。")

            # 2. 'bot_master_list' を別スレッドで読み込む (v10のロジック)
            print("[Bot] setup_hook: 'bot_master_list' の読み込みを別スレッドで開始...")
            bot_list = await asyncio.to_thread(
                sheets_loader.get_bot_master_list
            )
            print("[Bot] setup_hook: 'bot_master_list' の読み込み完了。")

            if not bot_list:
                print("[Bot] ERROR: bot_master_list が読み込めません。処理を中断します。")
                return

            print(f"[Bot] {len(bot_list)} 件のボット設定を読み込みました。")

            # 3. スプレッドシートに基づいて新しいコマンドを登録する (v10のロジック)
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
                            sheet_name, 
                            bot_title, 
                            allowed_channel_id
                        )
                        
                        self.tree.add_command(
                            app_commands.Command(
                                name=command_name,
                                description=f"{bot_title} を開始します。",
                                callback=final_callback 
                            )
                        )
                        
                        # print(f"[Bot] 登録 [クイズ]: /{command_name} ({bot_title})") # (ログが多すぎるので一旦コメントアウト)
                        successful_registrations += 1

                    except Exception as e:
                        print(f"[Bot] ERROR: クイズの登録に失敗: {bot_config} | Error: {e}")

                elif bot_type == '診断':
                    pass # (スキップ)
            
            print(f"[Bot] setup_hook: {successful_registrations} 件のクイズを .tree に登録しました。")

            # 4. 新しいコマンドリストで再度同期する
            if MY_GUILD:
                await self.tree.sync(guild=MY_GUILD)
            else:
                await self.tree.sync() 
                
            print("[Bot] setup_hook: (v11) ★★★ コマンドの同期が完了しました ★★★")

        except Exception as e:
            # 💥 もし setup_hook 全体が失敗したら、ここにエラーログが出る
            print("=================================================================")
            print(" FATAL ERROR: [Bot] setup_hook が致命的なエラーでクラッシュしました")
            print("=================================================================")
            # トレースバック（詳細なエラー内容）をログに出力
            traceback.print_exc()
            print("=================================================================")
    # 🔼 --- 修正 (v11) ここまで --- 🔼


    async def run_quiz_command(self, interaction: discord.Interaction, sheet_name: str, bot_title: str, allowed_channel_id: str):
        # (v8 のコードのまま - 修正なし)
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


client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

# Webサーバーを別スレッドで起動
web_thread = Thread(target=run_web_server)
web_thread.start()

# ボット本体を起動
client.run(TOKEN)