# メインファイル
# Discordボットのエントリーポイント
# (v4: 予測候補の削除 ＆ チャンネル名表示に対応)

import discord
from discord import app_commands
import os
from dotenv import load_dotenv 
from flask import Flask
from threading import Thread

# 🔽 --- 修正 (v8): asyncio をインポート --- 🔽
import asyncio
# 🔼 --- 修正 (v8) --- 🔼

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

# 🔽 --- 修正 (v6): Renderのヘルスチェック用Webサーバー --- 🔽
app = Flask('')

@app.route('/')
def health_check():
    # Render や UptimeRobot がアクセスするためのエンドポイント
    print("[Web Server] Health check OK.")
    return "Bot is alive!"

def run_web_server():
    # Render は 0.0.0.0 で 10000 (または 8080) をリッスンする
    # 環境変数 PORT があればそれを使い、なければ 10000 を使う
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
# 🔼 --- 修正 (v6) --- 🔼


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    # 🔽 --- 修正 (v4): 予測候補を削除するため、ファクトリ関数パターンに変更 --- 🔽
    def _create_quiz_callback(self, sheet_name: str, bot_title: str, allowed_channel_id: str):
        """
        コマンド実行時に呼ばれる「実際のコールバック関数」を
        動的に生成するためのファクトリ（工場）関数。
        """
        
        # この関数が Discord に 'callback' として登録される
        async def _actual_callback(interaction: discord.Interaction):
            # この関数は引数を持たないが、
            # 外側の関数の変数 (sheet_nameなど) を記憶している (クロージャー)
            await self.run_quiz_command(
                interaction=interaction,
                sheet_name=sheet_name,
                bot_title=bot_title,
                allowed_channel_id=allowed_channel_id
            )
        
        # 作成したコールバック関数そのものを返す
        return _actual_callback
    
    # 🔽 --- 修正 (v9): setup_hook 内のブロッキングを修正 --- 🔽
    async def setup_hook(self):
        print("[Bot] setup_hook: スプレッドシートからボットの登録を開始します...")
        
        # 'bot_master_list' の読み込みを別スレッドで実行
        print("[Bot] setup_hook: 'bot_master_list' の読み込みを別スレッドで開始...")
        bot_list = await asyncio.to_thread(
            sheets_loader.get_bot_master_list
        )
        print("[Bot] setup_hook: 'bot_master_list' の読み込み完了。")

        if not bot_list:
            print("[Bot] ERROR: bot_master_list が読み込めません。処理を中断します。")
            return

        print(f"[Bot] {len(bot_list)} 件のボット設定を読み込みました。")

        for bot_config in bot_list:
            if str(bot_config.get('is_active')).upper() != 'TRUE':
                print(f"[Bot] スキップ: {bot_config.get('bot_title')} (is_active=FALSE)")
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
                    
                    print(f"[Bot] 登録 [クイズ]: /{command_name} ({bot_title})")

                except Exception as e:
                    print(f"[Bot] ERROR: クイズの登録に失敗: {bot_config} | Error: {e}")

            elif bot_type == '診断':
                print(f"[Bot] スキップ (未実装): {bot_config.get('bot_title')} (診断)")
                pass
        
        if MY_GUILD:
            await self.tree.sync(guild=MY_GUILD)
        else:
            await self.tree.sync() 
            
        print("[Bot] setup_hook: コマンドの同期が完了しました。")
    # 🔼 --- 修正 (v9) ここまで --- 🔼    
  

