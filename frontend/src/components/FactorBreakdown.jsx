const FACTOR_META = {
  consistency: {
    label: 'Consistency',
    icon: '📈',
    description: 'Regularity of daily inflow — lower volatility means predictable repayment capacity.',
    detailFormat: (d) =>
      d.note
        ? d.note
        : `CV: ${d.coefficient_of_variation} · Active days: ${(d.active_days_ratio * 100).toFixed(0)}%`,
  },
  growth: {
    label: 'Growth',
    icon: '🚀',
    description: 'Month-over-month inflow trend — business trajectory, not just a snapshot.',
    detailFormat: (d) =>
      d.note ? d.note : `Avg MoM growth: ${d.avg_month_over_month_growth_pct}%`,
  },
  liquidity_buffer: {
    label: 'Liquidity Buffer',
    icon: '🛡️',
    description: 'Survival days from retained cash — classic working-capital health signal.',
    detailFormat: (d) =>
      d.note
        ? d.note
        : `Buffer: ${d.estimated_buffer_days} days · Net retained: ₹${d.net_retained_amount.toLocaleString()}`,
  },
  payer_diversity: {
    label: 'Payer Diversity',
    icon: '👥',
    description: 'Unique + repeat customers — thin/one-off customer base = concentration risk.',
    detailFormat: (d) =>
      d.note
        ? d.note
        : `${d.unique_payers} unique payers · ${(d.repeat_customer_ratio * 100).toFixed(0)}% repeat`,
  },
  reliability: {
    label: 'Reliability',
    icon: '✅',
    description: 'Inverse of failed/bounced transactions — proxy for operational reliability.',
    detailFormat: (d) =>
      d.note ? d.note : `Failure rate: ${d.failure_rate_pct}%`,
  },
  longevity: {
    label: 'Longevity',
    icon: '📅',
    description: 'Span of transaction history — more data = higher confidence.',
    detailFormat: (d) =>
      d.note ? d.note : `${d.history_span_days} days of history`,
  },
}

const FACTOR_ORDER = [
  'consistency',
  'growth',
  'liquidity_buffer',
  'payer_diversity',
  'reliability',
  'longevity',
]

export default function FactorBreakdown({ factors, details }) {
  return (
    <div className="factors">
      {FACTOR_ORDER.map((key) => {
        const meta = FACTOR_META[key]
        const score = factors[key]
        const detail = details[key]
        const pct = (score * 100).toFixed(0)

        return (
          <div className="factor-item" key={key} id={`factor-${key}`}>
            <div className="factor-item__header">
              <span className="factor-item__name">
                {meta.icon} {meta.label}
              </span>
              <span className="factor-item__score">{pct}%</span>
            </div>
            <div className="factor-item__bar-bg">
              <div
                className="factor-item__bar-fill"
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="factor-item__detail">
              {meta.detailFormat(detail)}
            </div>
          </div>
        )
      })}
    </div>
  )
}
