import React from 'react';

export default function TrustIntegrityCard({ integrity }) {
  if (!integrity) return null;

  const { risk_level, flags, clean } = integrity;

  return (
    <div className="card" id="integrity-card">
      <div className="card__title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        Trust & Integrity Check
        <span className={`integrity-badge integrity-badge--${risk_level}`}>
          Risk: {risk_level}
        </span>
      </div>

      {clean ? (
        <div style={{ color: 'var(--accent-emerald)', padding: 'var(--space-md)', background: 'rgba(52, 211, 153, 0.05)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(52, 211, 153, 0.15)', display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          ✅ No anomalies detected — transaction patterns look organic.
        </div>
      ) : (
        <div className="integrity-flags">
          {flags.map((flag, idx) => (
            <div key={idx} className={`integrity-flag integrity-flag--${flag.severity}`}>
              <div className="integrity-flag__header">
                <span className="integrity-flag__icon">⚠️</span>
                <span className="integrity-flag__severity">{flag.severity} Severity</span>
              </div>
              <div className="integrity-flag__message">
                {flag.message}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
