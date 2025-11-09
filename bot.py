import discord
from discord import app_commands
from discord.ui import Button, View

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

MY_GUILD = discord.Object(id=1432678542898102346)

ALLOWED_CHANNELS = [
    1432682367365156926,  # #雑談・オフトピックチャンネル
    # 必要に応じて追加
]

# クイズの問題データ(20問)
QUESTIONS = [
    {
        "text": "問1: 「音楽の父」と呼ばれ、『G線上のアリア』や『ブランデンブルク協奏曲』などで知られるバロック時代の作曲家は誰でしょう？",
        "options": ["ヘンデル", "J.S.バッハ", "ヴィヴァルディ"],
        "correct": 1
    },
    {
        "text": "問2: オペラ『魔笛』や『フィガロの結婚』、交響曲『ジュピター』などを作曲したオーストリアの天才作曲家は誰でしょう？",
        "options": ["ハイドン", "ベートーヴェン", "モーツァルト"],
        "correct": 2
    },
    {
        "text": "問3: 「運命」という愛称で知られる交響曲第5番や、第9番『合唱付き』を作曲したのは誰でしょう？",
        "options": ["ベートーヴェン", "シューベルト", "ブラームス"],
        "correct": 0
    },
    {
        "text": "問4: イタリアの作曲家で、ヴァイオリン協奏曲集『四季』を作曲したのは誰でしょう？",
        "options": ["コレッリ", "ヴィヴァルディ", "スカルラッティ"],
        "correct": 1
    },
    {
        "text": "問5: 100曲以上の交響曲を作曲し、「交響曲の父」と呼ばれている作曲家は誰でしょう？",
        "options": ["ハイドン", "モーツァルト", "サリエリ"],
        "correct": 0
    },
    {
        "text": "問6: 「ピアノの詩人」と呼ばれ、『英雄ポロネーズ』や『幻想即興曲』など、多くのピアノ曲を残したポーランドの作曲家は誰でしょう？",
        "options": ["リスト", "シューマン", "ショパン"],
        "correct": 2
    },
    {
        "text": "問7: 『美しく青きドナウ』など、優雅なウィンナ・ワルツを多く作曲し、「ワルツ王」と呼ばれたのは誰でしょう？",
        "options": ["ヨハン・シュトラウス2世", "リヒャルト・シュトラウス", "オッフェンバック"],
        "correct": 0
    },
    {
        "text": "問8: バッハやヘンデルが活躍した、豪華で装飾的な芸術が栄えた17世紀〜18世紀半ばの音楽様式は何でしょう？",
        "options": ["バロック音楽", "古典派音楽", "ロマン派音楽"],
        "correct": 0
    },
    {
        "text": "問9: モーツァルトやハイドンが活躍し、調和と形式美を重んじた18世紀後半の音楽様式は何でしょう？",
        "options": ["ルネサンス音楽", "バロック音楽", "古典派音楽"],
        "correct": 2
    },
    {
        "text": "問10: ベートーヴェンに始まり、ショパンやリストが活躍した、個人の感情や情熱的な表現を重視した19世紀の音楽様式は何でしょう？",
        "options": ["古典派音楽", "ロマン派音楽", "印象主義音楽"],
        "correct": 1
    },
    {
        "text": "問11: オペラ『カルメン』を作曲したフランスの作曲家は誰でしょう？",
        "options": ["ビゼー", "ドビュッシー", "サン=サーンス"],
        "correct": 0
    },
    {
        "text": "問12: アメリカ滞在中に、交響曲第9番『新世界より』を作曲したチェコの作曲家は誰でしょう？",
        "options": ["スメタナ", "ドヴォルザーク", "ヤナーチェク"],
        "correct": 1
    },
    {
        "text": "問13: 『魔王』や『野ばら』など600曲以上の歌曲(リート)を作曲し、「歌曲の王」と呼ばれたのは誰でしょう？",
        "options": ["シューベルト", "シューマン", "メンデルスゾーン"],
        "correct": 0
    },
    {
        "text": "問14: ロシアの作曲家で、バレエ音楽『白鳥の湖』『くるみ割り人形』などを作曲したのは誰でしょう？",
        "options": ["ムソルグスキー", "リムスキー=コルサコフ", "チャイコフスキー"],
        "correct": 2
    },
    {
        "text": "問15: 『アイーダ』『椿姫』『リゴレット』など、数多くの傑作オペラを作曲したイタリアの作曲家は誰でしょう？",
        "options": ["ヴェルディ", "プッチーニ", "ロッシーニ"],
        "correct": 0
    },
    {
        "text": "問16: ピアノの前身となった鍵盤楽器で、弦を爪(プレクトラム)で弾いて音を出す楽器は何でしょう？",
        "options": ["パイプオルガン", "チェンバロ", "クラヴィコード"],
        "correct": 1
    },
    {
        "text": "問17: 独唱とピアノ伴奏によって、詩の世界を深く表現するドイツの芸術歌曲のことを何と呼ぶでしょう？",
        "options": ["アリア", "リート", "カンタータ"],
        "correct": 1
    },
    {
        "text": "問18: オペラ『蝶々夫人』や『ラ・ボエーム』で知られる、イタリア・オペラの巨匠は誰でしょう？",
        "options": ["ヴェルディ", "ドニゼッティ", "プッチーニ"],
        "correct": 2
    },
    {
        "text": "問19: ノルウェーの作曲家で、劇音楽『ペール・ギュント』組曲(「朝」などが有名)を作曲したのは誰でしょう？",
        "options": ["グリーグ", "シベリウス", "ニールセン"],
        "correct": 0
    },
    {
        "text": "問20: 一定の旋律(主題)が、リズムや和声を変えながら次々と変化していく形式を何と呼ぶでしょう？",
        "options": ["ソナタ", "ロンド", "変奏曲(ヴァリエーション)"],
        "correct": 2
    }
]

