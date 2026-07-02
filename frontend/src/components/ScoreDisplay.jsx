import { useEffect, useState } from 'react'

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

export default function ScoreDisplay({ score, grade, totalTransactions, fileName }) {
  const [animatedScore, setAnimatedScore] = useState(0)

  useEffect(() => {
    let frame
    const start = performance.now()
    const duration = 1200

    function animate(now) {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setAnimatedScore(Math.round(eased * score * 10) / 10)
      if (progress < 1) {
        frame = requestAnimationFrame(animate)
      }
    }

    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [score])

  const dashOffset = CIRCUMFERENCE * (1 - score / 100)
  const g = grade.toLowerCase()

  return (
    <>
      <div className="score-ring">
        <svg className="score-ring__svg" viewBox="0 0 200 200">
          <circle className="score-ring__bg" cx="100" cy="100" r="88" />
          <circle
            className={`score-ring__fill score-ring__fill--${g}`}
            cx="100"
            cy="100"
            r="88"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={dashOffset}
          />
        </svg>
        <div className="score-ring__value">
          <span className="score-ring__number">{animatedScore}</span>
          <span className="score-ring__label">out of 100</span>
        </div>
      </div>

      <div className={`grade-badge grade-badge--${g}`}>
        Grade {grade} — {gradeLabel(grade)}
      </div>

      <div className="score-txn-count">
        <span>{totalTransactions.toLocaleString()}</span> transactions analyzed
        {fileName && <> from <span>{fileName}</span></>}
      </div>
    </>
  )
}
