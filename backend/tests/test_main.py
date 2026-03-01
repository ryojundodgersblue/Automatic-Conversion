"""FastAPI メインサーバー (main.py) の API + セキュリティテスト。

テスト対象:
- ファイルアップロードエンドポイント（正常系・異常系）
- ファイルサイズ制限（413エラー）
- ファイル形式バリデーション（400エラー）
- PDFマジックバイト検証（content-type偽装防止）
- secure_filename（パストラバーサル防止）
- セキュリティヘッダーの確認
- CORS設定の確認
- グローバル例外ハンドラ
- ヘルスチェックエンドポイント
- ダウンロードエンドポイント（正常系・異常系・UUID検証）
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from httpx import ASGITransport, AsyncClient
from main import _download_store, app, secure_filename


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


# =============================================
# ヘルスチェックテスト
# =============================================
class TestHealthCheck:
    """ヘルスチェックエンドポイントのテスト。"""

    @pytest.fixture
    def client(self):
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_health_check_returns_ok(self, client):
        """GET / は status: ok を返す。"""
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# =============================================
# PDFマジックバイト検証テスト
# =============================================
class TestPDFMagicByteValidation:
    """content-type偽装防止のためのマジックバイトチェックテスト。"""

    @pytest.fixture
    def client(self):
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_reject_fake_pdf_content_type(self, client):
        """content-typeがPDFだが中身がPDFでないファイルは400エラー。"""
        fake_pdf = b"This is not a PDF file"
        response = await client.post(
            "/api/upload",
            files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
        )
        assert response.status_code == 400
        assert "PDF" in response.json().get("error", "")

    @pytest.mark.asyncio
    async def test_accept_valid_pdf_magic_bytes(self, client):
        """正しいPDFマジックバイトを持つファイルはバリデーション通過。"""
        valid_pdf = b"%PDF-1.4 dummy content"
        response = await client.post(
            "/api/upload",
            files={"file": ("test.pdf", valid_pdf, "application/pdf")},
        )
        # マジックバイトチェックは通過（後続のPDF解析でエラーになる可能性あり）
        assert response.status_code != 400


# =============================================
# ダウンロードエンドポイントテスト
# =============================================
class TestDownloadEndpoint:
    """ダウンロードAPIの正常系・異常系テスト。"""

    @pytest.fixture
    def client(self):
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_download_invalid_uuid_format(self, client):
        """UUID形式でないdownload_idは400エラー。"""
        response = await client.get("/api/download/not-a-uuid")
        assert response.status_code == 400
        assert "無効" in response.json().get("error", "")

    @pytest.mark.asyncio
    async def test_download_nonexistent_id(self, client):
        """存在しないdownload_idは404エラー。"""
        import uuid

        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/download/{fake_id}")
        assert response.status_code == 404
        assert "見つかりません" in response.json().get("error", "")

    @pytest.mark.asyncio
    async def test_download_valid_file(self, client, tmp_path):
        """正常なダウンロード: 登録済みファイルをダウンロードできる。"""
        import time
        import uuid

        # テスト用の一時ファイルを作成
        test_file = tmp_path / "test_output.xlsx"
        test_file.write_bytes(b"dummy excel content")

        # ダウンロードストアに登録
        download_id = str(uuid.uuid4())
        _download_store[download_id] = {
            "path": str(test_file),
            "filename": "テスト_報告書.xlsx",
            "created": time.time(),
        }

        try:
            response = await client.get(f"/api/download/{download_id}")
            assert response.status_code == 200
            assert "attachment" in response.headers.get("content-disposition", "")
        finally:
            # テスト後にクリーンアップ
            _download_store.pop(download_id, None)

    @pytest.mark.asyncio
    async def test_download_with_dummy_filename(self, client, tmp_path):
        """ダミーファイル名付きURLでもダウンロードできる（Chrome対策）。"""
        import time
        import uuid

        test_file = tmp_path / "test_output.xlsx"
        test_file.write_bytes(b"dummy excel content")

        download_id = str(uuid.uuid4())
        _download_store[download_id] = {
            "path": str(test_file),
            "filename": "テスト_報告書.xlsx",
            "created": time.time(),
        }

        try:
            response = await client.get(
                f"/api/download/{download_id}/テスト_報告書.xlsx"
            )
            assert response.status_code == 200
        finally:
            _download_store.pop(download_id, None)

    @pytest.mark.asyncio
    async def test_download_path_traversal_in_id(self, client):
        """download_idにパストラバーサルを試行しても400エラー。"""
        response = await client.get("/api/download/../../../etc/passwd")
        assert response.status_code == 400
