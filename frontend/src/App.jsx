import { useState, useRef, useCallback, useEffect } from 'react'
import ScoreDisplay from './components/ScoreDisplay'
import RadarChart from './components/RadarChart'
import FactorBreakdown from './components/FactorBreakdown'
import TrendChart from './components/TrendChart'
import WhatIfSimulator from './components/WhatIfSimulator'
import TrustIntegrityCard from './components/TrustIntegrityCard'

const API_URL = 'http://127.0.0.1:8000'

export default function App() {
  const [state, setState] = useState('idle') // idle | loading | done | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [fileName, setFileName] = useState('')
  const [currentFile, setCurrentFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('general_service')
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
  }, [])

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
            <WhatIfSimulator file={currentFile} />
          </div>

          {/* Upload another */}
          <button className="btn-upload-another" onClick={reset} id="btn-upload-another">
            ↩ Upload Another CSV
          </button>
        </div>
      )}
    </div>
  )
}
