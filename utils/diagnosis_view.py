# 診断用の共通Viewクラス
# (v1.0: 2軸対応、統合conditions形式、タイムアウト処理対応)

import discord
import asyncio

# 🔽 --- 質問データを扱うクラス --- 🔽
class DiagnosisQuestion:
    """
    スプレッドシートの1行（1問）のデータを格納するクラス
    """
    def __init__(self, record: dict):
        self.question_id = record.get('question_id', 'N/A')
        self.question_text = record.get('question_text')
        self.option_1 = record.get('option_1')
        self.option_2 = record.get('option_2')
        self.axis_id = str(record.get('axis_id'))
        self.axis_name = record.get('axis_name', '')
        self.code_1 = str(record.get('code_1'))  # 選択肢1のコード（例: U）
        self.code_2 = str(record.get('code_2'))  # 選択肢2のコード（例: u）
        self.image_url = record.get('image_url', '')
        
        # バリデーション
        if not all([self.question_text, self.option_1, self.option_2, 
                   self.axis_id, self.code_1, self.code_2]):
            raise ValueError(f"診断データに不足があります (ID: {self.question_id}): {record}")


# 🔽 --- 結果データを扱うクラス --- 🔽
class DiagnosisResult:
    """
    スプレッドシートの結果データを格納するクラス
    """
    def __init__(self, record: dict):
        self.type_id = record.get('type_id', 'N/A')
        self.type_code = record.get('type_code')
        self.type_name = record.get('type_name')
        self.conditions = record.get('conditions', '')  # 例: "u>=U,l>=L"
        self.description = record.get('description', '')
        self.strength = record.get('strength', '')
        self.weakness = record.get('weakness', '')
        self.advice = record.get('advice', '')
        self.image_url = record.get('image_url', '')
        
        # バリデーション
        if not all([self.type_code, self.type_name, self.conditions]):
            raise ValueError(f"結果データに不足があります (ID: {self.type_id}): {record}")


