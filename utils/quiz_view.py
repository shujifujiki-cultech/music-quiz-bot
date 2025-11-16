# クイズ用の共通Viewクラス
# (フェーズ3: スプレッドシート連携版)

import discord
import random
import asyncio 

# 🔽 --- (新規追加) スプレッドシートのデータを扱うためのクラス --- 🔽
class QuizData:
    """
    スプレッドシートの1行（1問）のデータを格納するクラス
    bot.py がこのクラスのリストを作成して QuizView に渡します
    """
    def __init__(self, record: dict):
        # record は {'question_text': '問題文', 'option_1': '選択肢1', ...} のような辞書
        self.question_id = record.get('question_id', 'N/A')
        self.question_text = record.get('question_text')
        
        # 選択肢 (option_1, option_2, ...) を動的に収集
        self.options = []
        for i in range(1, 10): # option_9 まで自動で探す
            opt = record.get(f'option_{i}')
            # スプレッドシートのセルが空でないことを確認
            if opt is not None and str(opt).strip() != "":
                self.options.append(str(opt))
            else:
                break # option_N が途切れたら終了
        
        self.correct_answer = str(record.get('correct_answer'))
        self.explanation = record.get('explanation')
        
        # バリデーション（データが揃っているか確認）
        if not all([self.question_text, self.options, self.correct_answer, self.explanation]):
            raise ValueError(f"クイズデータに不足があります (ID: {self.question_id}): {record}")
        
        # 正解番号（correct_answer）が選択肢の範囲内かチェック
        try:
            correct_index = int(self.correct_answer) - 1 # 1始まりを0始まりに
            if not (0 <= correct_index < len(self.options)):
                raise ValueError(f"正解番号 '{self.correct_answer}' が選択肢の範囲外です (ID: {self.question_id})")
        except ValueError:
            raise ValueError(f"正解番号 '{self.correct_answer}' が数字ではありません (ID: {self.question_id})")

# 🔽 --- QuizView クラスをスプレッドシート対応に修正 --- 🔽
class QuizView(discord.ui.View):
    """クイズ用の共通Viewクラス (スプレッドシート連携版)"""

    # __init__ を大幅に変更。bot.py から QuizData のリストとタイトルを受け取る
    def __init__(self, questions: list[QuizData], bot_title: str):
        super().__init__(timeout=300.0) # 5分でタイムアウト
        self.questions = random.sample(questions, k=len(questions)) # 問題をシャッフル
        self.bot_title = bot_title
        
        # View 自身が状態を持つように変更
        self.current_question_index = 0
        self.correct_count = 0
        self.interaction = None # start() で interaction を保持する

    async def start(self, interaction: discord.Interaction):
        """
        クイズの開始（bot.pyから呼び出される）
        """
        self.interaction = interaction # 親となる interaction を保持
        await self.show_question()

    def create_embed(self, question: QuizData):
        """
        質問のEmbed（埋め込みメッセージ）を作成する
        """
        embed = discord.Embed(
            title=f"【{self.bot_title}】 - 第{self.current_question_index + 1}問",
            description=f"**{question.question_text}**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"全{len(self.questions)}問 | 正解数: {self.correct_count}")
        return embed

    def update_buttons(self, question: QuizData):
        """
        質問に合わせてボタン（選択肢）を動的に作成・更新する
        """
        self.clear_items() # 既存のボタンをクリア

        # 選択肢の数だけボタンを作成
        for i, option_text in enumerate(question.options):
            button = discord.ui.Button(
                label=f"{option_text}", # スプレッドシートの選択肢テキストをそのままラベルに
                style=discord.ButtonStyle.secondary,
                custom_id=f"answer_{i+1}" # custom_id に選択肢番号(1始まり)を設定
            )
            button.callback = self.button_callback
            self.add_item(button)

    # 🔽 --- show_question 関数を丸ごと置き換えてください (v7) --- 🔽
    async def show_question(self):
        """
        現在の質問を表示し、ボタンを更新する
        """
        question = self.questions[self.current_question_index]
        embed = self.create_embed(question)
        self.update_buttons(question)
        
        # 🔽 --- 修正 (v7) --- 🔽
        # 最初の質問(index=0)でも、2問目以降でも、
        # bot.py で defer された元の (ephemeral) メッセージを「編集」する
        await self.interaction.edit_original_response(embed=embed, view=self)
        # 🔼 --- 修正 (v7) --- 🔼
            
#    async def show_question(self):
#        """
 #       現在の質問を表示し、ボタンを更新する
  #      """
#        question = self.questions[self.current_question_index]
 #       embed = self.create_embed(question)
  #      self.update_buttons(question)
        
        # (ephemeral=True なので、メッセージは本人にしか見えない)
#        if self.current_question_index == 0:
            # 最初の質問 (defer しているので followup.send を使う)
 #           await self.interaction.followup.send(embed=embed, view=self, ephemeral=True)
  #      else:
            # 2問目以降 (メッセージを編集)
  #          await self.interaction.edit_original_response(embed=embed, view=self)

    # 🔽 --- button_callback 関数を丸ごと置き換えてください --- 🔽
    async def button_callback(self, interaction: discord.Interaction):
        """
        いずれかの選択肢ボタンが押されたときの処理
        """
        
        # 🔽 --- 追加: 
        # 2問目以降の操作対象(self.interaction)を、
        # このボタンが押されたメッセージ(interaction)に固定する
        self.interaction = interaction
        # 🔼 --- 追加完了
        
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
        else:
            color = discord.Color.red()
            title = "❌ 不正解..."

        result_embed = discord.Embed(
            title=title,
            description=f"**解説:**\n{question.explanation}",
            color=color
        )
        # 正解の選択肢テキストを取得
        correct_index = int(question.correct_answer) - 1
        correct_text = question.options[correct_index]
        result_embed.add_field(name="正解", value=f"{correct_text}")

        # ボタンを無効化してメッセージを編集 (質問Embed + 結果Embed の2つを表示)
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(embeds=[self.create_embed(question), result_embed], view=self)

        # 3秒待機 (解説を読む時間)
        await asyncio.sleep(3.0)

        # 次の問題へ
        self.current_question_index += 1
        if self.current_question_index < len(self.questions):
            await self.show_question() # 修正された self.interaction を使って編集
        else:
            await self.show_result() # 全問終了

    async def show_result(self):
        """
        最終結果を表示する
        (ご提示いただいた create_result_message のロジックをここに統合)
        """
        
        total = len(self.questions)
        score = self.correct_count
        percentage = int((score / total) * 100)
        
        # 🔽 --- ご提示いただいた素晴らしいロジックを活用 --- 🔽
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
        # 🔼 --- ここまで --- 🔼

        embed = discord.Embed(
            title=f"【{self.bot_title}】 - 結果発表",
            description=f"✨ **{grade}** ✨\n\n正解数: **{score}/{total}問** ({percentage}%)\n\n{comment}",
            color=discord.Color.gold()
        )
        
        self.clear_items() # 全てのボタンを削除
        await self.interaction.edit_original_response(embed=embed, view=self)
        self.stop() # Viewを終了
        
        #  (振り返りメッセージは、1問ずつの即時フィードバックに変更したため不要)