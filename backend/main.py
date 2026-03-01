"""FastAPI サーバー — PDF → Excel 変換 API を提供する。

フロントエンドから PDF をアップロードすると、解析して
指定テンプレートに転記した Excel をダウンロードさせる。

セキュリティ対策:
- PDFアップロードサイズ制限（10MB）
- タイムアウト設定（keep-alive 120秒）
- 基本的なエラーハンドリング（グローバル例外ハンドラ）
- HTTPS通信の確保（本番環境でHTTPSリダイレクト）
- CORS設定の適切な実装（メソッド・ヘッダー限定）
- セキュリティヘッダー設定（7種類のヘッダー付与）
"""

import logging
import os
import re

from excel_writer import write_to_excel
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pdf_parser import parse_pdf
from starlette.middleware.base import BaseHTTPMiddleware

# --- ログ設定 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 環境設定 ---
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
TRUSTED_HOSTS = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",")

# --- 定数 ---
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "aichi.xlsx")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()


# =============================================
# ミドルウェア設定
# =============================================


# --- 1. セキュリティヘッダーミドルウェア ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """すべてのレスポンスにセキュリティヘッダーを付与するミドルウェア。

    各ヘッダーの目的:
    - X-Content-Type-Options: MIMEタイプスニッフィング防止
    - X-Frame-Options: クリックジャッキング防止
    - X-XSS-Protection: 古いブラウザのXSSフィルター有効化
    - Strict-Transport-Security: HTTPS強制（HSTS）
    - Content-Security-Policy: 外部リソース読み込み制限
    - Referrer-Policy: リファラー情報漏洩防止
    - Permissions-Policy: ブラウザ機能アクセス制限
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)


# --- 2. CORS設定（メソッド・ヘッダーを必要最小限に制限） ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600,  # プリフライトキャッシュ10分
)

# --- 3. HTTPS / 信頼ホスト（本番環境のみ） ---
if ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)


# =============================================
# グローバル例外ハンドラ
# =============================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException をJSON形式で返却する。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """未処理の例外をキャッチし、安全なエラーレスポンスを返す。"""
    logger.error("予期しないエラーが発生しました: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "サーバー内部でエラーが発生しました。しばらくしてから再試行してください。"
        },
    )


# =============================================
# ユーティリティ関数
# =============================================


def secure_filename(filename: str) -> str:
    """ファイル名をサニタイズしてパストラバーサル攻撃を防止する。

    - ディレクトリ区切り文字を除去
    - 特殊文字を除去
    - 空文字の場合はデフォルト名を返す
    """
    # パス区切り文字を除去
    filename = os.path.basename(filename)
    # 安全な文字のみ保持（日本語・英数字・ドット・ハイフン・アンダースコア）
    filename = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF.\-]", "_", filename)
    # 空文字チェック
    if not filename or filename == ".":
        filename = "uploaded.pdf"
    return filename


# =============================================
# APIエンドポイント
# =============================================


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """PDF を受け取り、Excel に変換してダウンロードさせる。"""

    # --- バリデーション: ファイル形式チェック ---
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="PDFファイルのみアップロード可能です"
        )

    # --- バリデーション: ファイルサイズチェック（10MB制限） ---
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"ファイルサイズが上限（{MAX_FILE_SIZE // (1024 * 1024)}MB）を超えています",
        )

    # --- ファイル名サニタイズ（パストラバーサル防止） ---
    safe_filename = secure_filename(file.filename or "uploaded.pdf")
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # --- PDF を一時保存 ---
    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    try:
        # PDF 解析
        bs_data, pl_data, cr_data = parse_pdf(file_path)

        # Excel 生成
        output_path = write_to_excel(TEMPLATE_PATH, bs_data, pl_data, cr_data)

        # ダウンロードファイル名（元の PDF 名をベースにする）
        base_name = os.path.splitext(safe_filename)[0]
        download_name = f"{base_name}_報告書.xlsx"

        return FileResponse(
            path=output_path,
            filename=download_name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        logger.error("PDF処理中にエラーが発生しました: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="PDFの処理中にエラーが発生しました。ファイルの形式を確認してください。",
        ) from e

    finally:
        # アップロードされた PDF を削除
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        reload=True,
        timeout_keep_alive=120,  # タイムアウト設定: 長いPDF処理に対応
    )
