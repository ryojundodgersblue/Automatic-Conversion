import './ReportComplete.css'

function ReportComplete() {
  return (
    <div className="report-complete">
      <div className="card">
        <h1 className="title">事業年度終了報告書 自動変換システム</h1>
        <p className="subtitle">建設業の確定申告書 PDF を 事業年度終了報告書 Excel に自動で変換します。</p>

        <div className="info-tags">
          {/* 申告者名と申告年度のタグ */}
        </div>

        <button className="select-btn">
          ファイルを選択
        </button>

        <p className="note">処理時間: 約10〜30秒</p>

      </div>
    </div>
  )
}

export default ReportComplete
