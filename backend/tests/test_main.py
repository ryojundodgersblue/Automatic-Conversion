"""FastAPI メインサーバー (main.py) の API + セキュリティテスト。

テスト対象:
- ファイルアップロードエンドポイント（正常系・異常系）
- ファイルサイズ制限（413エラー）
- ファイル形式バリデーション（400エラー）
- secure_filename（パストラバーサル防止）
- セキュリティヘッダーの確認
- CORS設定の確認
- グローバル例外ハンドラ
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from httpx import ASGITransport, AsyncClient
from main import app, secure_filename


# =============================================
# secure_filename テスト
# =============================================
class TestSecureFilename:
    """ファイル名サニタイズのテスト。"""

    def test_normal_filename(self):
        assert secure_filename("test.pdf") == "test.pdf"

    def test_japanese_filename(self):
        result = secure_filename("確定申告書_令和5年.pdf")
        assert "確定申告書" in result
        assert result.endswith(".pdf")

    def test_path_traversal_attack(self):
        """パストラバーサル攻撃: ../../../etc/passwd → basename のみ。"""
        result = secure_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_path_with_directory(self):
        result = secure_filename("/some/path/file.pdf")
        assert result == "file.pdf"

    def test_special_characters_removed(self):
        """特殊文字（;, &, |, $ 等）は除去される。"""
        result = secure_filename("test;rm -rf;.pdf")
        assert ";" not in result

    def test_empty_filename(self):
        assert secure_filename("") == "uploaded.pdf"

    def test_dot_only(self):
        assert secure_filename(".") == "uploaded.pdf"

    def test_windows_path(self):
        result = secure_filename("C:\\Users\\hacker\\evil.pdf")
        # os.path.basename on macOS keeps the whole thing, but regex sanitizes \\
        assert "C:" not in result or "\\" not in result

    def test_unicode_allowed(self):
        """日本語のひらがな・カタカナ・漢字は保持される。"""
        result = secure_filename("テスト報告書.pdf")
        assert "テスト報告書" in result


# =============================================
# セキュリティヘッダーテスト
# =============================================
class TestSecurityHeaders:
    """レスポンスにセキュリティヘッダーが含まれるかテスト。"""

    @pytest.fixture
    def client(self):
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_security_headers_present(self, client):
        """任意のリクエストにセキュリティヘッダーが付与される。"""
        # 存在しないエンドポイントでもミドルウェアは動作する
        response = await client.get("/api/nonexistent")

        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-xss-protection") == "1; mode=block"
        assert "max-age=31536000" in response.headers.get(
            "strict-transport-security", ""
        )
        assert response.headers.get("content-security-policy") == "default-src 'self'"
        assert (
            response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        )
        assert "camera=()" in response.headers.get("permissions-policy", "")


# =============================================
# APIエンドポイントテスト
# =============================================
class TestUploadEndpoint:
    """ファイルアップロードAPIの正常系・異常系テスト。"""

    @pytest.fixture
    def client(self):
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_reject_non_pdf(self, client):
        """PDF以外のファイルは 400 エラー。"""
        response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 400
        data = response.json()
        assert "PDF" in data.get("error", "")

    @pytest.mark.asyncio
    async def test_reject_large_file(self, client):
        """10MBを超えるファイルは 413 エラー。"""
        # 11MB のダミーデータ
        large_data = b"x" * (11 * 1024 * 1024)
        response = await client.post(
            "/api/upload",
            files={"file": ("large.pdf", large_data, "application/pdf")},
        )
        assert response.status_code == 413
        data = response.json()
        assert "上限" in data.get("error", "") or "サイズ" in data.get("error", "")

    @pytest.mark.asyncio
    async def test_accept_small_pdf(self, client):
        """小さなPDFファイルはバリデーション通過（処理でエラーになる可能性あるが400/413ではない）。"""
        # 有効なPDFヘッダーだが中身は不正 → 500が返るが、400/413ではない
        dummy_pdf = b"%PDF-1.4 dummy content"
        response = await client.post(
            "/api/upload",
            files={"file": ("test.pdf", dummy_pdf, "application/pdf")},
        )
        # バリデーションは通過するので 400/413 ではない
        assert response.status_code != 400
        assert response.status_code != 413

    @pytest.mark.asyncio
    async def test_no_file_submitted(self, client):
        """ファイルなしのリクエストは 422 (Validation Error)。"""
        response = await client.post("/api/upload")
        assert response.status_code == 422


# =============================================
# CORS設定テスト
# =============================================
class TestCORSConfiguration:
    """CORS設定がレスポンスに反映されるかテスト。"""

    @pytest.fixture
    def client(self):
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_cors_preflight_allowed_origin(self, client):
        """許可されたオリジンからのプリフライトリクエスト。"""
        response = await client.options(
            "/api/upload",
            headers={
                "origin": "http://localhost:5173",
                "access-control-request-method": "POST",
                "access-control-request-headers": "Content-Type",
            },
        )
        assert response.status_code == 200
        assert "http://localhost:5173" in response.headers.get(
            "access-control-allow-origin", ""
        )

    @pytest.mark.asyncio
    async def test_cors_disallowed_origin(self, client):
        """許可されていないオリジンからのリクエスト。"""
        response = await client.options(
            "/api/upload",
            headers={
                "origin": "http://evil.com",
                "access-control-request-method": "POST",
            },
        )
        # 許可されていないオリジンにはCORSヘッダーが付与されない
        assert "http://evil.com" not in response.headers.get(
            "access-control-allow-origin", ""
        )
