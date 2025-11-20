# CULTECH音楽教育Discordbot 開発ドキュメント

**プロジェクト名:** CULTECH音楽教育Discordbot  
**プロジェクトオーナー:** 藤川修爾CEO  
**最終更新日:** 2025年11月19日  
**現在のバージョン:** v2.10（音声画像クイズ対応）

---

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [開発の経緯と変遷](#開発の経緯と変遷)
3. [現在の状況](#現在の状況)
4. [システムアーキテクチャ](#システムアーキテクチャ)
5. [ファイル構成と役割](#ファイル構成と役割)
6. [データフロー](#データフロー)
7. [スプレッドシート構造](#スプレッドシート構造)
8. [今後の開発ガイド](#今後の開発ガイド)
9. [トラブルシューティング](#トラブルシューティング)

---

## プロジェクト概要

### 目的
バイオリン学習者向けのインタラクティブな音楽教育Discordbotを開発し、音感クイズや姿勢診断などの教育コンテンツを提供する。

### 主要機能
- **クイズ機能**: テキスト、音声、画像を組み合わせたクイズ
- **診断機能**: 姿勢チェックなど、質問に基づく診断結果の提供
- **動的コマンド登録**: Googleスプレッドシートから自動的にコマンドを生成
- **復習機能**: クイズ終了後に全問題の解説を表示
- **YouTube連携**: 診断結果にYouTube動画を埋め込み

### 技術スタック
- **言語**: Python 3.10
- **フレームワーク**: discord.py
- **データベース**: Google Sheets（無料）
- **ホスティング**: Render.com（自動デプロイ）
- **バージョン管理**: GitHub

---

## 開発の経緯と変遷

### フェーズ1: 基本クイズ機能（v1.0 - v2.5）
- テキストベースのクイズ機能を実装
- Googleスプレッドシートとの連携
- 動的なコマンド登録システム
- 復習機能の追加

### フェーズ2: 診断機能追加（v2.6 - v2.7）
- 姿勢診断など、2軸4結果パターンの診断システム
- YouTube動画埋め込み機能
- 拡張可能な診断ロジック

### フェーズ3: 音声画像クイズ対応（v2.7 - v2.10）
**2025年11月19日の開発セッション**

#### 実装した機能
1. **音声対応**
   - スプレッドシートに `audio_url` カラムを追加
   - 音声ファイルの読み込みとダウンロード機能
   - GoogleドライブURL自動変換

2. **画像対応**
   - スプレッドシートに `option_X_image` カラムを追加（最大9選択肢分）
   - 画像の埋め込み表示
   - 画像がある場合はA/B/C/Dボタン表示

3. **Discord内表示最適化**
   - 画像を `Embed.set_image()` で埋め込み → Discord内で直接表示
   - 音声ファイルを公開メッセージで送信 → 音声プレーヤーが表示される

#### 直面した問題と解決策

**問題1: カラム名の不一致**
- **症状**: `question_text` を読み込もうとしていたが、スプレッドシートは `text`
- **原因**: コードとスプレッドシートの設計時のカラム名が異なっていた
- **解決**: `record.get('question_text')` → `record.get('text')` に修正

**問題2: スプレッドシートのtypo**
- **症状**: `option_3_image` が `option_3image` になっていた（アンダースコア抜け）
- **原因**: スプレッドシート編集時のミス
- **解決**: Googleスプレッドシートのヘッダー行を修正

**問題3: Googleドライブの音声が外部リンクになる**
- **症状**: 音声URLをクリックすると外部ブラウザが開く
- **原因**: GoogleドライブのURLは「ダウンロードページ」へのリンク
- **解決**: Discord CDNにファイルをアップロードする方式に変更

**問題4: Discord CDNの音声URLでチャンネル遷移**
- **症状**: 音声URLをクリックすると元のチャンネルに遷移
- **原因**: ephemeralメッセージではURLがリンクとして表示される（Discordの仕様）
- **解決**: 音声ファイルを直接添付する方式に変更（v2.9）

**問題5: 添付ファイルがダウンロードとして表示される**
- **症状**: ephemeralメッセージで音声ファイルを添付すると、ダウンロードボタンとして表示される
- **原因**: ephemeralメッセージでは音声プレーヤーが正常に動作しない（Discordの仕様）
- **解決**: 音声を公開メッセージで送信、問題はephemeralで送信（v2.10）

---

## 現在の状況

### ✅ 実現できたこと

1. **音声画像クイズの基本機能**
   - 音声ファイル、画像ファイル、テキストを組み合わせたクイズ
   - Discord CDNから音声・画像を高速読み込み
   - 画像はDiscord内で直接表示

2. **スムーズなユーザー体験**
   - 画像が瞬時に表示される（Discord CDN）
   - 問題と選択肢は本人のみに表示（ephemeral）
   - 復習機能で全問題の解説を確認可能

3. **柔軟なデータ管理**
   - スプレッドシートで問題数を自由に変更可能
   - 選択肢の数も自動判定（3つでも4つでもOK）
   - 音声・画像の有無を問わず動作

### 🔶 現在の問題点

**音声の表示方式（Discordの仕様上の制限）**

#### 状況
ephemeralメッセージ（本人のみに表示）では、音声プレーヤーが正常に動作しません。

#### 現在の対応（v2.10）
- **音声**: 公開メッセージで送信 → 音声プレーヤーが表示される
- **問題・選択肢・画像**: ephemeralメッセージで送信 → 本人のみに表示

#### メリット
- ✅ 音声プレーヤーが正常に表示される
- ✅ セッション内で音声再生が完結
- ✅ 問題や答えは隠される

#### デメリット
- ⚠️ 音声だけは全員に見える（問題文は見えない）
- ⚠️ チャンネルが少し賑やかになる

#### 代替案の検討結果
以下を試みましたが、すべてDiscordの仕様上の制限により不可能でした：

| 方法 | 結果 | 理由 |
|-----|------|-----|
| ephemeral + URL貼り付け | ❌ | リンクとして表示、クリックで遷移 |
| ephemeral + ファイル添付 | ❌ | ダウンロードボタンとして表示 |
| ephemeral + Embed埋め込み | ❌ | 音声Embedは非対応 |

**結論:** 現在の方式（音声は公開、問題はephemeral）が最も実用的

### 🎯 やりたいこと（長期目標）

1. **音声をセッション内で完全に隠す**
   - 理想: ephemeralメッセージ内で音声プレーヤーが動作する
   - 現実: Discordの仕様上不可能（現時点）
   - 対応: Discord APIの将来的なアップデートを待つ

2. **コンテンツの拡充**
   - 音感クイズのバリエーション追加
   - 楽譜読解クイズ
   - リズム感クイズ
   - 奏法テクニッククイズ

3. **診断機能の拡張**
   - より多くの診断軸（3軸、4軸など）
   - 診断結果のグラフ表示

---

## システムアーキテクチャ

### 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│                        Discord ユーザー                       │
└────────────────────┬────────────────────────────────────────┘
                     │ /コマンド実行
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      Discord Bot (Render.com)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ bot.py (v21)                                         │   │
│  │  - コマンド登録（setup_hook）                         │   │
│  │  - クイズ/診断の実行処理                              │   │
│  │  - interaction の管理                                 │   │
│  └───────┬──────────────────────────────────────────────┘   │
│          │ import                                            │
│  ┌───────▼──────────────────────────────────────────────┐   │
│  │ utils/quiz_view.py (v2.10)                           │   │
│  │  - QuizData: スプレッドシートデータの格納             │   │
│  │  - QuizView: クイズUI・ロジック                       │   │
│  │  - 音声ダウンロード・ファイル添付                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ utils/diagnosis_view.py (v1.1)                       │   │
│  │  - DiagnosisQuestion/Result: 診断データの格納         │   │
│  │  - DiagnosisView: 診断UI・ロジック                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ utils/sheets_loader.py                               │   │
│  │  - Google Sheets API連携                             │   │
│  │  - データ読み込み・キャッシュ（5分）                   │   │
│  └───────┬──────────────────────────────────────────────┘   │
└──────────┼──────────────────────────────────────────────────┘
           │ gspread API
           ▼
┌─────────────────────────────────────────────────────────────┐
│               Google Sheets（無料データベース）                │
│  - bot_master_list: コマンド一覧                             │
│  - q_*: クイズデータ                                          │
│  - d_*_q: 診断質問データ                                      │
│  - d_*_r: 診断結果データ                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Discord CDN                               │
│  - 音声ファイル（MP3）                                        │
│  - 画像ファイル（PNG, JPG）                                   │
└─────────────────────────────────────────────────────────────┘
```

### データフロー

#### クイズ実行の流れ

```
1. ユーザーが /quiz_name を実行
   ↓
2. bot.py: setup_hook で登録されたコマンドを実行
   ↓
3. bot.py: run_quiz_command が呼び出される
   ↓
4. sheets_loader.py: get_quiz_data(sheet_name) でデータ取得
   ↓ (キャッシュがあれば使用、なければAPI呼び出し)
5. bot.py: QuizData オブジェクトのリストを作成
   ↓
6. bot.py: 公開メッセージを送信「ユーザーがクイズに挑戦します」
   ↓
7. quiz_view.py: QuizView.start_with_followup() を呼び出し
   ↓
8. quiz_view.py: 最初の問題を表示
   ├─ 音声がある場合: 公開メッセージで音声ファイルを送信
   └─ 問題・選択肢・画像: ephemeralメッセージで送信
   ↓
9. ユーザーが選択肢ボタンをクリック
   ↓
10. quiz_view.py: button_callback で正解判定
    ↓
11. quiz_view.py: 正解/不正解のEmbedを表示（2秒待機）
    ↓
12. 次の問題へ（ステップ8に戻る）または結果発表
    ↓
13. quiz_view.py: show_result() で最終結果表示
    ↓
14. quiz_view.py: show_review() で全問題の復習
```

---

## ファイル構成と役割

### プロジェクト構造

```
CULTECH音楽教育Discordbot/
├── bot.py                          # メインファイル（v21）
├── .env                            # 環境変数（DISCORD_TOKEN, GUILD_ID）
├── requirements.txt                # 依存パッケージ
├── utils/
│   ├── __init__.py
│   ├── quiz_view.py                # クイズUI・ロジック（v2.10）
│   ├── diagnosis_view.py           # 診断UI・ロジック（v1.1）
│   └── sheets_loader.py            # Google Sheets連携
├── credentials/
│   └── google_sheets_credentials.json  # Google API認証情報
└── docs/
    └── (このドキュメント)
```

### 各ファイルの詳細

#### 1. bot.py（メインファイル - v21）

**役割:**
- Discordボットのエントリーポイント
- コマンドの動的登録
- クイズ・診断の実行処理
- Flask（Render対応）

**主要なクラス・関数:**

```python
class MyClient(discord.Client):
    # Discordクライアントのカスタムクラス
    
    async def setup_hook(self):
        # 起動時にコマンドを動的に登録
        # 1. bot_master_list を読み込み
        # 2. クイズ/診断を判定
        # 3. コマンドを tree に追加
    
    async def run_quiz_command(self, interaction, sheet_name, bot_title, allowed_channel_id):
        # クイズコマンドの実行処理
        # 1. データ読み込み
        # 2. QuizData オブジェクト作成
        # 3. 公開メッセージ送信
        # 4. QuizView.start_with_followup() 呼び出し
    
    async def run_diagnosis_command(self, interaction, sheet_questions, sheet_results, bot_title, allowed_channel_id):
        # 診断コマンドの実行処理
        # (クイズと同様の流れ)
```

**重要なポイント:**
- `setup_hook`: Discord接続「前」に実行（コマンド登録）
- `on_ready`: Discord接続「後」に実行（コマンド同期）
- `interaction.response.defer(ephemeral=False)`: 公開でdefer
- `interaction.edit_original_response()`: 公開メッセージを編集
- `QuizView.start_with_followup()`: ephemeralセッション開始

---

#### 2. utils/quiz_view.py（クイズUI・ロジック - v2.10）

**役割:**
- スプレッドシートデータの格納（QuizData）
- クイズのUI表示とロジック（QuizView）
- 音声ダウンロード・ファイル添付
- 画像の埋め込み表示

**主要なクラス:**

##### QuizData
```python
class QuizData:
    """スプレッドシートの1行（1問）のデータを格納"""
    
    def __init__(self, record: dict):
        self.question_id = record.get('question_id')
        self.question_text = record.get('text')  # ← 'question_text'ではなく'text'
        
        # 選択肢を動的に収集（空欄まで）
        self.options = []
        for i in range(1, 10):
            opt = record.get(f'option_{i}')
            if opt and str(opt).strip() != "":
                self.options.append(str(opt))
            else:
                break
        
        # 画像URLを動的に収集
        self.option_images = []
        for i in range(1, len(self.options) + 1):
            img_url = record.get(f'option_{i}_image')
            self.option_images.append(img_url if img_url else None)
        
        # 音声URL
        self.audio_url = record.get('audio_url')
        
        self.correct_answer = str(record.get('correct_answer'))
        self.explanation = record.get('explanation')
    
    @staticmethod
    def _convert_gdrive_url(url: str) -> str:
        """GoogleドライブURLを埋め込み可能な形式に変換"""
        # file/d/FILE_ID/view → uc?export=view&id=FILE_ID
```

##### QuizView
```python
class QuizView(discord.ui.View):
    """クイズのUI表示とロジック"""
    
    def __init__(self, questions: list[QuizData], bot_title: str):
        super().__init__(timeout=300.0)  # 5分でタイムアウト
        self.questions = random.sample(questions, k=len(questions))  # シャッフル
        self.current_question_index = 0
        self.correct_count = 0
        self.results_history = []  # 復習用
    
    async def start_with_followup(self, interaction):
        """公開メッセージ後にephemeralセッション開始"""
        self.interaction = interaction
        await self.show_question_with_followup()
    
    async def download_audio_file(self, audio_url: str):
        """音声ファイルをダウンロードしてdiscord.Fileオブジェクトを返す"""
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url) as response:
                audio_data = await response.read()
                return discord.File(io.BytesIO(audio_data), filename="audio.mp3")
    
    def create_embed(self, question: QuizData):
        """メインEmbed（問題文）を作成"""
    
    def create_image_embeds(self, question: QuizData):
        """画像Embedsを作成（Discord内で画像を直接表示）"""
        image_embeds = []
        for i, img_url in enumerate(question.option_images):
            if img_url:
                embed = discord.Embed()
                embed.set_author(name=f"選択肢 {label}: {option_text}")
                embed.set_image(url=converted_url)
                image_embeds.append(embed)
        return image_embeds
    
    def update_buttons(self, question: QuizData):
        """選択肢ボタンを動的に作成"""
        # 画像がある場合: A/B/C/Dラベル
        # テキストのみの場合: 選択肢テキストをラベルに
    
    async def show_question_with_followup(self):
        """問題を表示（followup版）"""
        # 🔽 重要: 音声は公開メッセージ、問題はephemeral
        if question.audio_url:
            audio_file = await self.download_audio_file(question.audio_url)
            await self.interaction.followup.send(
                content=f"🎵 {user_mention}さんの{bot_title} - 第{n}問の音声",
                file=audio_file,
                ephemeral=False  # 公開メッセージ
            )
        
        # 問題と選択肢はephemeral
        self.followup_message = await self.interaction.followup.send(
            embeds=[main_embed] + image_embeds,
            view=self,
            ephemeral=True
        )
    
    async def button_callback(self, interaction):
        """選択肢ボタンがクリックされた時の処理"""
        # 1. 正解判定
        # 2. 正解/不正解のEmbed表示
        # 3. 2秒待機
        # 4. 次の問題へ
    
    async def show_result(self):
        """最終結果を表示"""
        # 成績判定（マスター/上級者/中級者/初級者）
        # 復習機能の呼び出し
    
    async def show_review(self):
        """復習: 全問題の正解と解説を表示"""
        # 各問題をfield形式で表示
        # 1つのEmbedに25個まで
```

**重要なポイント:**
- `record.get('text')`: スプレッドシートのカラム名は `text`（`question_text`ではない）
- 選択肢数は自動判定: 3つでも4つでも9つでもOK
- 画像の有無も自動判定: `any(img for img in question.option_images)`
- 音声は公開メッセージ、問題はephemeralメッセージ（v2.10の重要な変更）

---

#### 3. utils/diagnosis_view.py（診断UI・ロジック - v1.1）

**役割:**
- 診断質問・結果データの格納
- 診断のUI表示とロジック
- 2軸4結果パターンの判定
- YouTube動画の埋め込み

**主要なクラス:**

```python
class DiagnosisQuestion:
    """診断質問データ"""
    def __init__(self, record: dict):
        self.question_id = record.get('question_id')
        self.text = record.get('text')
        self.option_1 = record.get('option_1')
        self.option_2 = record.get('option_2')
        self.axis_id = record.get('axis_id')  # 軸ID（例: 'u', 'l'）
        self.code_1 = record.get('code_1')    # 選択肢1のコード（例: 'u', 'U'）
        self.code_2 = record.get('code_2')    # 選択肢2のコード（例: 'u', 'U'）

class DiagnosisResult:
    """診断結果データ"""
    def __init__(self, record: dict):
        self.type_id = record.get('type_id')
        self.code = record.get('code')            # 例: "ul", "Ul", "uL", "UL"
        self.name = record.get('name')
        self.conditions = record.get('conditions')  # 判定条件（例: "u>=U,l>=L"）
        self.description = record.get('description')
        self.strength = record.get('strength')
        self.weakness = record.get('weakness')
        self.advice = record.get('advice')
        self.youtube_url = record.get('youtube_url')

class DiagnosisView(discord.ui.View):
    """診断のUI表示とロジック"""
    # クイズとほぼ同じ構造
    # 違いは判定ロジック: 各軸のスコアを集計して結果を判定
```

**重要なポイント:**
- 2軸4結果: 各軸で大文字/小文字をカウント → 結果コードを生成
- 拡張可能: 軸を追加すれば3軸8結果、4軸16結果も可能
- YouTube URL: followup.send() で別メッセージとして送信

---

#### 4. utils/sheets_loader.py（Google Sheets連携）

**役割:**
- Google Sheets APIとの連携
- データの読み込みとキャッシュ（5分間）
- エラーハンドリング

**主要な関数:**

```python
# キャッシュ設定
CACHE_DURATION = 5 * 60  # 5分間キャッシュ
_cache = {}

def get_bot_master_list():
    """bot_master_listシートからコマンド一覧を取得"""
    # 1. キャッシュを確認
    # 2. なければGoogleスプレッドシートから取得
    # 3. キャッシュに保存して返却

def get_quiz_data(sheet_name: str):
    """クイズデータを取得"""
    # 1. キャッシュを確認
    # 2. なければGoogleスプレッドシートから取得
    # 3. コメント行（#で始まる行）をスキップ
    # 4. 辞書形式に変換: {'question_id': 'q1', 'text': '問題文', ...}
    # 5. キャッシュに保存して返却

def get_diagnosis_data(sheet_name: str):
    """診断データを取得（クイズと同様）"""
```

**重要なポイント:**
- キャッシュは5分間有効 → Botを再起動すればすぐに反映
- スプレッドシートの1行目はヘッダー行として自動認識
- コメント行（`#`で始まる行）は自動的にスキップ
- 辞書のキーはスプレッドシートのカラム名そのまま

---

## データフロー

### クイズデータの流れ（詳細）

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ユーザーがコマンド実行: /pitch_challenge_easy             │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. bot.py: run_quiz_command()                               │
│    - interaction.response.defer(ephemeral=False)            │
│      → 公開でdefer（「考え中...」表示）                      │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. sheets_loader.py: get_quiz_data('q_pitch_challenge_easy')│
│    ┌──────────────────────────────────────────────────┐    │
│    │ キャッシュ確認:                                   │    │
│    │  - ある → キャッシュを返却                        │    │
│    │  - ない → Google Sheets APIを呼び出し             │    │
│    └──────────────────────────────────────────────────┘    │
│    ┌──────────────────────────────────────────────────┐    │
│    │ データ変換:                                       │    │
│    │  - ヘッダー行を取得                               │    │
│    │  - 各行を辞書に変換                               │    │
│    │    例: {'question_id': 'q1', 'text': '問題文',   │    │
│    │         'option_1': '選択肢1', ...}              │    │
│    └──────────────────────────────────────────────────┘    │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. bot.py: QuizDataオブジェクトのリスト作成                  │
│    quiz_data_list = [QuizData(q) for q in questions_data]  │
│                                                             │
│    各QuizDataオブジェクトで:                                 │
│    - question_textの取得（'text'カラム）                    │
│    - optionsの動的収集（空欄まで）                           │
│    - option_imagesの動的収集                                │
│    - audio_urlの取得                                        │
│    - バリデーション                                          │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. bot.py: 公開メッセージを送信                              │
│    await interaction.edit_original_response(                │
│        content="@Shuji_Violinが音感チャレンジに挑戦！"       │
│    )                                                        │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. bot.py: QuizViewを作成してセッション開始                  │
│    view = QuizView(quiz_data_list, bot_title)              │
│    await view.start_with_followup(interaction)             │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. quiz_view.py: 最初の問題を表示                           │
│    await self.show_question_with_followup()                │
│                                                             │
│    🔽 音声がある場合:                                        │
│    ┌──────────────────────────────────────────────────┐    │
│    │ audio_file = await download_audio_file(url)      │    │
│    │ await interaction.followup.send(                │    │
│    │     content="🎵 第1問の音声",                    │    │
│    │     file=audio_file,                            │    │
│    │     ephemeral=False  ← 公開メッセージ           │    │
│    │ )                                               │    │
│    └──────────────────────────────────────────────────┘    │
│                                                             │
│    🔽 問題・選択肢・画像:                                    │
│    ┌──────────────────────────────────────────────────┐    │
│    │ main_embed = create_embed(question)              │    │
│    │ image_embeds = create_image_embeds(question)     │    │
│    │ update_buttons(question)                         │    │
│    │                                                  │    │
│    │ await interaction.followup.send(                │    │
│    │     embeds=[main_embed] + image_embeds,         │    │
│    │     view=self,                                  │    │
│    │     ephemeral=True  ← 本人のみに表示            │    │
│    │ )                                               │    │
│    └──────────────────────────────────────────────────┘    │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. ユーザーが選択肢ボタンをクリック                          │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. quiz_view.py: button_callback()                         │
│    - 正解判定                                                │
│    - 正解/不正解のEmbed表示                                  │
│    - results_historyに記録（復習用）                         │
│    - 2秒待機                                                 │
│    - 次の問題へ（ステップ7に戻る）                           │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. 全問終了: show_result()                                 │
│     - 成績判定（正解率に応じて）                              │
│     - 結果Embedを表示                                        │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 11. 復習機能: show_review()                                 │
│     - 全問題の正解と解説をephemeralメッセージで送信          │
│     - 各問題をfield形式で表示                                │
└─────────────────────────────────────────────────────────────┘
```

---

## スプレッドシート構造

### 1. bot_master_list（コマンド一覧）

**役割:** Botに登録するコマンドを定義

| カラム名 | 説明 | 例 |
|---------|------|---|
| command_name | コマンド名 | pitch_challenge_easy |
| bot_title | クイズのタイトル | 音感チャレンジ【初】 |
| sheet_questions | クイズシート名（クイズの場合） | q_pitch_challenge_easy |
| sheet_results | 結果シート名（診断の場合） | d_posture_r |
| type | 種類 | クイズ / 診断 |
| is_active | 有効化 | TRUE / FALSE |
| allowed_channel_id | 許可チャンネルID（オプション） | 1234567890 / N/A |

**例:**
```csv
command_name,bot_title,sheet_questions,sheet_results,type,is_active,allowed_channel_id
pitch_challenge_easy,音感チャレンジ【初】,q_pitch_challenge_easy,,クイズ,TRUE,N/A
pitch_challenge_medium,音感チャレンジ【中】,q_pitch_challenge_medium,,クイズ,TRUE,N/A
posture_diagnosis,姿勢診断,d_posture_q,d_posture_r,診断,TRUE,N/A
```

---

### 2. q_*（クイズデータ）

**ヘッダー行:**
```csv
question_id,text,option_1,option_1_image,option_2,option_2_image,option_3,option_3_image,option_4,option_4_image,correct_answer,explanation,audio_url
```

**各カラムの説明:**

| カラム名 | 必須 | 説明 | 例 |
|---------|-----|------|---|
| question_id | ✅ | 問題ID（一意） | q1, q2, q3 |
| text | ✅ | 問題文 | この楽器は何? |
| option_1 | ✅ | 選択肢1のテキスト | ヴァイオリン |
| option_1_image | ⭕ | 選択肢1の画像URL | https://cdn.discordapp.com/... |
| option_2 | ✅ | 選択肢2のテキスト | ヴィオラ |
| option_2_image | ⭕ | 選択肢2の画像URL | （空欄でも可） |
| option_3 | ✅ | 選択肢3のテキスト | チェロ |
| option_3_image | ⭕ | 選択肢3の画像URL | （空欄でも可） |
| option_4 | ⭕ | 選択肢4のテキスト | （空欄でも可） |
| option_4_image | ⭕ | 選択肢4の画像URL | （空欄でも可） |
| correct_answer | ✅ | 正解番号（1-4） | 1 |
| explanation | ✅ | 解説 | ヴァイオリンの音色です |
| audio_url | ⭕ | 音声URL | https://cdn.discordapp.com/... |

**データ例:**

```csv
question_id,text,option_1,option_1_image,option_2,option_2_image,option_3,option_3_image,option_4,option_4_image,correct_answer,explanation,audio_url
q1,この楽器は?,ヴァイオリン,,ヴィオラ,,チェロ,,,,,1,ヴァイオリンの音色です,https://cdn.discordapp.com/.../violin.mp3
q2,正しい楽譜は?,選択肢A,https://cdn.discordapp.com/.../A.png,選択肢B,https://cdn.discordapp.com/.../B.png,選択肢C,https://cdn.discordapp.com/.../C.png,,,1,Aが正しいです,https://cdn.discordapp.com/.../audio.mp3
q3,この音楽用語は?,フォルテ,,ピアノ,,メゾ,,,,,1,フォルテは強くです,
```

**重要な注意事項:**
- **カラム名は厳密に一致すること**: `text`（`question_text`ではない）
- **option_X_imageのアンダースコア**: `option_3_image`（`option_3image`ではない）
- **選択肢は3つでもOK**: option_4は空欄でも自動判定される
- **コメント行**: 行頭に `#` をつけると無視される

---

### 3. d_*_q（診断質問データ）

**ヘッダー行:**
```csv
question_id,text,option_1,option_2,axis_id,axis_name,code_1,code_2
```

**各カラムの説明:**

| カラム名 | 説明 | 例 |
|---------|------|---|
| question_id | 質問ID | q1 |
| text | 質問文 | 頭の位置は? |
| option_1 | 選択肢1 | 前に出ている |
| option_2 | 選択肢2 | まっすぐ |
| axis_id | 軸ID | u |
| axis_name | 軸の名前 | 上半身 |
| code_1 | 選択肢1のコード | U（大文字=問題あり） |
| code_2 | 選択肢2のコード | u（小文字=良好） |

---

### 4. d_*_r（診断結果データ）

**ヘッダー行:**
```csv
type_id,code,name,conditions,description,strength,weakness,advice,youtube_url
```

**各カラムの説明:**

| カラム名 | 説明 | 例 |
|---------|------|---|
| type_id | 結果ID | 1 |
| code | 結果コード | ul |
| name | 結果名 | バランス型 |
| conditions | 判定条件 | u>=U,l>=L |
| description | 説明 | 上半身も下半身も良好です |
| strength | 強み | 姿勢が安定している |
| weakness | 弱み | （特になし） |
| advice | アドバイス | この調子で練習を続けてください |
| youtube_url | YouTube URL | https://www.youtube.com/watch?v=... |

**判定条件の書き方:**
- `u>=U`: u軸で小文字（良好）が大文字（問題あり）以上
- `,`（カンマ）でAND条件
- 例: `u>=U,l>=L` = 両方とも良好

---

## 今後の開発ガイド

### 開発を再開する際の手順

1. **現状確認**
   - このドキュメントの「現在の状況」セクションを読む
   - 最新のコードバージョンを確認（bot.py: v21, quiz_view.py: v2.10）

2. **環境セットアップ**
   - ローカル環境で動作確認
   - 必要に応じてパッケージをアップデート

3. **変更を加える前に**
   - 影響範囲を確認（どのファイルを変更する必要があるか）
   - バックアップを取る
   - Gitでコミット

4. **テスト**
   - ローカルでテスト
   - Discordの専用テストチャンネルで動作確認
   - 問題なければ本番環境にデプロイ

---

### よくある変更パターン

#### パターン1: 新しいクイズを追加

**手順:**
1. Googleスプレッドシートに新しいシート作成（例: `q_rhythm_quiz`）
2. ヘッダー行をコピー
3. 問題データを入力
4. `bot_master_list`に新しい行を追加
   ```csv
   rhythm_quiz,リズムクイズ,q_rhythm_quiz,,クイズ,TRUE,N/A
   ```
5. Botを再起動
6. `/rhythm_quiz` コマンドで確認

**変更が必要なファイル:**
- Googleスプレッドシートのみ（コードは変更不要）

---

#### パターン2: 選択肢を5つに増やす

**現状:** option_1〜option_4（最大4つ）

**変更手順:**
1. **スプレッドシート**: option_5, option_5_image カラムを追加
2. **コード変更は不要**: QuizDataクラスが自動的に認識

**理由:**
```python
# quiz_view.py: QuizData.__init__
for i in range(1, 10):  # option_9 まで自動で探す
    opt = record.get(f'option_{i}')
    if opt and str(opt).strip() != "":
        self.options.append(str(opt))
    else:
        break  # 空欄で終了
```

---

#### パターン3: タイムアウト時間を延長

**現状:** 5分（300秒）

**変更箇所:**
```python
# utils/quiz_view.py: QuizView.__init__
def __init__(self, questions: list[QuizData], bot_title: str):
    super().__init__(timeout=300.0)  # ← ここを変更
```

**推奨設定:**
- 10問まで: 300秒（5分）
- 15問まで: 600秒（10分）
- 30問まで: 900秒（15分）

---

#### パターン4: 音声を完全にephemeralにしたい

**現状:** Discordの仕様上不可能

**将来的な対応:**
1. Discord APIのアップデートを待つ
2. Discord公式ドキュメントを定期的にチェック
3. ephemeralメッセージで音声プレーヤーが動作するようになったら、以下を変更:

```python
# utils/quiz_view.py: show_question_with_followup
# 修正前（v2.10）
await self.interaction.followup.send(
    file=audio_file,
    ephemeral=False  # 公開メッセージ
)

# 修正後（将来）
await self.interaction.followup.send(
    file=audio_file,
    embeds=all_embeds,
    view=self,
    ephemeral=True  # ephemeralで音声が動作するようになったら
)
```

---

### コード修正時の注意事項

#### 1. カラム名は厳密に一致させる

**誤り:**
```python
self.question_text = record.get('question_text')  # ❌
```

**正しい:**
```python
self.question_text = record.get('text')  # ✅
```

**確認方法:**
- スプレッドシートのヘッダー行を確認
- sheets_loader.pyが返す辞書のキーを確認

---

#### 2. ephemeral vs 公開メッセージ

**ephemeral（本人のみに表示）:**
```python
await interaction.followup.send(
    content="これは本人のみに表示",
    ephemeral=True
)
```

**公開メッセージ（全員に表示）:**
```python
await interaction.followup.send(
    content="これは全員に表示",
    ephemeral=False
)
```

**使い分け:**
- クイズの問題・選択肢: ephemeral
- 音声ファイル: 公開（v2.10の制約）
- クイズ開始メッセージ: 公開

---

#### 3. キャッシュの扱い

**キャッシュの仕組み:**
- sheets_loader.pyが5分間データをキャッシュ
- スプレッドシートを更新しても、すぐには反映されない

**即座に反映する方法:**
- Botを再起動する（最も確実）
- 5分以上待つ

---

## トラブルシューティング

### よくあるエラーと解決方法

#### エラー1: クイズデータに不足があります

**エラーメッセージ:**
```
エラー: クイズデータの形式が正しくありません。(sheet: q_xxx): 
クイズデータに不足があります (ID: q1): {...}
```

**原因:**
1. スプレッドシートのカラム名が間違っている
2. 必須カラムが空欄
3. カラム名にtypo（例: `option_3image`）

**解決方法:**
1. スプレッドシートのヘッダー行を確認
2. エラーメッセージの辞書部分を確認
   - どのキーが存在するか
   - どのキーが抜けているか
3. 該当カラムを修正
4. Botを再起動

---

#### エラー2: No module named 'aiohttp'

**原因:**
aiohttpパッケージがインストールされていない

**解決方法:**

**ローカル:**
```bash
pip install aiohttp --break-system-packages
```

**Render:**
requirements.txtに追加:
```txt
aiohttp
```

---

#### エラー3: 音声プレーヤーが表示されない

**原因1:** ephemeralメッセージで音声を送信している
- **解決:** 音声は公開メッセージで送信（v2.10）

**原因2:** ファイル形式が非対応
- **対応形式:** MP3, WAV, M4A, OGG
- **推奨:** MP3

**原因3:** ファイルが削除されている
- Discord CDNのURLが無効
- 元のチャンネルでファイルが削除されていないか確認

---

#### エラー4: 画像が表示されない

**原因1:** URLが間違っている
- Discord CDN形式: `https://cdn.discordapp.com/attachments/.../image.png`

**原因2:** ファイルが削除されている
- 元のチャンネルで画像が削除されていないか確認

**原因3:** ファイル形式が非対応
- **対応形式:** PNG, JPG, JPEG, GIF, WEBP

---

#### エラー5: コマンドが表示されない

**原因1:** bot_master_listで`is_active`がFALSE
- **解決:** TRUEに変更

**原因2:** コマンドが同期されていない
- **解決:** Botを再起動してon_readyで同期

**原因3:** GUILD_IDが間違っている
- **解決:** .envファイルのGUILD_IDを確認

---

### デバッグ方法

#### 1. ログを確認

**Render:**
- ダッシュボード → Logs
- エラーメッセージを検索

**ローカル:**
- ターミナルの出力を確認

**重要なログ:**
```
[Bot] setup_hook: コマンドのロードが完了
[Bot] on_ready: コマンドの同期が完了
[Bot] {user} のために {sheet_name} の読み込みを開始
[Bot] {sheet_name} の読み込み完了
[SheetsLoader] シート '{sheet_name}' から {n} 件のデータを取得
```

---

#### 2. スプレッドシートのデータを確認

**手動でデータを取得:**
```python
# Python コンソールで
from utils import sheets_loader
data = sheets_loader.get_quiz_data('q_pitch_challenge_easy')
print(data[0])  # 最初の問題を表示
```

**確認ポイント:**
- 辞書のキーが正しいか
- 値が空でないか

---

#### 3. QuizDataオブジェクトを確認

```python
from utils.quiz_view import QuizData
record = {'question_id': 'q1', 'text': '問題', 'option_1': '選択肢1', ...}
quiz_data = QuizData(record)
print(quiz_data.question_text)
print(quiz_data.options)
print(quiz_data.option_images)
```

---

## 付録

### 依存パッケージ一覧（requirements.txt）

```txt
# Discord Bot
discord.py>=2.0.0

# 環境変数
python-dotenv

# Google Sheets連携
gspread
oauth2client

# Render対応（ヘルスチェック用）
Flask

# 音声ファイルダウンロード用
aiohttp
```

---

### 環境変数（.env）

```env
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_guild_id_here
```

---

### Googleスプレッドシート構造（サマリー）

```
スプレッドシート名: CULTECH音楽教育Bot用データ

シート一覧:
├── bot_master_list      # コマンド一覧
├── q_pitch_challenge_easy    # 音感クイズ（初級）
├── q_pitch_challenge_medium  # 音感クイズ（中級）
├── d_posture_q          # 姿勢診断（質問）
└── d_posture_r          # 姿勢診断（結果）
```

---

### 連絡先

**プロジェクトオーナー:** 藤川修爾CEO  
**プロジェクト:** CULTECH Corporation  

---

**このドキュメントは開発を再開する際の完全なガイドです。数日後に戻ってきたら、まずこのドキュメントを読んでから作業を始めてください。**

---

**最終更新:** 2025年11月19日  
**バージョン:** 1.0