import { useRef, useState } from 'react'
import './ReportComplete.css'

function ReportComplete() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  const handleClick = () => {
    // ファイル選択ダイアログを開く
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setSelectedFile(file)

    // バックエンドにファイルをアップロード
    await uploadFile(file)
  }

  const uploadFile = async (file: File) => {
    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        // レスポンスをBlobとして取得し、Excelをダウンロード
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')

        // ファイル名をレスポンスヘッダーから取得、なければデフォルト名
        const disposition = response.headers.get('content-disposition')
        let filename = '報告書.xlsx'
        if (disposition) {
          const match = disposition.match(/filename\*?=(?:UTF-8'')?([^;]+)/)
          if (match) {
            filename = decodeURIComponent(match[1].replace(/"/g, ''))
          }
        }

        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      } else {
        const error = await response.json()
        console.error('アップロード失敗:', error)
        alert('ファイルのアップロードに失敗しました')
      }
    } catch (error) {
      console.error('アップロードエラー:', error)
      alert('ファイルのアップロード中にエラーが発生しました')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="report-complete">
      <div className="card">
        <h1 className="title">事業年度終了報告書 自動変換システム</h1>
        <p className="subtitle">建設業の確定申告書 PDF を 事業年度終了報告書 Excel に自動で変換します。</p>

        <div className="info-tags">
          {/* 申告者名と申告年度のタグ */}
        </div>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf"
          style={{ display: 'none' }}
        />

        <button
          className="select-btn"
          onClick={handleClick}
          disabled={isUploading}
        >
          {isUploading ? '変換中...' : selectedFile ? selectedFile.name : 'PDFファイルを選択'}
        </button>

        <p className="note">処理時間: 約10〜30秒</p>

      </div>
    </div>
  )
}

export default ReportComplete
