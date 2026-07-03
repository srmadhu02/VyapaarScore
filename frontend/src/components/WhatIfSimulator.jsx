import { useState, useEffect, useRef } from 'react'

const API_URL = 'http://127.0.0.1:8000'

const CIRCUMFERENCE = 2 * Math.PI * 88 // radius = 88

function gradeLabel(grade) {
  const labels = {
    A: 'Excellent',
    B: 'Good',
    C: 'Fair',
    D: 'Poor',
  }
  return labels[grade] || grade
}

export default function WhatIfSimulator({ file, demoBank }) {
  const [params, setParams] = useState({
    inflowGrowth: 0,
    newRepeatCustomers: 0,
    reduceFailures: 0,
    reduceOutflows: 0,
  })
  
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Ref to hold the latest timeout for debounce
  const timerRef = useRef(null)

  // Track if we need to fetch initial baseline
  const isFirstRun = useRef(true)

  const fetchSimulation = async (currentParams) => {
    if (!file && !demoBank) return

    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      if (file) {
        formData.append('file', file)
      } else {
        formData.append('bank', demoBank)
      }
      formData.append('inflow_growth_pct', currentParams.inflowGrowth)
      formData.append('new_repeat_customers', currentParams.newRepeatCustomers)
      formData.append('reduce_failures_pct', currentParams.reduceFailures)
      formData.append('reduce_outflows_pct', currentParams.reduceOutflows)

      const endpoint = file ? `${API_URL}/simulate` : `${API_URL}/simulate_demo`

      const res = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Server returned ${res.status}`)
      }

      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Failed to connect to the scoring API.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isFirstRun.current) {
      isFirstRun.current = false
      fetchSimulation(params)
      return
    }

    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    timerRef.current = setTimeout(() => {
      fetchSimulation(params)
    }, 400)

    return () => clearTimeout(timerRef.current)
  }, [params, file, demoBank])

  const handleChange = (key, val) => {
    setParams(prev => ({ ...prev, [key]: Number(val) }))
  }

  return (
    <div className="card what-if-card">
      <div className="card__title">What-If Simulator</div>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-xl)' }}>
        See how realistic business improvements could impact your score.
      </p>

      <div className="simulator-layout">
        <div className="simulator-controls">
          <div className="slider-group">
            <div className="slider-header">
              <label>Monthly inflow growth</label>
              <span>{params.inflowGrowth}%</span>
            </div>
            <input 
              type="range" 
              min="0" 
              max="30" 
              value={params.inflowGrowth} 
              onChange={(e) => handleChange('inflowGrowth', e.target.value)} 
              className="styled-slider"
            />
          </div>

          <div className="slider-group">
            <div className="slider-header">
              <label>New repeat customers</label>
              <span>{params.newRepeatCustomers}</span>
            </div>
            <input 
              type="range" 
              min="0" 
              max="25" 
              value={params.newRepeatCustomers} 
              onChange={(e) => handleChange('newRepeatCustomers', e.target.value)} 
              className="styled-slider"
            />
          </div>

          <div className="slider-group">
            <div className="slider-header">
              <label>Fix failed transactions</label>
              <span>{params.reduceFailures}%</span>
            </div>
            <input 
              type="range" 
              min="0" 
              max="100" 
              value={params.reduceFailures} 
              onChange={(e) => handleChange('reduceFailures', e.target.value)} 
              className="styled-slider"
            />
          </div>

          <div className="slider-group">
            <div className="slider-header">
              <label>Reduce large outflows</label>
              <span>{params.reduceOutflows}%</span>
            </div>
            <input 
              type="range" 
              min="0" 
              max="40" 
              value={params.reduceOutflows} 
              onChange={(e) => handleChange('reduceOutflows', e.target.value)} 
              className="styled-slider"
            />
          </div>
        </div>

        <div className="simulator-result">
          {error && <div className="error-text">⚠️ {error}</div>}
          {result && (
            <div className="sim-score-display">
              <div className="score-ring">
                <svg className="score-ring__svg" viewBox="0 0 200 200">
                  <circle className="score-ring__bg" cx="100" cy="100" r="88" />
                  <circle
                    className={`score-ring__fill score-ring__fill--${result.simulated.grade.toLowerCase()}`}
                    cx="100"
                    cy="100"
                    r="88"
                    strokeDasharray={CIRCUMFERENCE}
                    strokeDashoffset={CIRCUMFERENCE * (1 - result.simulated.score / 100)}
                    style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
                  />
                </svg>
                <div className="score-ring__value">
                  <span className="score-ring__number">{result.simulated.score.toFixed(1)}</span>
                  <span className="score-ring__label">out of 100</span>
                </div>
              </div>

              <div className={`grade-badge grade-badge--${result.simulated.grade.toLowerCase()}`}>
                Grade {result.simulated.grade} — {gradeLabel(result.simulated.grade)}
              </div>

              <div className={`sim-delta ${result.score_delta > 0 ? 'delta-positive' : result.score_delta < 0 ? 'delta-negative' : 'delta-neutral'}`}>
                {result.score_delta > 0 ? '+' : ''}{result.score_delta.toFixed(1)} from baseline
              </div>
            </div>
          )}
          {loading && !result && (
            <div className="sim-loading">Calculating...</div>
          )}
        </div>
      </div>
    </div>
  )
}
