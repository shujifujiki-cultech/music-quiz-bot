#設定ファイル
#サーバーIDやチャンネルIDなどの設定を管理


import discord

# サーバーID(あなたのDiscordサーバーのID)
MY_GUILD_ID = 1432678542898102346  # ここに数字を入力

# 各クイズ/診断で使用できるチャンネルID
CHANNELS = {
    'music_history_quiz': [
        1432682367365156926,
        1432682411019473038,  # 音楽史クイズを許可するチャンネルID
    ],
    'violin_quiz': [
        1432682367365156926,
        1432682411019473038,  # バイオリンクイズを許可するチャンネルID
    ],
    'composer_quiz': [
        1432682367365156926,
        1432682411019473038,  # 作曲家クイズを許可するチャンネルID
    ],
    'violinist_diagnosis': [
        1432682367365156926,
        1432682411019473038,  # 演奏家診断を許可するチャンネルID
    ],
}

# Google Sheets設定(後で使用)
GOOGLE_SHEETS_ID = ''  # 後で設定
GOOGLE_SHEETS_CREDENTIALS = 'credentials.json'  # 後で設定