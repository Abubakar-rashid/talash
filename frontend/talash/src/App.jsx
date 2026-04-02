import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'
import CVUpload from './components/CVUpload'
import CandidateDashboard from './components/CandidateDashboard'

function App() {
  const [activeTab, setActiveTab] = useState('upload')

  return (
    <>
      <section id="center" style={{ paddingTop: '20px' }}>
        <div className="hero">
          <img src={heroImg} className="base" width="170" height="179" alt="" />
          <img src={reactLogo} className="framework" alt="React logo" />
          <img src={viteLogo} className="vite" alt="Vite logo" />
        </div>
        <div>
          <h1>Talash Dashboard</h1>
          <p>Smart HR Recruitment System</p>
        </div>
        
        {/* Simple navigation tabs */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
          <button 
            onClick={() => setActiveTab('upload')}
            style={{ 
              padding: '10px 20px', 
              background: activeTab === 'upload' ? 'var(--accent)' : 'var(--code-bg)',
              color: activeTab === 'upload' ? 'white' : 'var(--text-h)',
              border: activeTab === 'upload' ? '2px solid var(--accent)' : '2px solid transparent',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Upload New CV
          </button>
          <button 
            onClick={() => setActiveTab('dashboard')}
            style={{ 
              padding: '10px 20px', 
              background: activeTab === 'dashboard' ? 'var(--accent)' : 'var(--code-bg)',
              color: activeTab === 'dashboard' ? 'white' : 'var(--text-h)',
              border: activeTab === 'dashboard' ? '2px solid var(--accent)' : '2px solid transparent',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            View Parsed CVs
          </button>
        </div>

        {activeTab === 'upload' ? <CVUpload /> : <CandidateDashboard />}
        
      </section>

      <div className="ticks"></div>

      <section id="next-steps">
        <div id="docs">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#documentation-icon"></use>
          </svg>
          <h2>Documentation</h2>
          <p>Your questions, answered</p>
          <ul>
            <li>
              <a href="https://vite.dev/" target="_blank">
                <img className="logo" src={viteLogo} alt="" />
                Explore Vite
              </a>
            </li>
            <li>
              <a href="https://react.dev/" target="_blank">
                <img className="button-icon" src={reactLogo} alt="" />
                Learn more
              </a>
            </li>
          </ul>
        </div>
        <div id="social">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#social-icon"></use>
          </svg>
          <h2>Connect with us</h2>
          <p>Join the Vite community</p>
          <ul>
            <li>
              <a href="https://github.com/vitejs/vite" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#github-icon"></use>
                </svg>
                GitHub
              </a>
            </li>
            <li>
              <a href="https://chat.vite.dev/" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#discord-icon"></use>
                </svg>
                Discord
              </a>
            </li>
            <li>
              <a href="https://x.com/vite_js" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#x-icon"></use>
                </svg>
                X.com
              </a>
            </li>
            <li>
              <a href="https://bsky.app/profile/vite.dev" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#bluesky-icon"></use>
                </svg>
                Bluesky
              </a>
            </li>
          </ul>
        </div>
      </section>

      <div className="ticks"></div>
      <section id="spacer"></section>
    </>
  )
}

export default App
