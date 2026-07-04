import { useState, useRef, useCallback, useEffect } from 'react'
import ScoreDisplay from './components/ScoreDisplay'
import RadarChart from './components/RadarChart'
import FactorBreakdown from './components/FactorBreakdown'
import TrendChart from './components/TrendChart'
import WhatIfSimulator from './components/WhatIfSimulator'
import TrustIntegrityCard from './components/TrustIntegrityCard'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default function App() {
  const [state, setState] = useState('idle') // idle | loading | done | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [fileName, setFileName] = useState('')
  const [currentFile, setCurrentFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('general_service')
  const [viewMode, setViewMode] = useState('merchant')
  const [selectedBank, setSelectedBank] = useState(null)
  const inputRef = useRef(null)

  useEffect(() => {
    fetch(`${API_URL}/categories`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setCategories(data)
        }
      })
      .catch((err) => console.error('Failed to fetch categories:', err))
  }, [])

  const uploadFile = useCallback(async (file) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Please upload a .csv file.')
      setState('error')
      return
    }
    setFileName(file.name)
    setCurrentFile(file)
    setState('loading')
    setError('')
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', selectedCategory)
      const res = await fetch(`${API_URL}/score`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Server returned ${res.status}`)
      }
      const data = await res.json()
      setResult(data)
      setState('done')
    } catch (err) {
      setError(err.message || 'Failed to connect to the scoring API.')
      setState('error')
    }
  }, [selectedCategory])

  const handleAAApprove = useCallback(async () => {
    setState('aa_loading')
    const fileMap = {
      'HDFC Bank': 'stable_kirana.csv',
      'ICICI Bank': 'growing_shop.csv',
      'State Bank of India': 'seasonal_vendor.csv',
      'Axis Bank': 'gaming_attempt.csv'
    };
    const mappedFile = fileMap[selectedBank] || 'stable_kirana.csv';
    setFileName(`${mappedFile} (via AA)`)
    setCurrentFile(null)
    try {
      const formData = new FormData()
      formData.append('category', selectedCategory)
      formData.append('bank', selectedBank)
      const res = await fetch(`${API_URL}/score_demo`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Server returned ${res.status}`)
      }
      const data = await res.json()
      setTimeout(() => {
        setResult(data)
        setState('done')
      }, 1500)
    } catch (err) {
      setError('Failed to simulate AA fetch: ' + err.message)
      setState('error')
    }
  }, [selectedCategory, selectedBank])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    uploadFile(file)
  }, [uploadFile, selectedCategory])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragOver(false)
  }, [])

  const handleFileChange = useCallback((e) => {
    const file = e.target.files?.[0]
    uploadFile(file)
  }, [uploadFile, selectedCategory])

  const reset = useCallback(() => {
    setState('idle')
    setResult(null)
    setError('')
    setFileName('')
    setCurrentFile(null)
    if (inputRef.current) inputRef.current.value = ''
  }, [])

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header__logo">
          <div className="header__icon">📊</div>
          <h1 className="header__title">VyapaarScore</h1>
        </div>
        <p className="header__subtitle">
          Upload UPI transaction data. Get an instant, explainable merchant trust score.
        </p>
      </header>

      {/* Error banner */}
      {state === 'error' && (
        <div className="error-banner" id="error-banner">
          ⚠️ {error}
          <button
            className="btn-upload-another"
            onClick={reset}
            style={{ marginLeft: '1rem', marginTop: 0 }}
          >
            Try Again
          </button>
        </div>
      )}

      {/* Upload state */}
      {(state === 'idle' || state === 'error') && (
        <div className="upload-grid">
          <div className="card" id="upload-card">
            <div style={{ marginBottom: 'var(--space-md)' }}>
              <label htmlFor="category-select" style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 'bold' }}>
                Business Category
              </label>
              <select
                id="category-select"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                style={{
                  width: '100%',
                  padding: 'var(--space-sm)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-card)',
                  color: 'var(--text-primary)',
                  fontSize: '1rem',
                  outline: 'none',
                }}
              >
                {categories.map((cat) => (
                  <option key={cat.key} value={cat.key}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>
            <div
              className={`upload-zone ${dragOver ? 'upload-zone--dragover' : ''}`}
              onClick={() => inputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              id="upload-zone"
            >
              <span className="upload-zone__icon">📁</span>
              <p className="upload-zone__text">
                Drop your merchant CSV here, or click to browse
              </p>
              <p className="upload-zone__hint">
                Expects columns: transaction_id, timestamp, amount, type, status, payer_vpa, payee_vpa
              </p>
              <input
                ref={inputRef}
                type="file"
                accept=".csv"
                className="upload-zone__input"
                onChange={handleFileChange}
                id="csv-file-input"
              />
            </div>
          </div>

          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', cursor: 'pointer', transition: 'all var(--transition-base)', minHeight: '300px' }} onClick={() => setState('aa_intro')} onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--accent-indigo)'; e.currentTarget.style.boxShadow = 'var(--shadow-glow-indigo)' }} onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-subtle)'; e.currentTarget.style.boxShadow = 'var(--shadow-card)' }}>
            <div style={{ fontSize: '3.5rem', marginBottom: 'var(--space-md)' }}>🔗</div>
            <h3 style={{ fontSize: '1.4rem', color: 'var(--text-primary)', marginBottom: 'var(--space-sm)' }}>Connect via Account Aggregator</h3>
            <p style={{ color: 'var(--text-muted)' }}>Securely link your bank account to fetch transaction history directly.</p>
          </div>
        </div>
      )}

      {/* AA Intro */}
      {state === 'aa_intro' && (
        <div className="card" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
          <div style={{ display: 'inline-block', background: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-indigo)', padding: '6px 16px', borderRadius: '20px', fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '1.5rem', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
            Simulated flow — for demonstration
          </div>
          <h2 style={{ marginBottom: '1rem', color: 'var(--text-primary)', fontSize: '1.8rem' }}>Account Aggregator Framework</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '1.1rem', lineHeight: '1.6' }}>
            This simulates the RBI's Account Aggregator (AA) framework, which allows secure, user-consented data sharing between financial institutions.
          </p>
          <div className="aa-buttons">
            <button className="btn-upload-another" style={{ margin: 0 }} onClick={() => setState('idle')}>Cancel</button>
            <button className="btn-upload-another" style={{ background: 'var(--accent-indigo)', color: 'white', border: 'none', margin: 0 }} onClick={() => setState('aa_bank')}>
              Proceed to Bank Selection ➔
            </button>
          </div>
        </div>
      )}

      {/* AA Bank Selection */}
      {state === 'aa_bank' && (
        <div className="card" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>Select Your Bank</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            Choose the bank where you hold your primary business account.
          </p>
          <div className="bank-grid">
            {['HDFC Bank', 'ICICI Bank', 'State Bank of India', 'Axis Bank'].map(bank => (
              <div
                key={bank}
                onClick={() => { setSelectedBank(bank); setState('aa_consent'); }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-glass-strong)'; e.currentTarget.style.borderColor = 'var(--accent-indigo)' }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--bg-glass)'; e.currentTarget.style.borderColor = 'var(--border-subtle)' }}
                style={{
                  padding: '1.5rem',
                  background: 'var(--bg-glass)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  color: 'var(--text-primary)',
                  transition: 'all var(--transition-base)'
                }}
              >
                {bank}
              </div>
            ))}
          </div>
          <button className="btn-upload-another" style={{ margin: 0 }} onClick={() => setState('idle')}>Cancel</button>
        </div>
      )}

      {/* AA Consent Artifact */}
      {state === 'aa_consent' && (
        <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
          <h2 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)', textAlign: 'center' }}>Consent Request</h2>
          <div style={{ background: 'var(--bg-glass)', padding: '1.5rem', borderRadius: 'var(--radius-md)', marginBottom: '2rem' }}>
            <div className="consent-row">
              <span style={{ color: 'var(--text-muted)' }}>Financial Information User (FIU):</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>VyapaarScore</span>
            </div>
            <div className="consent-row">
              <span style={{ color: 'var(--text-muted)' }}>Financial Information Provider (FIP):</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>{selectedBank}</span>
            </div>
            <div className="consent-row">
              <span style={{ color: 'var(--text-muted)' }}>Data Requested:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>UPI Transaction History</span>
            </div>
            <div className="consent-row">
              <span style={{ color: 'var(--text-muted)' }}>Purpose:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>Credit scoring for loan eligibility</span>
            </div>
            <div className="consent-row">
              <span style={{ color: 'var(--text-muted)' }}>Data Range:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>Last 6 months</span>
            </div>
            <div className="consent-row">
              <span style={{ color: 'var(--text-muted)' }}>Consent Validity:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>30 days</span>
            </div>
            <div className="consent-row" style={{ borderBottom: 'none', marginBottom: 0, paddingBottom: 0 }}>
              <span style={{ color: 'var(--text-muted)' }}>Frequency:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>One-time pull</span>
            </div>
          </div>
          <div className="aa-buttons">
            <button className="btn-upload-another" style={{ margin: 0 }} onClick={() => setState('idle')}>Deny</button>
            <button className="btn-upload-another" style={{ background: 'var(--accent-emerald)', color: '#0a0e1a', border: 'none', margin: 0, fontWeight: 'bold' }} onClick={handleAAApprove}>Approve & Share Data</button>
          </div>
        </div>
      )}

      {/* AA Loading */}
      {state === 'aa_loading' && (
        <div className="card">
          <div className="analyzing">
            <div className="analyzing__spinner" style={{ borderTopColor: 'var(--accent-emerald)' }} />
            <p className="analyzing__text">
              Fetching transaction data via <strong>{selectedBank}</strong> Account Aggregator…
            </p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {state === 'loading' && (
        <div className="card">
          <div className="analyzing">
            <div className="analyzing__spinner" />
            <p className="analyzing__text">
              Analyzing <strong>{fileName}</strong>…
            </p>
          </div>
        </div>
      )}

      {/* Results dashboard */}
      {state === 'done' && result && (
        <div className="dashboard" id="dashboard">
          <div className="view-toggle no-print" style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', justifyContent: 'center' }}>
            <button className={`btn-toggle ${viewMode === 'merchant' ? 'active' : ''}`} onClick={() => setViewMode('merchant')}>Merchant View</button>
            <button className={`btn-toggle ${viewMode === 'lender' ? 'active' : ''}`} onClick={() => setViewMode('lender')}>Lender View</button>
          </div>

          {viewMode === 'merchant' ? (
            <>
              {/* Top row: Score + Radar */}
              <div className="dashboard__top">
                <div className="card score-display" id="score-card">
                  <ScoreDisplay
                    score={result.score}
                    grade={result.grade}
                    totalTransactions={result.total_transactions}
                    fileName={fileName}
                  />
                </div>
                <div className="card radar-card" id="radar-card">
                  <div className="card__title">Factor Radar</div>
                  <RadarChart factors={result.factors_normalized_0_1} />
                </div>
              </div>

              {/* Peer Benchmark */}
              {result.benchmark && (
                <div className="dashboard__bottom">
                  <div className="card" id="benchmark-card">
                    <div className="card__title">Peer Benchmark</div>
                    <div style={{ padding: 'var(--space-md)', background: 'rgba(59, 130, 246, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(59, 130, 246, 0.25)' }}>
                      <div style={{ fontSize: '1.2rem', fontWeight: 'bold', marginBottom: 'var(--space-sm)', color: 'var(--text-primary)' }}>
                        🏆 {result.benchmark.message}
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-lg)', color: 'var(--text-secondary)' }}>
                        <span><strong>Category:</strong> {result.benchmark.category_label}</span>
                        <span><strong>Peer Median:</strong> {result.benchmark.peer_median}</span>
                        <span><strong>Peer Mean:</strong> {result.benchmark.peer_mean}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Trust & Integrity Check */}
              {result.integrity && (
                <div className="dashboard__bottom">
                  <TrustIntegrityCard integrity={result.integrity} />
                </div>
              )}

              {/* Trend Chart */}
              {result.trend && (
                <div className="dashboard__bottom">
                  <div className="card" id="trend-card">
                    <div className="card__title">Score Trend</div>
                    <TrendChart trend={result.trend} />
                  </div>
                </div>
              )}

              {/* Bottom: Factor breakdown */}
              <div className="dashboard__bottom">
                <div className="card" id="factors-card">
                  <div className="card__title">Factor Breakdown</div>
                  <FactorBreakdown
                    factors={result.factors_normalized_0_1}
                    details={result.factor_details}
                  />
                </div>
              </div>

              {/* Bottom: Improve your score */}
              <div className="dashboard__bottom">
                <div className="card" id="tips-card">
                  <div className="card__title">Improve your score</div>
                  {result.strength && (
                    <div style={{ color: 'var(--grade-a)', marginBottom: 'var(--space-md)', padding: 'var(--space-md)', background: 'rgba(52, 211, 153, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(52, 211, 153, 0.25)' }}>
                      ✨ <strong>Strength:</strong> {result.strength.message}
                    </div>
                  )}
                  {result.tips && result.tips.length > 0 ? (
                    <div style={{ display: 'grid', gap: 'var(--space-md)' }}>
                      {result.tips.map((tip, idx) => (
                        <div key={idx} className="factor-item" style={{ padding: 'var(--space-lg)', animationDelay: `${idx * 0.1}s` }}>
                          <div className="factor-item__name" style={{ marginBottom: 'var(--space-sm)' }}>
                            Target: {tip.label} (Current Score: {(tip.score * 100).toFixed(0)}%)
                          </div>
                          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>
                            {tip.tip}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ color: 'var(--text-muted)', padding: 'var(--space-md)', textAlign: 'center' }}>
                      No major weak points detected — all factors above threshold!
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom: What-If Simulator */}
              <div className="dashboard__bottom">
                <WhatIfSimulator file={currentFile} demoBank={!currentFile ? selectedBank : null} />
              </div>
            </>
          ) : result.lender_recommendation ? (
            <div className="lender-report card">
              <div className="lender-header">
                <div>
                  <h2 style={{ margin: 0, fontSize: '1.5rem', color: 'var(--text-primary)' }}>Lender Recommendation Report</h2>
                  <div style={{ color: 'var(--text-secondary)' }}>File: {fileName}</div>
                </div>
                <button className="btn-upload-another no-print" onClick={() => window.print()} style={{ margin: 0 }}>🖨️ Print / Save PDF</button>
              </div>

              <div className="lender-summary">
                <div style={{ flex: '1 1 auto', minWidth: '250px' }}>
                  <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)', margin: '0 0 0.5rem 0' }}>Automated Decision</h3>
                  <div className="badge-print-color" style={{
                    padding: '1rem',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '1.25rem',
                    textAlign: 'center',
                    background: `var(--grade-${result.lender_recommendation.tone === 'success' ? 'a' : result.lender_recommendation.tone === 'warning' ? 'c' : 'd'}-bg, ${result.lender_recommendation.tone === 'success' ? 'rgba(52, 211, 153, 0.2)' : result.lender_recommendation.tone === 'warning' ? 'rgba(251, 191, 36, 0.2)' : 'rgba(239, 68, 68, 0.2)'})`,
                    color: `var(--grade-${result.lender_recommendation.tone === 'success' ? 'a' : result.lender_recommendation.tone === 'warning' ? 'c' : 'd'}, ${result.lender_recommendation.tone === 'success' ? '#10b981' : result.lender_recommendation.tone === 'warning' ? '#f59e0b' : '#ef4444'})`,
                    border: `2px solid currentColor`
                  }}>
                    {result.lender_recommendation.label}
                  </div>
                </div>
                <div style={{ flex: '1 1 auto', minWidth: '250px' }}>
                  <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)', margin: '0 0 0.5rem 0' }}>Max Recommended Amount</h3>
                  <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                    ₹{result.lender_recommendation.max_recommended_amount.toLocaleString('en-IN')}
                  </div>
                  <div style={{ color: 'var(--text-muted)' }}>{result.lender_recommendation.tier_label}</div>
                </div>
              </div>

              <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>Reasoning</h3>
                <ul style={{ paddingLeft: '1.5rem', margin: 0, color: 'var(--text-secondary)', fontSize: '1.1rem', lineHeight: 1.6 }}>
                  {result.lender_recommendation.reasoning.map((r, i) => <li key={i} style={{ marginBottom: '0.5rem' }}>{r}</li>)}
                </ul>
              </div>

              {result.lender_recommendation.conditions && result.lender_recommendation.conditions.length > 0 && (
                <div className="badge-print-color" style={{ background: 'rgba(251, 191, 36, 0.1)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                  <h3 style={{ fontSize: '1.2rem', color: '#b45309', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    ⚠️ Conditions for Approval
                  </h3>
                  <ul style={{ paddingLeft: '1.5rem', margin: 0, color: 'var(--text-secondary)' }}>
                    {result.lender_recommendation.conditions.map((c, i) => <li key={i} style={{ marginBottom: '0.5rem' }}>{c}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ) : null}

          {/* Upload another */}
          <button className="btn-upload-another no-print" onClick={reset} id="btn-upload-another">
            ↩ Upload Another CSV
          </button>
        </div>
      )}
    </div>
  )
}
