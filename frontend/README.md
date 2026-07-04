# VyapaarScore — Frontend

React + Vite dashboard for **VyapaarScore**, an explainable UPI cash-flow credit scoring engine for India's micro-merchants.

This is the client application that talks to the FastAPI backend (see `../main.py`) to upload transaction data, display the score, and walk through the simulated Account Aggregator consent flow.

> For the full project overview — problem statement, scoring methodology, and all backend modules — see the [root README](../README.md).

## What's in here

- **Merchant Dashboard** — score, grade, radar chart, factor breakdown, rule-based improvement tips, score trend chart
- **What-If Simulator** — live sliders that recompute the score against realistic business scenarios
- **Trust & Integrity Check** — surfaces anomaly/fraud-pattern flags alongside the score
- **Peer Benchmark** — percentile comparison against a modeled category distribution
- **Lender View** — a print/PDF-ready recommendation report for a loan officer
- **Account Aggregator flow** — a simulated RBI AA consent journey (bank selection → consent artifact → approve) as an alternative entry point to CSV upload

## Tech stack

- React 18 + Vite
- Chart.js / react-chartjs-2 (radar chart, score trend line chart)
- Plain CSS with design tokens (see `src/index.css`) — no CSS framework

## Running locally

```bash
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` by default and expects the backend API at `http://127.0.0.1:8000` (see `API_URL` in `src/App.jsx`).

Make sure the backend is running first:
```bash
cd ..
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## Building for production

```bash
npm run build
```

Outputs a static build to `dist/`, ready to deploy (e.g. to Vercel or Netlify).