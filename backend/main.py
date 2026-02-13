import os
import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pdf_parser import parse_pdf

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="PDFファイルのみアップロード可能です"
        )
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # PDF読み取り・変換処理を追加
    bs_result, pl_result, cr_result = parse_pdf(file_path)
    print(bs_result)
    print(pl_result)
    print(cr_result)

    return {
        "filename": file.filename,
        "message": "アップロード成功",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
