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
    console.log('選択されたファイル:', file.name)

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
        const result = await response.json()
        console.log('アップロード成功:', result)
        // 成功時の処理（例：結果ページへの遷移など）
      } else {
        console.error('アップロード失敗:', response.statusText)
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
          {isUploading ? 'アップロード中...' : selectedFile ? selectedFile.name : 'ファイルを選択'}
        </button>

        <p className="note">処理時間: 約10〜30秒</p>

      </div>
    </div>
  )
}

export default ReportComplete
