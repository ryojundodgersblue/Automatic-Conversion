import { useRef, useState } from "react";
import "./ReportComplete.css";

/** PDFアップロードサイズ上限（10MB） */
const MAX_FILE_SIZE = 10 * 1024 * 1024;
/** アップロードタイムアウト（180秒 — Render Free プランのコールドスタート対応） */
const UPLOAD_TIMEOUT_MS = 180_000;

/**
 * エラーメッセージをHTTPステータスコードに応じて返す
 */
function getErrorMessage(status: number): string {
  switch (status) {
    case 400:
      return "PDFファイルのみアップロード可能です。ファイル形式を確認してください。";
    case 413:
      return "ファイルサイズが上限（10MB）を超えています。";
    case 500:
      return "サーバーでエラーが発生しました。しばらくしてから再試行してください。";
    default:
      return `予期しないエラーが発生しました（エラーコード: ${status}）`;
  }
}

function ReportComplete() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleClick = () => {
    // ファイル選択ダイアログを開く
    fileInputRef.current?.click();
  };

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // --- フロントエンド側サイズチェック（10MB制限） ---
    if (file.size > MAX_FILE_SIZE) {
      setErrorMessage("ファイルサイズが上限（10MB）を超えています。");
      setSelectedFile(null);
      // input をリセット
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    setSelectedFile(file);
    setErrorMessage(null);

    // バックエンドにファイルをアップロード
    await uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setErrorMessage(null);

    // --- タイムアウト設定（AbortController で60秒制限） ---
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT_MS);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        // レスポンスをBlobとして取得し、Excelをダウンロード
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");

        // ファイル名をレスポンスヘッダーから取得、なければデフォルト名
        const disposition = response.headers.get("content-disposition");
        let filename = "報告書.xlsx";
        if (disposition) {
          const match = disposition.match(/filename\*?=(?:UTF-8'')?([^;]+)/);
          if (match && match[1]) {
            filename = decodeURIComponent(match[1].replace(/"/g, ""));
          }
        }

        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        setErrorMessage(null);
      } else {
        // --- ステータスコード別エラーメッセージ ---
        const message = getErrorMessage(response.status);
        setErrorMessage(message);
        console.error("アップロード失敗:", response.status, message);
      }
    } catch (error) {
      clearTimeout(timeoutId);

      // --- エラー種別の判別 ---
      if (error instanceof DOMException && error.name === "AbortError") {
        // タイムアウト
        setErrorMessage(
          "アップロードがタイムアウトしました。ネットワーク接続を確認してください。",
        );
      } else if (error instanceof TypeError) {
        // ネットワークエラー（サーバー未起動等）
        setErrorMessage(
          "サーバーに接続できません。ネットワーク接続を確認してください。",
        );
      } else {
        // その他のエラー
        setErrorMessage(
          "ファイルのアップロード中に予期しないエラーが発生しました。",
        );
      }
      console.error("アップロードエラー:", error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="report-complete">
      <div className="card">
        <h1 className="title">事業年度終了報告書 自動変換システム</h1>
        <p className="subtitle">
          建設業の確定申告書 PDF を 事業年度終了報告書 Excel
          に自動で変換します。
        </p>

        <div className="info-tags">{/* 申告者名と申告年度のタグ */}</div>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf"
          style={{ display: "none" }}
        />

        <button
          className="select-btn"
          onClick={handleClick}
          disabled={isUploading}
        >
          {isUploading
            ? "変換中..."
            : selectedFile
              ? selectedFile.name
              : "PDFファイルを選択"}
        </button>

        {/* エラーメッセージ表示 */}
        {errorMessage && (
          <p className="error-message" role="alert">
            {errorMessage}
          </p>
        )}

        <p className="note">処理時間: 約1〜3分（初回アクセス時は時間がかかります） ｜ ファイルサイズ上限: 10MB</p>
      </div>
    </div>
  );
}

export default ReportComplete;
