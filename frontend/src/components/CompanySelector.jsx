import { Search, Landmark } from 'lucide-react';
import { fmtMoney } from '../format';

export default function CompanySelector({
  companies, totalCount, selectedId, onSelect, apiOnline, loadError, onRetry, search, onSearch, loading,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-head">
        <div className="brand">
          <span className="brand-mark"><Landmark size={16} strokeWidth={2.2} /></span>
          <div>
            <span className="eyebrow">Comp Universe</span>
            <h1>M&amp;A Analyzer</h1>
          </div>
        </div>

        <div className="search-box">
          <Search size={14} strokeWidth={2} className="search-icon" />
          <input
            className="search-input"
            placeholder="Search companies or ticker…"
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            aria-label="Search companies"
          />
        </div>
      </div>

      {loadError ? (
        <div className="sidebar-error">
          <p>Couldn't load companies — {loadError}</p>
          <button className="retry-btn" onClick={onRetry}>Retry</button>
        </div>
      ) : loading ? (
        <div className="company-list">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="skel skel-company-row" />
          ))}
        </div>
      ) : (
        <div className="company-list" role="listbox" aria-label="Select target company">
          {companies.length === 0 && (
            <p className="no-results">No companies match "{search}"</p>
          )}
          {companies.map((c) => (
            <button
              key={c.company_id}
              role="option"
              aria-selected={c.company_id === selectedId}
              className={`company-row ${c.company_id === selectedId ? 'active' : ''}`}
              onClick={() => onSelect(c.company_id)}
            >
              <div className="company-row-main">
                <span className="company-name">{c.name}</span>
                <span className="company-ticker mono">{c.ticker}</span>
              </div>
              <span className="company-ev mono">{fmtMoney(c.enterprise_value_musd)}</span>
            </button>
          ))}
        </div>
      )}

      <div className="sidebar-foot">
        <span className={`status-dot ${apiOnline === false ? 'offline' : apiOnline === true ? 'online' : 'pending'}`} />
        <span>
          {apiOnline === false ? 'API offline' : apiOnline === true ? 'API connected' : 'Checking API…'}
        </span>
        {totalCount > 0 && <span className="company-count">· {totalCount} companies</span>}
      </div>
    </aside>
  );
}
