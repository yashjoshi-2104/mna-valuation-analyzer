import { fmtMoney, fmtPct, fmtX } from '../format';

export default function CompsTab({ comps, targetName }) {
  if (!comps) return null;
  return (
    <div className="panel-block">
      <div className="block-head">
        <div>
          <span className="eyebrow">Cosine similarity · StandardScaler-normalized features</span>
          <h2>Comparable Companies</h2>
        </div>
      </div>

      <div className="comps-list">
        {comps.map((c, i) => (
          <div key={c.company_id} className="comp-row">
            <span className="comp-rank mono">{String(i + 1).padStart(2, '0')}</span>
            <div className="comp-main">
              <div className="comp-name-line">
                <span className="comp-name">{c.name}</span>
                <span className="comp-industry">{c.industry}</span>
              </div>
              <div className="sim-bar-track">
                <div
                  className="sim-bar-fill"
                  style={{ width: `${Math.max(c.similarity_score, 0) * 100}%` }}
                />
              </div>
            </div>
            <span className="sim-score mono">{(c.similarity_score * 100).toFixed(1)}%</span>
            <div className="comp-metrics mono">
              <span>{fmtMoney(c.revenue_musd)} rev</span>
              <span>{fmtPct(c.revenue_growth_pct)} gr</span>
              <span>{fmtPct(c.ebitda_margin_pct)} margin</span>
              <span>{fmtX(c.debt_to_ebitda)} D/E</span>
            </div>
          </div>
        ))}
      </div>

      <p className="footnote">
        Ranked by cosine similarity to {targetName} across revenue, growth, EBITDA margin,
        market cap, enterprise value, and Debt/EBITDA — each scaled to zero mean / unit
        variance so no single metric dominates purely by magnitude.
      </p>
    </div>
  );
}
