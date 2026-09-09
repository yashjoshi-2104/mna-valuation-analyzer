import {
  DollarSign, TrendingUp, PieChart, Banknote, Wallet,
  Building2, Scale, Percent, Layers,
} from 'lucide-react';
import { fmtMoney, fmtPct, fmtX } from '../format';

function Stat({ icon: Icon, label, value, accent, trend }) {
  return (
    <div className="stat">
      <div className="stat-top">
        <span className="stat-icon"><Icon size={14} strokeWidth={2} /></span>
        <span className="stat-label">{label}</span>
      </div>
      <span className={`stat-value mono ${accent ? 'accent' : ''} ${trend === 'up' ? 'trend-up' : trend === 'down' ? 'trend-down' : ''}`}>
        {value}
      </span>
    </div>
  );
}

export default function OverviewTab({ company, metrics }) {
  if (!company || !metrics) return null;
  const growthTrend = company.revenue_growth_pct >= 15 ? 'up' : company.revenue_growth_pct < 0 ? 'down' : null;

  return (
    <div className="panel-block">
      <div className="block-head">
        <div>
          <span className="eyebrow">{company.industry} · {company.geography}</span>
          <h2>{company.name}</h2>
        </div>
        <span className="ticker-badge mono">{company.ticker}</span>
      </div>

      <div className="stat-grid">
        <Stat icon={DollarSign} label="Revenue" value={fmtMoney(metrics.revenue_musd)} />
        <Stat icon={TrendingUp} label="Revenue Growth" value={fmtPct(company.revenue_growth_pct)} trend={growthTrend} />
        <Stat icon={PieChart} label="EBITDA" value={fmtMoney(metrics.ebitda_musd)} />
        <Stat icon={Percent} label="EBITDA Margin" value={fmtPct(metrics.ebitda_margin_pct)} />
        <Stat icon={Banknote} label="Net Income" value={fmtMoney(metrics.net_income_musd)} />
        <Stat icon={Building2} label="Market Cap" value={fmtMoney(metrics.market_cap_musd)} accent />
        <Stat icon={Layers} label="Enterprise Value" value={fmtMoney(metrics.enterprise_value_musd)} accent />
        <Stat icon={Scale} label="Debt / EBITDA" value={fmtX(metrics.debt_to_ebitda)} />
        <Stat icon={Wallet} label="P / E" value={fmtX(metrics.pe_ratio)} />
        <Stat icon={DollarSign} label="EV / Revenue" value={fmtX(metrics.ev_revenue)} />
        <Stat icon={DollarSign} label="EV / EBITDA" value={fmtX(metrics.ev_ebitda)} />
      </div>

      <p className="footnote">
        Every figure above is a direct or one-step-derived calculation from the raw dataset —
        no model or LLM is involved in this page.
      </p>
    </div>
  );
}
