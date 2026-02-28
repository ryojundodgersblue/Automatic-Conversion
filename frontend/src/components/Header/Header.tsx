import './Header.css'
import logo from '@/assets/system-logo.png';

function Header() {
  return (
    <header className="header">
      <div className="header-left">                  
          <img src={logo} alt="systemLogo" className="header-logo" />
          <h1>自動変換クン</h1>      
      </div>
      <nav className="header-nav">
        {/* メニューリンク（背債、投屏、投屏、ヘルプ）をここに */}
      </nav>
    </header>
  )
}

export default Header
