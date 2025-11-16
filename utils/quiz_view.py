#クイズ用の共通Viewクラス
#全てのクイズで使用する共通ロジック

import discord
from discord.ui import Button, View


class QuizView(View):
    """クイズ用の共通Viewクラス"""
    
    def __init__(self, questions, question_index, correct_count, user_answers):
        super().__init__(timeout=300)
        self.questions = questions
        self.question_index = question_index
        self.correct_count = correct_count
        self.user_answers = user_answers
        
        question = questions[question_index]
        for i, option in enumerate(question["options"]):
            button = Button(
                label=f"({i+1}) {option}", 
                style=discord.ButtonStyle.primary, 
                custom_id=str(i)
            )
            button.callback = self.button_callback
            self.add_item(button)
    
    async def button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        question = self.questions[self.question_index]
        selected_option = int(interaction.data["custom_id"])
        self.user_answers.append(selected_option)
        
        is_correct = selected_option == question["correct"]
        if is_correct:
            self.correct_count += 1
        
        if self.question_index + 1 < len(self.questions):
            next_view = QuizView(self.questions, self.question_index + 1, self.correct_count, self.user_answers)
            next_question = self.questions[self.question_index + 1]
            
            await interaction.edit_original_response(
                content=f"**問題 {self.question_index + 2}/{len(self.questions)}**\n\n{next_question['text']}",
                view=next_view
            )
        else:
            result_message = self.create_result_message()
            await interaction.edit_original_response(
                content=result_message,
                view=None
            )
            
            review_messages = self.create_review_messages()
            for review_msg in review_messages:
                await interaction.followup.send(review_msg)
    
    def create_result_message(self):
        total = len(self.questions)
        score = self.correct_count
        percentage = int((score / total) * 100)
        
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
        
        return f"""
✨ **クイズ終了!** ✨

**{grade}**

正解数: **{score}/{total}問** ({percentage}%)

{comment}
"""
    
    def create_review_messages(self):
        messages = []
        current_message = "📝 **振り返り**\n\n"
        
        for i, question in enumerate(self.questions):
            user_answer = self.user_answers[i]
            correct_answer = question["correct"]
            is_correct = user_answer == correct_answer
            
            icon = "✅" if is_correct else "❌"
            review_line = f"{icon} **問{i+1}**: "
            
            if is_correct:
                review_line += f"正解! ({correct_answer+1}) {question['options'][correct_answer]}\n"
            else:
                review_line += f"不正解\n"
                review_line += f"   あなたの回答: ({user_answer+1}) {question['options'][user_answer]}\n"
                review_line += f"   正解: ({correct_answer+1}) {question['options'][correct_answer]}\n"
            
            review_line += "\n"
            
            if len(current_message + review_line) > 1900:
                messages.append(current_message)
                current_message = "📝 **振り返り(続き)**\n\n"
            
            current_message += review_line
        
        if current_message:
            messages.append(current_message)
        
        return messages