# クイズ用の共通Viewクラス
# (v2.9: 音声ファイル直接添付 + Discord内で音声・画像を直接表示 + 公開メッセージ後にephemeralセッション開始対応 + 待機時間2秒 + 復習機能 + タイムアウト処理 + クリック可能なコマンド)

import discord
import random
import asyncio
import aiohttp  # 非同期HTTPリクエスト用
import io  # BytesIO用 

# 🔽 --- スプレッドシートのデータを扱うためのクラス (v2.8: Discord内で音声・画像を直接表示) --- 🔽
# QuizData クラスの __init__ メソッド修正版
# quiz_view.py の QuizData クラス全体をこれに置き換えてください

class QuizData:
    """
    スプレッドシートの1行（1問）のデータを格納するクラス
    bot.py がこのクラスのリストを作成して QuizView に渡します
    (v3.2: 画像のみの選択肢に対応)
    """
    def __init__(self, record: dict):
        # record は {'text': '問題文', 'option_1': '選択肢1', ...} のような辞書
        self.question_id = record.get('question_id', 'N/A')
        self.question_text = record.get('text')  # スプレッドシートのカラム名は 'text'
        
        # 🔽 修正: 選択肢とその画像を同時に収集
        self.options = []
        self.option_images = []
        
        for i in range(1, 10):  # option_9 まで自動で探す
            opt_text = record.get(f'option_{i}')
            opt_image = record.get(f'option_{i}_image')
            
            # テキストまたは画像のいずれかが存在する場合に選択肢として追加
            has_text = opt_text is not None and str(opt_text).strip() != ""
            has_image = opt_image is not None and str(opt_image).strip() != ""
            
            if has_text or has_image:
                # テキストが空の場合はデフォルトのラベルを設定
                if has_text:
                    self.options.append(str(opt_text))
                else:
                    # 画像のみの場合、ラベルマップに対応した文字を使用
                    label_map = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F", 7: "G", 8: "H", 9: "I"}
                    self.options.append(f"選択肢{label_map.get(i, str(i))}")
                
                # 画像URLを追加（なければNone）
                if has_image:
                    self.option_images.append(str(opt_image).strip())
                else:
                    self.option_images.append(None)
            else:
                # テキストも画像もない場合は終了
                break
        
        # 🔽 新規追加: 音声URL
        self.audio_url = record.get('audio_url')
        if self.audio_url and str(self.audio_url).strip() != "":
            self.audio_url = str(self.audio_url).strip()
        else:
            self.audio_url = None
        
        self.correct_answer = str(record.get('correct_answer'))
        self.explanation = record.get('explanation')
        
        # バリデーション（データが揃っているか確認）
        if not all([self.question_text, self.options, self.correct_answer, self.explanation]):
            raise ValueError(f"クイズデータに不足があります (ID: {self.question_id}): {record}")
        
        # 正解番号（correct_answer）が選択肢の範囲内かチェック
        try:
            correct_index = int(self.correct_answer) - 1  # 1始まりを0始まりに
            if not (0 <= correct_index < len(self.options)):
                raise ValueError(f"正解番号 '{self.correct_answer}' が選択肢の範囲外です (ID: {self.question_id})")
        except ValueError:
            raise ValueError(f"正解番号 '{self.correct_answer}' が数字ではありません (ID: {self.question_id})")
    
    @staticmethod
    def _convert_gdrive_url(url: str) -> str:
        """
        GoogleドライブのURLを埋め込み可能な形式に変換
        例: https://drive.google.com/file/d/FILE_ID/view
        → https://drive.google.com/uc?export=view&id=FILE_ID
        """
        if not url or 'drive.google.com' not in url:
            return url
        
        # file/d/FILE_ID/view 形式の場合
        if '/file/d/' in url:
            try:
                file_id = url.split('/file/d/')[1].split('/')[0]
                # ?usp=sharing などのパラメータを削除
                file_id = file_id.split('?')[0]
                return f"https://drive.google.com/uc?export=view&id={file_id}"
            except:
                return url
        
        return url

