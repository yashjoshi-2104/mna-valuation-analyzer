import { fmtMoney, fmtX } from '../format';

export default function TransactionsTab({ transactions, summary }) {
  if (!transactions || !summary) return null;
  return (
    <div className="panel-block">
      <div className="block-head">
        <div>
          <span className="eyebrow">{summary.deal_count} disclosed deals · software sector</span>
          <h2>Precedent Transactions</h2>
        </div>
      </div>

      <div className="stat-grid compact">
        <div className="stat">
          <span className="stat-label">Median EV/Revenue</span>
          <span className="stat-value mono accent">{fmtX(summary.ev_revenue.median)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Median EV/EBITDA</span>
          <span className="stat-value mono accent">{fmtX(summary.ev_ebitda.median)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">EV/Revenue Range (P25–P75)</span>
          <span className="stat-value mono">{fmtX(summary.ev_revenue.p25)} – {fmtX(summary.ev_revenue.p75)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">EV/EBITDA Range (P25–P75)</span>
          <span className="stat-value mono">{fmtX(summary.ev_ebitda.p25)} – {fmtX(summary.ev_ebitda.p75)}</span>
        </div>
      </div>

      <div className="table-wrap">
        <table className="deal-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Acquirer</th>
              <th>Target</th>
              <th className="num-col">Deal Value</th>
              <th className="num-col">EV/Rev</th>
              <th className="num-col">EV/EBITDA</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t) => (
              <tr key={t.deal_id}>
                <td className="mono">{t.announce_date}</td>
                <td>{t.acquirer}</td>
                <td>{t.target}</td>
                <td className="mono num-col">{fmtMoney(t.deal_value_musd)}</td>
                <td className="mono num-col">{fmtX(t.ev_revenue)}</td>
                <td className="mono num-col">{fmtX(t.ev_ebitda)}</td>
                <td className="deal-type">{t.deal_type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="footnote">
        Deal-level multiples typically embed a control premium over public trading levels —
        treat these as a separate reference point, not a like-for-like with trading comps.
      </p>
    </div>
  );
}