class QuizView(View):
    def __init__(self, question_index, correct_count, user_answers):
        super().__init__(timeout=300)
        self.question_index = question_index
        self.correct_count = correct_count
        self.user_answers = user_answers
        
        question = QUESTIONS[question_index]
        for i, option in enumerate(question["options"]):
            button = Button(
                label=f"({i+1}) {option}", 
                style=discord.ButtonStyle.primary, 
                custom_id=str(i)
            )
            button.callback = self.button_callback
            self.add_item(button)
    
    async def button_callback(self, interaction: discord.Interaction):
        # まず応答を延期(処理時間を確保)
        await interaction.response.defer()
        
        # 選択を記録
        question = QUESTIONS[self.question_index]
        selected_option = int(interaction.data["custom_id"])
        self.user_answers.append(selected_option)
        
        # 正解チェック
        is_correct = selected_option == question["correct"]
        if is_correct:
            self.correct_count += 1
        
        # 次の質問があるか確認
        if self.question_index + 1 < len(QUESTIONS):
            # 次の質問を表示
            next_view = QuizView(self.question_index + 1, self.correct_count, self.user_answers)
            next_question = QUESTIONS[self.question_index + 1]
            
            await interaction.edit_original_response(
                content=f"**問題 {self.question_index + 2}/{len(QUESTIONS)}**\n\n{next_question['text']}",
                view=next_view
            )
        else:
            # 最終結果を表示
            result_message = self.create_result_message()
            await interaction.edit_original_response(
                content=result_message,
                view=None
            )
            
            # 振り返りを送信
            review_messages = self.create_review_messages()
            for review_msg in review_messages:
                await interaction.followup.send(review_msg)
    
    def create_result_message(self):
        total = len(QUESTIONS)
        score = self.correct_count
        percentage = int((score / total) * 100)
        
        if percentage >= 90:
            grade = "🏆 音楽史マスター!"
            comment = "素晴らしい!あなたは音楽史の達人です!"
        elif percentage >= 70:
            grade = "🎵 音楽通"
            comment = "かなりの知識をお持ちですね!素晴らしいです!"
        elif percentage >= 50:
            grade = "🎼 音楽好き"
            comment = "良い結果です!もう少し学ぶと更に楽しめますよ!"
        else:
            grade = "🎹 音楽入門者"
            comment = "これから音楽史を学んでいきましょう!"
        
        result = f"""
✨ **クイズ終了!** ✨

**{grade}**

正解数: **{score}/{total}問** ({percentage}%)

{comment}

もう一度挑戦する場合は `/音楽史クイズ` を実行してください!
"""
        return result
    
    def create_review_messages(self):
        """各問題の振り返りを生成(複数メッセージに分割)"""
        messages = []
        current_message = "📝 **振り返り**\n\n"
        
        for i, question in enumerate(QUESTIONS):
            user_answer = self.user_answers[i]
            correct_answer = question["correct"]
            is_correct = user_answer == correct_answer
            
            # 結果アイコン
            icon = "✅" if is_correct else "❌"
            
            # 問題番号と結果
            review_line = f"{icon} **問{i+1}**: "
            
            if is_correct:
                review_line += f"正解! ({correct_answer+1}) {question['options'][correct_answer]}\n"
            else:
                review_line += f"不正解\n"
                review_line += f"   あなたの回答: ({user_answer+1}) {question['options'][user_answer]}\n"
                review_line += f"   正解: ({correct_answer+1}) {question['options'][correct_answer]}\n"
            
            review_line += "\n"
            
            # メッセージが2000文字を超えそうなら分割
            if len(current_message + review_line) > 1900:
                messages.append(current_message)
                current_message = "📝 **振り返り(続き)**\n\n"
            
            current_message += review_line
        
        # 最後のメッセージを追加
        if current_message:
            messages.append(current_message)
        
        return messages


@client.event
async def on_ready():
    tree.copy_global_to(guild=MY_GUILD)
    await tree.sync(guild=MY_GUILD)
    print(f'{client.user} としてログインしました!')
    print('コマンドを同期しました!')

@tree.command(name="音楽史クイズ", description="音楽史に関する20問のクイズに挑戦!")
async def quiz(interaction: discord.Interaction):
    # ★追加:チャンネルチェック
    if interaction.channel_id not in ALLOWED_CHANNELS:
        await interaction.response.send_message(
            "❌ このチャンネルではクイズを実行できません。\n"
            "#雑談・オフトピックチャンネル内で実行してください。",
            ephemeral=True  # このメッセージは実行者にのみ表示
        )
        return
    
    # 許可されたチャンネルの場合、クイズを開始
    view = QuizView(0, 0, [])
    first_question = QUESTIONS[0]
    await interaction.response.send_message(
        f"🎻 **音楽史クイズ**\n\n**問題 1/{len(QUESTIONS)}**\n\n{first_question['text']}",
        view=view
    )

import os
client.run(os.getenv('DISCORD_TOKEN'))