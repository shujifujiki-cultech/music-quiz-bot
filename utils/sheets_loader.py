import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import time

# --- 定数 ---

# 認証情報ファイル（.gitignoreに追加したもの）
CREDENTIALS_FILE = 'credentials.json'

# Google APIのスコープ（スプレッドシートとDrive APIを使用）
SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

# Googleスプレッドシートのファイル名
# ※※※【要設定】※※※
# あなたが作成したスプレッドシートの「ファイル名」をここに設定してください。
SPREADSHEET_NAME = 'Bot一覧シート' 

# キャッシュの有効時間（秒）
# (APIの呼び出し回数を減らすため。300秒 = 5分)
CACHE_EXPIRATION = 300 

# --- グローバル変数（キャッシュ用） ---
g_client = None
g_spreadsheet = None
g_cache = {} # シート名ごとのデータをキャッシュする

def _get_gspread_client():
    """Googleスプレッドシートに接続するためのクライアントを取得する"""
    global g_client
    if g_client:
        return g_client

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, SCOPE
        )
        client = gspread.authorize(creds)
        g_client = client
        print("[SheetsLoader] Googleスプレッドシートへの認証に成功しました。")
        return client
    except Exception as e:
        print(f"[SheetsLoader] ERROR: 認証に失敗しました: {e}")
        print(f"[SheetsLoader] ヒント: 1. '{CREDENTIALS_FILE}' が存在しますか？")
        print("[SheetsLoader] ヒント: 2. スプレッドシート側でサービスアカウントのメールアドレスを「共有」しましたか？")
        return None

def _get_spreadsheet():
    """スプレッドシート本体（ブック全体）を取得する"""
    global g_spreadsheet
    if g_spreadsheet:
        return g_spreadsheet
        
    client = _get_gspread_client()
    if not client:
        return None

    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        g_spreadsheet = spreadsheet
        print(f"[SheetsLoader] スプレッドシート '{SPREADSHEET_NAME}' を開きました。")
        return spreadsheet
    except gspread.SpreadsheetNotFound:
        print(f"[SheetsLoader] ERROR: スプレッドシート '{SPREADSHEET_NAME}' が見つかりません。")
        print("[SheetsLoader] ヒント: 1. SPREADSHEET_NAME の設定は正しいですか？")
        print("[SheetsLoader] ヒント: 2. サービスアカウントをスプレッドシートに「共有」しましたか？")
        return None
    except Exception as e:
        print(f"[SheetsLoader] ERROR: スプレッドシートを開けません: {e}")
        return None

def _fetch_sheet_data(sheet_name):
    """
    指定されたシート名のデータを取得し、辞書のリストとして返す
    (例: get_all_records() は1行目をヘッダーとして扱います)
    """
    spreadsheet = _get_spreadsheet()
    if not spreadsheet:
        return None

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        # .get_all_records() は、1行目をキーにした辞書のリストを返します
        # これがメモ[cite: 91]にある「データ変換処理」の核となります
        records = worksheet.get_all_records()
        print(f"[SheetsLoader] シート '{sheet_name}' から {len(records)} 件のデータを取得しました。")
        return records
    except gspread.WorksheetNotFound:
        print(f"[SheetsLoader] ERROR: シート '{sheet_name}' が見つかりません。")
        return None
    except Exception as e:
        print(f"[SheetsLoader] ERROR: シート '{sheet_name}' の読み込み中にエラー: {e}")
        return None

def load_sheet_data(sheet_name):
    """
    指定されたシート名のデータを取得する（キャッシュを利用）
    外部（bot.pyなど）からはこの関数を呼び出す
    """
    global g_cache
    current_time = time.time()

    # キャッシュのチェック
    if sheet_name in g_cache:
        cached_data, timestamp = g_cache[sheet_name]
        if current_time - timestamp < CACHE_EXPIRATION:
            print(f"[SheetsLoader] シート '{sheet_name}' のキャッシュを利用します。")
            return cached_data

    # キャッシュがないか、古い場合はデータを再取得
    print(f"[SheetsLoader] シート '{sheet_name}' のデータをAPIから取得します...")
    data = _fetch_sheet_data(sheet_name)
    
    if data is not None:
        # データをキャッシュに保存
        g_cache[sheet_name] = (data, current_time)
        
    return data

# --- bot.py から利用する関数 ---

def get_bot_master_list():
    """
    ボットのマスターリスト（bot_master_list）を取得する
    """
    return load_sheet_data('bot_master_list')

def get_quiz_data(sheet_name):
    """
    指定されたクイズシートのデータを取得する
    (例: 'q_music_history_easy')
    """
    return load_sheet_data(sheet_name)

def get_diagnosis_data(sheet_name):
    """
    指定された診断シート（質問・結果）のデータを取得する
    (例: 'd_violinist_type_q' や 'd_violinist_type_r')
    """
    return load_sheet_data(sheet_name)

# --- 動作確認用のメイン処理 ---
if __name__ == '__main__':
    print("--- [SheetsLoader] 動作テスト開始 ---")
    
    # 1. マスターリストの読み込みテスト
    master_list = get_bot_master_list()
    if master_list:
        print("\n[テスト成功] マスターリストの読み込み:")
        print(f"  {len(master_list)} 件のボット設定を発見。")
        print(f"  1件目のデータ: {master_list[0]}")
    else:
        print("\n[テスト失敗] マスターリストの読み込みに失敗しました。")

    # 2. クイズシートの読み込みテスト
    # (bot_master_listが読み込めていれば、そのシート名を拝借)
    if master_list and master_list[0].get('sheet_questions'):
        test_sheet = master_list[0]['sheet_questions']
        print(f"\n--- 2. '{test_sheet}' の読み込みテスト ---")
        quiz_data = get_quiz_data(test_sheet)
        if quiz_data:
            print(f"\n[テスト成功] クイズデータの読み込み:")
            print(f"  {len(quiz_data)} 件の質問を発見。")
            print(f"  1件目のデータ: {quiz_data[0]}")
        else:
            print(f"\n[テスト失敗] クイズデータの読み込みに失敗しました。")

    print("\n--- [SheetsLoader] 動作テスト終了 ---")