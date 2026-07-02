import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler
)

export default function TrendChart({ trend }) {
  if (!trend || trend.length === 0) {
    return null;
  }

  const labels = trend.map((t) => t.date);
  const dataPoints = trend.map((t) => t.score);

  const data = {
    labels,
    datasets: [
      {
        label: 'Score Trend',
        data: dataPoints,
        backgroundColor: 'rgba(56, 189, 248, 0.15)',
        borderColor: 'rgba(56, 189, 248, 0.8)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(56, 189, 248, 1)',
        pointBorderColor: '#1e1b4b',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.3,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        min: 0,
        max: 100,
        ticks: {
          color: 'rgba(148, 163, 184, 0.8)',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.06)',
        },
      },
      x: {
        ticks: {
          color: 'rgba(148, 163, 184, 0.8)',
          maxTicksLimit: 6,
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.06)',
        },
      },
    },
    plugins: {
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(56, 189, 248, 0.3)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        titleFont: { weight: '600' },
        callbacks: {
          label: (ctx) => `Score: ${ctx.raw.toFixed(1)}`,
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
      <Line data={data} options={options} />
    </div>
  )
}
