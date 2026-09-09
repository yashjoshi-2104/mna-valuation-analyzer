import { fmtMoney } from '../format';

function RangeBar({ label, low, base, high, domainLow, domainHigh, currentEv }) {
  const span = domainHigh - domainLow || 1;
  const pct = (v) => Math.min(100, Math.max(0, ((v - domainLow) / span) * 100));

  return (
    <div className="range-row">
      <span className="range-label">{label}</span>
      <div className="range-track">
        {low !== null && high !== null && (
          <div
            className="range-fill"
            style={{ left: `${pct(low)}%`, width: `${pct(high) - pct(low)}%` }}
          />
        )}
        {base !== null && (
          <div className="range-marker base" style={{ left: `${pct(base)}%` }} title={`Base: ${fmtMoney(base)}`} />
        )}
        {currentEv !== undefined && currentEv !== null && (
          <div className="range-marker current" style={{ left: `${pct(currentEv)}%` }} title={`Current EV: ${fmtMoney(currentEv)}`} />
        )}
      </div>
      <div className="range-values mono">
        <span>{fmtMoney(low)}</span>
        <span className="range-base">{fmtMoney(base)}</span>
        <span>{fmtMoney(high)}</span>
      </div>
    </div>
  );
}

export default function ValuationTab({ valuation }) {
  if (!valuation) return null;
  const { target, valuation: v, peers_used } = valuation;

  const allLows = v.methods.map((m) => m.low_ev_musd).filter((x) => x !== null);
  const allHighs = v.methods.map((m) => m.high_ev_musd).filter((x) => x !== null);
  const domainLow = Math.min(...allLows, target.current_enterprise_value_musd) * 0.9;
  const domainHigh = Math.max(...allHighs, target.current_enterprise_value_musd) * 1.1;

  return (
    <div className="panel-block">
      <div className="block-head">
        <div>
          <span className="eyebrow">Trading comps + precedent transactions, blended</span>
          <h2>Valuation Range — {target.name}</h2>
        </div>
      </div>

      <div className="valuation-headline">
        <div className="headline-figure">
          <span className="stat-label">Base Case Enterprise Value</span>
          <span className="headline-value mono">{fmtMoney(v.base_ev_musd)}</span>
        </div>
        <div className="headline-figure">
          <span className="stat-label">Current Market EV</span>
          <span className="headline-value mono muted-value">{fmtMoney(target.current_enterprise_value_musd)}</span>
        </div>
      </div>

      <div className="range-chart">
        {v.methods.map((m) => (
          <RangeBar
            key={m.method}
            label={m.method}
            low={m.low_ev_musd}
            base={m.base_ev_musd}
            high={m.high_ev_musd}
            domainLow={domainLow}
            domainHigh={domainHigh}
          />
        ))}
        <RangeBar
          label="Blended"
          low={v.low_ev_musd}
          base={v.base_ev_musd}
          high={v.high_ev_musd}
          domainLow={domainLow}
          domainHigh={domainHigh}
          currentEv={target.current_enterprise_value_musd}
        />
        <div className="range-legend">
          <span><i className="legend-swatch base" /> Base case</span>
          <span><i className="legend-swatch current" /> Current market EV</span>
        </div>
      </div>

      <div className="methods-detail">
        {v.methods.map((m) => (
          <div key={m.method} className="method-card">
            <h3>{m.method}</h3>
            <p>{m.notes}</p>
          </div>
        ))}
      </div>

      <div className="peers-used">
        <span className="stat-label">Peer set used ({peers_used.length})</span>
        <div className="peer-chips">
          {peers_used.map((p) => (
            <span key={p.company_id} className="peer-chip mono">
              {p.name} · {(p.similarity_score * 100).toFixed(0)}%
            </span>
          ))}
        </div>
      </div>

      <p className="footnote disclaimer">{v.disclaimer}</p>
    </div>
  );
}
