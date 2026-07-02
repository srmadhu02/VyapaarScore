import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from 'chart.js'
import { Radar } from 'react-chartjs-2'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip)

const FACTOR_LABELS = {
  consistency: 'Consistency',
  growth: 'Growth',
  liquidity_buffer: 'Liquidity',
  payer_diversity: 'Diversity',
  reliability: 'Reliability',
  longevity: 'Longevity',
}

const FACTOR_ORDER = [
  'consistency',
  'growth',
  'liquidity_buffer',
  'payer_diversity',
  'reliability',
  'longevity',
]

export default function RadarChart({ factors }) {
  const labels = FACTOR_ORDER.map((k) => FACTOR_LABELS[k])
  const values = FACTOR_ORDER.map((k) => factors[k])

  const data = {
    labels,
    datasets: [
      {
        label: 'Factor Score',
        data: values,
        backgroundColor: 'rgba(129, 140, 248, 0.15)',
        borderColor: 'rgba(129, 140, 248, 0.8)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(129, 140, 248, 1)',
        pointBorderColor: '#1e1b4b',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        fill: true,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        beginAtZero: true,
        min: 0,
        max: 1,
        ticks: {
          stepSize: 0.25,
          color: 'rgba(148, 163, 184, 0.5)',
          backdropColor: 'transparent',
          font: { size: 10 },
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.06)',
          circular: true,
        },
        angleLines: {
          color: 'rgba(255, 255, 255, 0.06)',
        },
        pointLabels: {
          color: '#94a3b8',
          font: {
            size: 12,
            weight: '500',
            family: "'Inter', sans-serif",
          },
          padding: 12,
        },
      },
    },
    plugins: {
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(129, 140, 248, 0.3)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        titleFont: { weight: '600' },
        callbacks: {
          label: (ctx) => `Score: ${(ctx.raw * 100).toFixed(1)}%`,
        },
      },
      legend: {
        display: false,
      },
    },
    animation: {
      duration: 1000,
      easing: 'easeOutQuart',
    },
  }

  return (
    <div style={{ position: 'relative', height: '320px', width: '100%' }}>
      <Radar data={data} options={options} />
    </div>
  )
}
