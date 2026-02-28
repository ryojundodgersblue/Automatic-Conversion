"""FastAPI サーバー — PDF → Excel 変換 API を提供する。

フロントエンドから PDF をアップロードすると、解析して
指定テンプレートに転記した Excel をダウンロードさせる。
"""

import os
import shutil

from excel_writer import write_to_excel
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pdf_parser import parse_pdf

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
# 都道府県別テンプレート（将来的に選択可能にする）
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "aichi.xlsx")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """PDF を受け取り、Excel に変換してダウンロードさせる。"""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="PDFファイルのみアップロード可能です"
        )

    # PDF を一時保存
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # PDF 解析
        bs_data, pl_data, cr_data = parse_pdf(file_path)

        # Excel 生成
        output_path = write_to_excel(TEMPLATE_PATH, bs_data, pl_data, cr_data)

        # ダウンロードファイル名（元の PDF 名をベースにする）
        base_name = os.path.splitext(file.filename)[0]
        download_name = f"{base_name}_報告書.xlsx"

        return FileResponse(
            path=output_path,
            filename=download_name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    finally:
        # アップロードされた PDF を削除
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
