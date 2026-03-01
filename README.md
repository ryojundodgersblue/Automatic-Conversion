# 事業年度終了報告書 自動変換システム

建設業の確定申告書 PDF を、事業年度終了報告書 Excel に自動で変換するWebアプリケーション。

## 技術スタック

| レイヤー       | 技術                                                                     |
| -------------- | ------------------------------------------------------------------------ |
| フロントエンド | React 19 + TypeScript + Vite + TailwindCSS                               |
| バックエンド   | Python + FastAPI + pdfplumber + openpyxl                                 |
| テスト         | pytest（バックエンド）/ Vitest + React Testing Library（フロントエンド） |

## ディレクトリ構成

```
doc/
├── backend/                   # バックエンド（FastAPI）
│   ├── main.py                # APIサーバー + セキュリティ設定
│   ├── pdf_parser.py          # PDF解析モジュール
│   ├── excel_writer.py        # Excel書き込みモジュール
│   ├── requirements.txt       # Python依存パッケージ
│   ├── templates/             # Excel テンプレート
│   ├── uploads/               # 一時アップロードディレクトリ
│   └── tests/                 # バックエンド単体テスト
│       ├── test_pdf_parser.py # PDF解析テスト（278テスト）
│       ├── test_excel_writer.py # Excel書き込みテスト
│       └── test_main.py       # API + セキュリティテスト
├── frontend/                  # フロントエンド（React + Vite）
│   ├── src/
│   │   ├── pages/ReportComplete/  # メインページ
│   │   │   ├── ReportComplete.tsx
│   │   │   ├── ReportComplete.css
│   │   │   └── ReportComplete.test.tsx  # コンポーネントテスト
│   │   └── test/setup.ts      # テストセットアップ
│   ├── vitest.config.ts       # Vitest設定
│   └── package.json
├── security_audit.md          # セキュリティ監査レポート
└── README.md                  # このファイル
```

## セットアップ手順

### 1. バックエンド

```bash
cd backend

# 仮想環境の作成・有効化
python3 -m venv .venv
source .venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt

# テスト用ライブラリのインストール
pip install pytest pytest-asyncio httpx

# サーバー起動
python3 main.py
```

サーバーは `http://localhost:8000` で起動します。

### 2. フロントエンド

```bash
cd frontend

# 依存パッケージのインストール
npm install

# 開発サーバー起動
npm run dev
```

ブラウザで `http://localhost:5173` にアクセスします。

## 使い方

1. ブラウザで `http://localhost:5173` を開く
2. 「PDFファイルを選択」ボタンをクリック
3. 確定申告書 PDF を選択
4. 自動で変換されて Excel ファイルがダウンロードされる

### 制限事項

- PDFファイルのみアップロード可能
- ファイルサイズ上限: 10MB
- 処理タイムアウト: 60秒

## テスト実行

### バックエンドテスト

```bash
cd backend
source .venv/bin/activate
python3 -m pytest tests/ -v
```

### フロントエンドテスト

```bash
cd frontend
npm run test
```

### テスト一覧

| テストファイル            | テスト数 | 内容                                                                   |
| ------------------------- | -------- | ---------------------------------------------------------------------- |
| `test_pdf_parser.py`      | 278      | 勘定科目認識（多表記対応）、類似名称判定、△処理、セクション判定        |
| `test_excel_writer.py`    | 21       | 千円単位変換、合算計算、比率計算、ゼロ除算防止                         |
| `test_main.py`            | 14       | API正常系/異常系、セキュリティヘッダー、CORS、secure_filename          |
| `ReportComplete.test.tsx` | 13       | UI表示、サイズ制限、エラーメッセージ、タイムアウト、ネットワークエラー |

## 本番デプロイ時の環境変数

```bash
# HTTPS強制を有効化
ENVIRONMENT=production

# 許可するオリジン（カンマ区切り）
CORS_ORIGINS=https://yourdomain.com

# 信頼するホスト（カンマ区切り）
TRUSTED_HOSTS=yourdomain.com,www.yourdomain.com
```

## セキュリティ対策

詳細は [security_audit.md](security_audit.md) を参照。

- ✅ PDFアップロードサイズ制限（10MB）
- ✅ タイムアウト設定（フロント60秒 / バック120秒）
- ✅ エラーハンドリング（グローバル例外ハンドラ + ファイル名サニタイズ）
- ✅ HTTPS通信の確保（本番環境でHTTPSリダイレクト）
- ✅ CORS設定（メソッド・ヘッダー限定）
- ✅ セキュリティヘッダー（7種類）