# 🔽 --- DiagnosisView クラス --- 🔽
class DiagnosisView(discord.ui.View):
    """診断用の共通Viewクラス"""

    def __init__(self, questions_data: list[DiagnosisQuestion], 
                 results_data: list[DiagnosisResult], bot_title: str):
        super().__init__(timeout=300.0)  # 5分でタイムアウト
        self.questions = questions_data  # 質問はシャッフルしない（順番通り）
        self.results = results_data
        self.bot_title = bot_title
        
        # View 自身が状態を持つ
        self.current_question_index = 0
        self.interaction = None  # start() で interaction を保持
        
        # スコア集計用の辞書（各コードのカウント）
        # 例: {'U': 3, 'u': 3, 'L': 4, 'l': 2}
        self.score_dict = {}

    async def start(self, interaction: discord.Interaction):
        """
        診断の開始（bot.pyから呼び出される）
        """
        self.interaction = interaction
        # コマンド名とIDを取得
        self.command_name = interaction.command.name if interaction.command else "diagnosis"
        self.command_id = interaction.data.get('id', '0') if hasattr(interaction, 'data') else '0'
        await self.show_question()

    def create_embed(self, question: DiagnosisQuestion):
        """
        質問のEmbed（埋め込みメッセージ）を作成する
        """
        embed = discord.Embed(
            title=f"【{self.bot_title}】 - 質問 {self.current_question_index + 1}/{len(self.questions)}",
            description=f"**{question.question_text}**",
            color=discord.Color.blue()
        )
        
        # 軸の情報を追加（オプション）
        if question.axis_name:
            embed.set_footer(text=f"判定項目: {question.axis_name}")
        
        return embed

    def update_buttons(self, question: DiagnosisQuestion):
        """
        質問に合わせてボタン（選択肢）を作成
        診断は常に2択
        """
        self.clear_items()
        
        # 選択肢1のボタン
        button1 = discord.ui.Button(
            label=question.option_1,
            style=discord.ButtonStyle.primary,
            custom_id="option_1"
        )
        button1.callback = self.button_callback
        self.add_item(button1)
        
        # 選択肢2のボタン
        button2 = discord.ui.Button(
            label=question.option_2,
            style=discord.ButtonStyle.secondary,
            custom_id="option_2"
        )
        button2.callback = self.button_callback
        self.add_item(button2)

    async def show_question(self):
        """
        現在の質問を表示し、ボタンを更新する
        """
        question = self.questions[self.current_question_index]
        embed = self.create_embed(question)
        self.update_buttons(question)
        
        await self.interaction.edit_original_response(embed=embed, view=self)

    async def button_callback(self, interaction: discord.Interaction):
        """
        いずれかの選択肢ボタンが押されたときの処理
        """
        # タイムアウトチェック
        if self.is_finished():
            await interaction.response.send_message(
                f"⏰ この診断セッションは時間切れで終了しました。\n再度診断を受ける場合は </{self.command_name}:{self.command_id}> をクリックしてください。",
                ephemeral=True
            )
            return
        
        # 操作対象を更新
        self.interaction = interaction
        await interaction.response.defer()
        
        question = self.questions[self.current_question_index]
        selected_option = interaction.data['custom_id']  # "option_1" or "option_2"
        
        # 選択されたコードを記録
        if selected_option == "option_1":
            selected_code = question.code_1
        else:
            selected_code = question.code_2
        
        # スコア辞書に加算
        if selected_code not in self.score_dict:
            self.score_dict[selected_code] = 0
        self.score_dict[selected_code] += 1
        
        # 短い待機時間（ユーザー体験向上）
        await asyncio.sleep(0.5)
        
        # 次の質問へ
        self.current_question_index += 1
        if self.current_question_index < len(self.questions):
            await self.show_question()
        else:
            await self.show_result()

    def determine_result(self) -> DiagnosisResult:
        """
        スコアから結果タイプを判定する
        conditions を解析して、該当する結果を返す
        """
        for result in self.results:
            if self.check_conditions(result.conditions):
                return result
        
        # 該当する結果がない場合（通常は起こらないはず）
        # デフォルトで最初の結果を返す
        return self.results[0]
    
    def check_conditions(self, conditions_str: str) -> bool:
        """
        conditions 文字列を解析して、条件を満たすかチェック
        
        例: "u>=U,l>=L"
        → u のカウント >= U のカウント AND l のカウント >= L のカウント
        """
        # 条件をカンマで分割
        conditions_list = [c.strip() for c in conditions_str.split(',')]
        
        for condition in conditions_list:
            # 条件を解析（例: "u>=U"）
            if '>=' in condition:
                left, right = condition.split('>=')
                left = left.strip()
                right = right.strip()
                
                # スコアを取得（存在しない場合は0）
                left_score = self.score_dict.get(left, 0)
                right_score = self.score_dict.get(right, 0)
                
                # 条件チェック
                if not (left_score >= right_score):
                    return False
            
            elif '>' in condition:
                left, right = condition.split('>')
                left = left.strip()
                right = right.strip()
                
                left_score = self.score_dict.get(left, 0)
                right_score = self.score_dict.get(right, 0)
                
                if not (left_score > right_score):
                    return False
            
            # 他の演算子（<, <=, ==）も必要に応じて追加可能
        
        # すべての条件を満たした
        return True

    async def show_result(self):
        """
        最終結果を表示する
        """
        # 結果を判定
        result = self.determine_result()
        
        # 結果発表のEmbed
        result_embed = discord.Embed(
            title=f"【{self.bot_title}】 - 診断結果",
            description=f"✨ **{result.type_name}** ✨\n\n{result.description}",
            color=discord.Color.gold()
        )
        
        # 詳細情報をフィールドとして追加
        if result.strength:
            result_embed.add_field(
                name="💪 あなたの強み",
                value=result.strength,
                inline=False
            )
        
        if result.weakness:
            result_embed.add_field(
                name="⚠️ 改善ポイント",
                value=result.weakness,
                inline=False
            )
        
        if result.advice:
            result_embed.add_field(
                name="📝 アドバイス",
                value=result.advice,
                inline=False
            )
        
        # 画像がある場合は設定（オプション）
        # if result.image_url:
        #     result_embed.set_thumbnail(url=result.image_url)
        
        self.clear_items()  # 全てのボタンを削除
        await self.interaction.edit_original_response(embed=result_embed, view=self)
        
        self.stop()  # Viewを終了
    
    async def on_timeout(self):
        """
        タイムアウト時の処理（5分経過）
        """
        for item in self.children:
            item.disabled = True
        
        timeout_embed = discord.Embed(
            title="⏰ タイムアウト",
            description=f"診断セッションの制限時間（5分）が経過しました。\n\n**回答済み:** {self.current_question_index}/{len(self.questions)}問\n\n再度診断を受ける場合は </{self.command_name}:{self.command_id}> をクリックしてください。",
            color=discord.Color.orange()
        )
        
        try:
            await self.interaction.edit_original_response(embed=timeout_embed, view=self)
        except:
            pass  # メッセージが削除されている場合などのエラーを無視
