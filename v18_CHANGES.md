# 📋 bot.py v18 - 変更内容と使用方法

## 🔧 v17 からの変更点

### 問題点（v17）
```python
async def main():
    web_task = asyncio.to_thread(run_web_server)  # ❌ これが問題
    bot_task = run_bot()
    await asyncio.gather(web_task, bot_task)  # Flask が終了するまで待ち続ける
```

**何が起きていたか:**
- `app.run()` は **無限ループ** で、サーバーが停止されるまで制御を返さない
- `asyncio.gather` は最初のタスク（Flask）の完了を待ち続ける
- 結果: ボットタスクが **永遠に実行されない**

---

### 解決策（v18）
```python
async def main():
    # ✅ Flask を daemon thread で起動（await しない）
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # ✅ ボットをメインループで実行
    async with client:
        await client.start(TOKEN)
```

**何が改善されたか:**
1. **Flask は別スレッド** で動作し、メインの asyncio ループをブロックしない
2. **ボットはメインループ** で正常に実行される
3. **`daemon=True`** により、ボットが終了すれば Flask スレッドも自動終了する

---

## 🚀 デプロイ手順

### 1. ローカルでテスト（推奨）

```powershell
# 1. ファイルを置き換え
# bot.py (v18) を既存の bot.py に上書き

# 2. ローカルで起動
python bot.py
```

**期待されるログ:**
```
ターゲットサーバーID: 1432678542898102346 (テスト用)
[Main] (v18) Flask を daemon thread で起動し、ボットをメインループで実行します...
[Web Server] Flask を起動します (ポート: 10000)...
[Main] (v18) Flask サーバーを起動しました。
 * Serving Flask app ''
 * Running on http://127.0.0.1:10000
[Bot] setup_hook: (v18) 処理を開始します (コマンドのロード)...
[Bot] setup_hook: 'bot_master_list' の読み込みを別スレッドで開始...
[Bot] setup_hook: 'bot_master_list' の読み込み完了。
[Bot] X 件のボット設定を読み込みました。
[Bot] setup_hook: X 件のクイズを .tree に登録しました。
[Bot] setup_hook: (v18) コマンドのロードが完了しました。
Logged in as YourBotName (ID: ...)
------
[Bot] on_ready: (v18) 処理を開始します (コマンドの同期)...
[Bot] on_ready: (v18) ★★★ コマンドの同期が完了しました ★★★
```

### 2. Discord で動作確認

1. サーバーのチャンネルで `/` を入力
2. `quiz_music_history_easy` などのコマンド候補が表示されることを確認
3. コマンドを実行してクイズが正常に動作することを確認

### 3. GitHub にプッシュ

```powershell
# ローカルで動作確認できたら
git add bot.py
git commit -m "fix: v18 - Flask を daemon thread で起動し asyncio ブロック問題を解決"
git push origin main
```

### 4. Render で自動デプロイ

1. Render ダッシュボードでデプロイが開始されることを確認
2. ログで以下が表示されることを確認:
   - `[Main] (v18) Flask を daemon thread で起動...`
   - `Logged in as ...`
   - `[Bot] on_ready: (v18) ★★★ コマンドの同期が完了しました ★★★`

---

## 🔍 トラブルシューティング

### ローカルで起動しない場合

**症状:** `ModuleNotFoundError: No module named 'XXX'`
**解決:** 
```powershell
pip install -r requirements.txt
```

---

### Render でログが途中で止まる場合

**症状:** `[Main] (v18) Flask サーバーを起動しました。` の後にログが出ない

**確認事項:**
1. **DISCORD_TOKEN** が正しく設定されているか
2. **GUILD_ID** が正しく設定されているか
3. **credentials.json** が Secret File として設定されているか

**確認方法:**
Render ダッシュボード → Environment → 各変数の値を確認

---

### コマンドが表示されない場合

**原因:** Discord のキャッシュ

**解決手順:**
1. Discord クライアントを **完全に終了**（タスクトレイも）
2. Discord を再起動
3. サーバーで `/` を入力して確認

それでもダメな場合は、ボットを再招待:
1. Discord Developer Portal → OAuth2 → URL Generator
2. Scopes: `bot`, `applications.commands` にチェック
3. Bot Permissions: `Send Messages`, `Embed Links` にチェック
4. 生成された URL でサーバーに再招待

---

## 📊 期待される結果

### Render のログ（正常時）
```
==> Running 'python bot.py'
ターゲットサーバーID: 1432678542898102346 (テスト用)
[Main] (v18) Flask を daemon thread で起動し、ボットをメインループで実行します...
[Web Server] Flask を起動します (ポート: 10000)...
[Main] (v18) Flask サーバーを起動しました。
 * Serving Flask app ''
 * Running on all addresses (0.0.0.0)
 * Running on http://10.16.123.139:10000
127.0.0.1 - - [18/Nov/2025 XX:XX:XX] "HEAD / HTTP/1.1" 200 -
==> Your service is live 🎉
[Bot] setup_hook: (v18) 処理を開始します (コマンドのロード)...
[Bot] setup_hook: 'bot_master_list' の読み込みを別スレッドで開始...
[SheetsLoader] Googleスプレッドシートへの認証に成功しました。
[SheetsLoader] スプレッドシート 'Bot一覧シート' を開きました。
[SheetsLoader] シート 'bot_master_list' から X 件のデータを取得しました。
[Bot] setup_hook: 'bot_master_list' の読み込み完了。
[Bot] X 件のボット設定を読み込みました。
[Bot] setup_hook: X 件のクイズを .tree に登録しました。
[Bot] setup_hook: (v18) コマンドのロードが完了しました。
Logged in as YourBotName (ID: ...)
------
[Bot] on_ready: (v18) 処理を開始します (コマンドの同期)...
[Bot] on_ready: ギルド 1432678542898102346 のコマンドをクリアします...
[Bot] on_ready: (v18) ★★★ コマンドの同期が完了しました ★★★
127.0.0.1 - - [18/Nov/2025 XX:XX:XX] "GET / HTTP/1.1" 200 -
```

### Discord での動作（正常時）
1. `/` を入力 → コマンド候補が表示される
2. `/quiz_music_history_easy` を実行 → クイズが開始される
3. 問題に回答 → 正解/不正解が表示される
4. 全問終了 → 結果が表示される

---

## 🎯 次のステップ（v18 動作確認後）

### フェーズ4: コンテンツの量産
v18 が正常に動作したら、コードを触らずに **Google スプレッドシート** だけでコンテンツを追加できます。

**やること:**
1. `q_music_history_hard` シートを作成（音楽史【上】20問）
2. `bot_master_list` に新しい行を追加
3. ボットが自動的に新しいコマンドを認識（5分後のキャッシュ更新）

**メリット:**
- ✅ コードを編集する必要がない
- ✅ デプロイする必要がない
- ✅ プログラマー以外でもコンテンツを追加できる

---

## 📞 サポート

問題が解決しない場合は、以下の情報を共有してください:

1. **Render のログ全体**（特に `[Bot] on_ready:` 以降）
2. **Discord Developer Portal** でのインテント設定のスクリーンショット
3. **Render の Environment 変数**（値は伏せて、キー名のみ）

---

**最終更新:** 2025/11/18
**バージョン:** v18
