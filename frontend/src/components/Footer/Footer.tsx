import './Footer.css'
import logo from '@/assets/ryojun-logo.png';

function Footer() {
  return (
    <footer className="footer">
      <p className="footer-copyright">© 2026 良純</p>
      <div className="footer-links">
        {/* プライバシーポリシー、利用規約などのリンク */}
      </div>
      <img src={logo} alt="ryojunLogo" className="footer-logo" />
    </footer>
  )
}

export default Footer