"""
    async def setup_hook(self):
        print("[Bot] setup_hook: スプレッドシートからボットの登録を開始します...")
        
        bot_list = sheets_loader.get_bot_master_list()
        
        if not bot_list:
            print("[Bot] ERROR: bot_master_list が読み込めません。処理を中断します。")
            return

        print(f"[Bot] {len(bot_list)} 件のボット設定を読み込みました。")

        for bot_config in bot_list:
            if str(bot_config.get('is_active')).upper() != 'TRUE':
                print(f"[Bot] スキップ: {bot_config.get('bot_title')} (is_active=FALSE)")
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
                    
                    # 🔽 --- 修正 (v4): ファクトリ関数を呼び出す --- 🔽
                    final_callback = self._create_quiz_callback(
                        sheet_name, 
                        bot_title, 
                        allowed_channel_id
                    )
                    # 🔼 --- 修正 (v4) --- 🔼
                    
                    self.tree.add_command(
                        app_commands.Command(
                            name=command_name,
                            description=f"{bot_title} を開始します。",
                            callback=final_callback # 引数を持たないコールバックを登録
                        )
                    )
                    
                    print(f"[Bot] 登録 [クイズ]: /{command_name} ({bot_title})")

                except Exception as e:
                    print(f"[Bot] ERROR: クイズの登録に失敗: {bot_config} | Error: {e}")

            elif bot_type == '診断':
                print(f"[Bot] スキップ (未実装): {bot_config.get('bot_title')} (診断)")
                pass
        
        if MY_GUILD:
#            self.tree.copy_global_to(guild=MY_GUILD)
            await self.tree.sync(guild=MY_GUILD)
        else:
            await self.tree.sync() 
            
        print("[Bot] setup_hook: コマンドの同期が完了しました。")"""


    async def run_quiz_command(self, interaction: discord.Interaction, sheet_name: str, bot_title: str, allowed_channel_id: str):
        """
        スプレッドシートからデータを読み込んでクイズを実行する共通関数
        (v8: asyncio.to_thread でブロッキングI/Oを回避)
        """
        try:
            # 1. 最初に「本人にだけ見える」応答を defer する
            await interaction.response.defer(ephemeral=True) 

            # 2. チャンネルIDをチェックする (高速)
            if allowed_channel_id and allowed_channel_id.strip() not in ['N/A', '0', '']:
                allowed_channel_id_str = allowed_channel_id.strip()
                if str(interaction.channel.id) != allowed_channel_id_str:
                    
                    error_message = f"このコマンド（`/ {interaction.command.name}`）は、このチャンネルでは実行できません。\n"
                    try:
                        channel_id_int = int(allowed_channel_id_str)
                        target_channel = self.get_channel(channel_id_int) 
                        if target_channel:
                            error_message += f"（{target_channel.mention} でお試しください）"
                        else:
                            error_message += f"（指定されたチャンネルでお試しください）"
                    except ValueError:
                        error_message += f"（指定されたチャンネルでお試しください）"
                    
                    await interaction.edit_original_response(content=error_message)
                    return
            
            # 3. クイズデータを「別スレッド」で取得する (低速だがフリーズしない)
            print(f"[Bot] {interaction.user.name} のために {sheet_name} の読み込みを別スレッドで開始...")
            
            questions_data = await asyncio.to_thread(
                sheets_loader.get_quiz_data, sheet_name
            )
            
            print(f"[Bot] {sheet_name} の読み込み完了。")

            # 4. 取得したデータをチェック
            if not questions_data:
                await interaction.edit_original_response(content=f"エラー: クイズデータ（{sheet_name}）を読み込めませんでした。")
                return
                
            try:
                quiz_data_list = [QuizData(q) for q in questions_data]
            except Exception as e:
                await interaction.edit_original_response(content=f"エラー: クイズデータの形式が正しくありません。(sheet: {sheet_name}): {e}")
                return

            # 5. 挑戦開始の「公開メッセージ」を送信
            await interaction.channel.send(
                f"**{interaction.user.mention} が「{bot_title}」に挑戦します！** 🎵"
            )

            # 6. 実際のクイズビューを開始
            view = QuizView(quiz_data_list, bot_title)
            await view.start(interaction)
        
        except Exception as e:
            print(f"ERROR: run_quiz_command で予期せぬエラー: {e}")
            if interaction.response.is_done():
                try:
                    await interaction.edit_original_response(content="予期せぬエラーが発生しました。")
                except:
                    pass # 編集に失敗しても無視
            else:
                try:
                    await interaction.response.send_message("予期せぬエラーが発生しました。", ephemeral=True)
                except:
                    pass # 送信に失敗しても無視
    # 🔼 --- 修正 (v8) ここまで --- 🔼

client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

web_thread = Thread(target=run_web_server)
web_thread.start()

client.run(TOKEN)