# 🔽 --- QuizView クラスをスプレッドシート対応に修正 (v2.8: Discord内で音声・画像を直接表示) --- 🔽
class QuizView(discord.ui.View):
    """クイズ用の共通Viewクラス (スプレッドシート連携版 + Discord内で音声・画像を直接表示)"""

    def __init__(self, questions: list[QuizData], bot_title: str):
        super().__init__(timeout=300.0) # 5分でタイムアウト
        self.questions = random.sample(questions, k=len(questions)) # 問題をシャッフル
        self.bot_title = bot_title
        
        # View 自身が状態を持つように変更
        self.current_question_index = 0
        self.correct_count = 0
        self.interaction = None # start() で interaction を保持する
        self.followup_message = None # 🔽 追加: followup メッセージを保持
        
        # 🔽 復習機能 (v2): 各問題の結果を記録
        self.results_history = []  # 各問題の結果を保存するリスト

    async def start(self, interaction: discord.Interaction):
        """
        クイズの開始（bot.pyから呼び出される）
        従来の方式: edit_original_response を使用
        """
        self.interaction = interaction # 親となる interaction を保持
        self.command_name = interaction.command.name if interaction.command else "quiz"
        self.command_id = interaction.data.get('id', '0') if hasattr(interaction, 'data') else '0'
        await self.show_question()

    # 🔽 追加: followup でセッションを開始する新しいメソッド
    async def start_with_followup(self, interaction: discord.Interaction):
        """
        クイズの開始（followup版）
        公開メッセージの後にephemeralセッションを開始する際に使用
        """
        self.interaction = interaction
        self.command_name = interaction.command.name if interaction.command else "quiz"
        self.command_id = interaction.data.get('id', '0') if hasattr(interaction, 'data') else '0'
        await self.show_question_with_followup()
    
    async def download_audio_file(self, audio_url: str):
        """
        音声URLから音声ファイルをダウンロードしてdiscord.Fileオブジェクトを返す
        (v2.9: ephemeralメッセージ内で音声を再生するため)
        """
        try:
            # Googleドライブ URL を変換
            converted_url = QuizData._convert_gdrive_url(audio_url)
            
            # 非同期でファイルをダウンロード
            async with aiohttp.ClientSession() as session:
                async with session.get(converted_url) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        # ファイル名をURLから取得（なければデフォルト）
                        filename = "audio.mp3"
                        if "/" in audio_url:
                            filename = audio_url.split("/")[-1].split("?")[0]
                        
                        # BytesIOオブジェクトを作成
                        audio_bytes = io.BytesIO(audio_data)
                        return discord.File(audio_bytes, filename=filename)
            return None
        except Exception as e:
            print(f"[QuizView] 音声ファイルのダウンロードに失敗: {e}")
            return None

    def create_embed(self, question: QuizData):
        """
        質問のメインEmbed（埋め込みメッセージ）を作成する
        (v2.7: 音声・画像は別途処理)
        """
        embed = discord.Embed(
            title=f"【{self.bot_title}】 - 第{self.current_question_index + 1}問",
            description=f"**{question.question_text}**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"全{len(self.questions)}問 | 正解数: {self.correct_count}")
        return embed
    
    def create_image_embeds(self, question: QuizData):
        """
        画像がある場合、各選択肢用のEmbedを作成する
        (v2.8: Discord内で画像を直接表示)
        """
        image_embeds = []
        has_images = any(img for img in question.option_images)
        
        if has_images:
            label_map = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F", 6: "G", 7: "H", 8: "I"}
            
            for i, (option_text, img_url) in enumerate(zip(question.options, question.option_images)):
                if img_url:
                    converted_url = QuizData._convert_gdrive_url(img_url)
                    embed = discord.Embed(color=discord.Color.blue())
                    embed.set_author(name=f"選択肢 {label_map.get(i, str(i+1))}: {option_text}")
                    embed.set_image(url=converted_url)
                    image_embeds.append(embed)
        
        return image_embeds

    def update_buttons(self, question: QuizData):
        """
        質問に合わせてボタン（選択肢）を動的に作成・更新する
        (v2.7: 画像がある場合はA/B/C/Dボタンに変更)
        """
        self.clear_items() # 既存のボタンをクリア
        
        # 🔽 画像があるかどうかを判定
        has_images = any(img for img in question.option_images)

        # 選択肢の数だけボタンを作成
        for i, option_text in enumerate(question.options):
            # 画像がある場合はA/B/C/Dラベル、ない場合はテキストラベル
            if has_images:
                label_map = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F", 6: "G", 7: "H", 8: "I"}
                label = label_map.get(i, str(i+1))
            else:
                label = option_text
            
            button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"answer_{i+1}" # custom_id に選択肢番号(1始まり)を設定
            )
            button.callback = self.button_callback
            self.add_item(button)

    async def show_question(self):
        """
        現在の質問を表示し、ボタンを更新する
        従来の方式: edit_original_response を使用
        (v2.8: 音声はcontent、画像はEmbedで表示)
        """
        question = self.questions[self.current_question_index]
        main_embed = self.create_embed(question)
        image_embeds = self.create_image_embeds(question)
        self.update_buttons(question)
        
        # 音声URLがある場合はメッセージcontentに含める
        audio_content = None
        if question.audio_url:
            converted_url = QuizData._convert_gdrive_url(question.audio_url)
            audio_content = f"🎵 **音声を再生:**\n{converted_url}"
        
        # すべてのEmbedを結合
        all_embeds = [main_embed] + image_embeds
        
        await self.interaction.edit_original_response(
            content=audio_content,
            embeds=all_embeds,
            view=self
        )

    async def show_question_with_followup(self):
        """
        現在の質問を表示（followup版）
        (v3.1: 音声の有無で処理を分岐し、「読み込めませんでした」エラーを防ぐ)
        """
        question = self.questions[self.current_question_index]
        main_embed = self.create_embed(question)
        image_embeds = self.create_image_embeds(question)
        self.update_buttons(question)
        
        # すべてのEmbedを結合（メインEmbed + 画像Embeds）
        all_embeds = [main_embed] + image_embeds
        
        # 音声ファイルの処理
        audio_file = None
        audio_content = None
        has_audio = False
        
        # audio_url が存在し、かつ空でない場合のみダウンロードを試みる
        if question.audio_url:
            audio_file = await self.download_audio_file(question.audio_url)
            if audio_file:
                audio_content = "🎵 **音声を再生:**"
                has_audio = True
        
        # 🔽 重要な修正: 音声の有無で処理を分岐
        if self.followup_message is None:
            # 最初の質問: 新しいメッセージを送信
            if has_audio:
                self.followup_message = await self.interaction.followup.send(
                    content=audio_content,
                    file=audio_file,
                    embeds=all_embeds,
                    view=self,
                    ephemeral=True,
                    wait=True
                )
            else:
                self.followup_message = await self.interaction.followup.send(
                    embeds=all_embeds,
                    view=self,
                    ephemeral=True,
                    wait=True
                )
        else:
            # 2問目以降の処理
            if has_audio:
                # 音声がある場合: 古いメッセージを編集してボタンを無効化し、
                # 新しいメッセージを送信（この方法で「読み込めませんでした」を回避）
                try:
                    # 前のメッセージのボタンを無効化（削除はしない）
                    for item in self.children:
                        item.disabled = True
                    await self.followup_message.edit(view=self)
                    # ボタンを再度有効化
                    self.update_buttons(question)
                except:
                    pass
                
                # 新しいメッセージを送信
                self.followup_message = await self.interaction.followup.send(
                    content=audio_content,
                    file=audio_file,
                    embeds=all_embeds,
                    view=self,
                    ephemeral=True,
                    wait=True
                )
            else:
                # 音声がない場合: 既存のメッセージを編集
                try:
                    await self.followup_message.edit(
                        content=None,
                        embeds=all_embeds,
                        view=self
                    )
                except discord.errors.NotFound:
                    # メッセージが見つからない場合は新規送信
                    self.followup_message = await self.interaction.followup.send(
                        embeds=all_embeds,
                        view=self,
                        ephemeral=True,
                        wait=True
                    )

    async def button_callback(self, interaction: discord.Interaction):
        """
        いずれかの選択肢ボタンが押されたときの処理
        (v2.7: 画像のみの場合は「選択肢X」と表示)
        """
        
        # 🔽 タイムアウトチェック (v2.4)
        if self.is_finished():
            await interaction.response.send_message(
                f"⏰ このクイズセッションは時間切れで終了しました。\n再度遊ぶ場合は </{self.command_name}:{self.command_id}> をクリックしてください。",
                ephemeral=True
            )
            return
        
        # 2問目以降の操作対象(self.interaction)を、
        # このボタンが押されたメッセージ(interaction)に固定する
        self.interaction = interaction
        
        await interaction.response.defer() # ボタンの応答
        
        question = self.questions[self.current_question_index]
        selected_option_id = interaction.data['custom_id'] # "answer_1" など
        selected_answer = selected_option_id.split('_')[1] # "1"

        is_correct = (selected_answer == question.correct_answer)
        
        # 答え合わせのEmbedを作成
        if is_correct:
            self.correct_count += 1
            color = discord.Color.green()
            title = "⭕ 正解！"
            result_icon = "⭕"
        else:
            color = discord.Color.red()
            title = "❌ 不正解..."
            result_icon = "❌"

        result_embed = discord.Embed(
            title=title,
            description=f"**解説:**\n{question.explanation}",
            color=color
        )
        
        # 正解の選択肢テキストを取得
        correct_index = int(question.correct_answer) - 1
        correct_text = question.options[correct_index]
        
        # 🔽 画像のみの場合は「選択肢X」と表示
        has_images = any(img for img in question.option_images)
        if has_images:
            label_map = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F", 6: "G", 7: "H", 8: "I"}
            correct_label = label_map.get(correct_index, str(correct_index+1))
            result_embed.add_field(name="正解", value=f"選択肢 {correct_label}")
        else:
            result_embed.add_field(name="正解", value=f"{correct_text}")

        # 🔽 復習機能 (v2): 結果を記録
        self.results_history.append({
            'question_number': self.current_question_index + 1,
            'question_text': question.question_text,
            'is_correct': is_correct,
            'result_icon': result_icon,
            'correct_text': correct_text,
            'explanation': question.explanation
        })

        # ボタンを無効化してメッセージを編集 (質問Embed + 結果Embed + 画像Embeds)
        # (v2.9: 音声ファイルは最初に添付されているのでそのまま残る)
        for item in self.children:
            item.disabled = True
        
        main_embed = self.create_embed(question)
        image_embeds = self.create_image_embeds(question)
        all_embeds = [main_embed] + image_embeds + [result_embed]
        
        # 🔽 修正: followup_message を編集（音声ファイルはそのまま）
        if self.followup_message:
            await self.followup_message.edit(embeds=all_embeds, view=self)
        else:
            await interaction.edit_original_response(embeds=all_embeds, view=self)

        # 🔽 待機時間調整 (v2.1): 2秒に設定
        await asyncio.sleep(2.0)

        # 次の問題へ
        self.current_question_index += 1
        if self.current_question_index < len(self.questions):
            if self.followup_message:
                await self.show_question_with_followup()
            else:
                await self.show_question()
        else:
            await self.show_result() # 全問終了

    async def show_result(self):
        """
        最終結果を表示する
        (v2: 復習機能を追加)
        """
        
        total = len(self.questions)
        score = self.correct_count
        percentage = int((score / total) * 100)
        
        # 成績判定
        if percentage >= 90:
            grade = "🏆 マスター!"
            comment = "素晴らしい!あなたは達人です!"
        elif percentage >= 70:
            grade = "🎵 上級者"
            comment = "かなりの知識をお持ちですね!素晴らしいです!"
        elif percentage >= 50:
            grade = "🎼 中級者"
            comment = "良い結果です!もう少し学ぶと更に楽しめますよ!"
        else:
            grade = "🎹 初級者"
            comment = "これから学んでいきましょう!"

        # 結果発表のEmbed
        result_embed = discord.Embed(
            title=f"【{self.bot_title}】 - 結果発表",
            description=f"✨ **{grade}** ✨\n\n正解数: **{score}/{total}問** ({percentage}%)\n\n{comment}",
            color=discord.Color.gold()
        )
        
        self.clear_items() # 全てのボタンを削除
        
        # 🔽 修正: followup_message がある場合はそれを編集（contentをクリア）
        if self.followup_message:
            await self.followup_message.edit(content=None, embeds=[result_embed], view=self)
        else:
            await self.interaction.edit_original_response(content=None, embeds=[result_embed], view=self)
        
        # 🔽 復習機能 (v2): 全問題の詳細を表示
        await self.show_review()
        
        self.stop() # Viewを終了
    
    async def show_review(self):
        """
        復習機能: 全問題の正解/不正解と解説を表示する
        """
        # 復習用のEmbedを作成（複数に分割する可能性あり）
        review_embeds = []
        
        # Discordのfield制限: 1つのEmbedに最大25個のfieldまで
        # 問題が多い場合は複数のEmbedに分割
        MAX_FIELDS_PER_EMBED = 25
        
        for i in range(0, len(self.results_history), MAX_FIELDS_PER_EMBED):
            chunk = self.results_history[i:i + MAX_FIELDS_PER_EMBED]
            
            embed = discord.Embed(
                title=f"📝 復習 - 全問題の詳細",
                description="各問題の正解と解説を確認できます。",
                color=discord.Color.blue()
            )
            
            for result in chunk:
                # フィールド名: 問題番号と正解/不正解
                field_name = f"{result['result_icon']} 第{result['question_number']}問"
                
                # フィールド値: 問題文、正解、解説
                # Discordのfield値の制限: 1024文字まで
                field_value = f"**問題:** {result['question_text']}\n"
                field_value += f"**正解:** {result['correct_text']}\n"
                field_value += f"**解説:** {result['explanation']}"
                
                # 1024文字を超える場合は切り詰める
                if len(field_value) > 1024:
                    field_value = field_value[:1020] + "..."
                
                embed.add_field(
                    name=field_name,
                    value=field_value,
                    inline=False  # 各問題を縦に並べる
                )
            
            review_embeds.append(embed)
        
        # 復習Embedを送信（ephemeralで本人のみに表示）
        for embed in review_embeds:
            await self.interaction.followup.send(embed=embed, ephemeral=True)
    
    async def on_timeout(self):
        """
        タイムアウト時の処理（5分経過）
        """
        # ボタンを無効化
        for item in self.children:
            item.disabled = True
        
        # タイムアウトメッセージを表示
        timeout_embed = discord.Embed(
            title="⏰ タイムアウト",
            description=f"クイズセッションの制限時間（5分）が経過しました。\n\n**正解数:** {self.correct_count}/{self.current_question_index}問\n\n再度遊ぶ場合は </{self.command_name}:{self.command_id}> をクリックしてください。",
            color=discord.Color.orange()
        )
        
        try:
            if self.followup_message:
                await self.followup_message.edit(content=None, embeds=[timeout_embed], view=self)
            else:
                await self.interaction.edit_original_response(content=None, embeds=[timeout_embed], view=self)
        except:
            pass  # メッセージが削除されている場合などのエラーを無視
