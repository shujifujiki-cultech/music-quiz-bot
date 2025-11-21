#!/usr/bin/env python3
# デバッグ用スクリプト: Google Sheetsから読み込まれるデータの実際の構造を確認

import sys
import os

# ローカル環境用のインポート（utilsディレクトリから）
from utils.sheets_loader import get_quiz_data
import json

def debug_sheet_data(sheet_name):
    """指定されたシートのデータを詳しく調査"""
    print(f"\n{'='*80}")
    print(f"シート名: {sheet_name}")
    print(f"{'='*80}\n")
    
    # データを取得
    data = get_quiz_data(sheet_name)
    
    if not data:
        print("❌ データの取得に失敗しました")
        return
    
    print(f"✅ データ取得成功: {len(data)} 件")
    print("\n" + "-"*80)
    
    # 最初のレコードを詳しく調査
    if len(data) > 0:
        first_record = data[0]
        print(f"\n📋 1件目のデータ:")
        print(f"\n型: {type(first_record)}")
        print(f"\nキーの一覧 (全 {len(first_record)} 個):")
        
        for i, key in enumerate(first_record.keys(), 1):
            value = first_record[key]
            # キーの詳細情報（見えない文字を検出）
            key_repr = repr(key)  # 文字列の正確な表現
            key_bytes = key.encode('utf-8') if isinstance(key, str) else b''
            
            print(f"\n  [{i}] キー: {key_repr}")
            print(f"      型: {type(key)}")
            print(f"      長さ: {len(key)}")
            print(f"      バイト: {key_bytes}")
            print(f"      値: {repr(value)[:100]}...")  # 最初の100文字のみ
        
        print("\n" + "-"*80)
        print("\n📝 JSON形式での表示 (1件目):")
        print(json.dumps(first_record, ensure_ascii=False, indent=2))
        
        # 特定のキーパターンを検索
        print("\n" + "-"*80)
        print("\n🔍 'option_3' で始まるキーを検索:")
        option3_keys = [k for k in first_record.keys() if 'option_3' in k.lower()]
        for key in option3_keys:
            print(f"  - {repr(key)}")
    
    print("\n" + "="*80 + "\n")

# メイン処理
if __name__ == '__main__':
    print("\n" + "="*80)
    print("🔬 Google Sheets データ構造デバッグツール")
    print("="*80)
    
    # 問題のあるシートを調査
    sheets_to_debug = [
        'q_music_history_easy',
        'q_pitch_challenge_easy'
    ]
    
    for sheet_name in sheets_to_debug:
        try:
            debug_sheet_data(sheet_name)
        except Exception as e:
            print(f"\n❌ エラー発生: {sheet_name}")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ デバッグ完了")
    print("="*80 + "\n")