import { useEffect, useState, useCallback, useMemo } from 'react';
import { LayoutGrid, GitCompareArrows, Landmark, TrendingUp, Sparkles } from 'lucide-react';
import { api } from './api';
import CompanySelector from './components/CompanySelector';
import OverviewTab from './components/OverviewTab';
import CompsTab from './components/CompsTab';
import TransactionsTab from './components/TransactionsTab';
import ValuationTab from './components/ValuationTab';
import AiAnalystTab from './components/AiAnalystTab';
import Skeleton from './components/Skeleton';
import './app.css';

const TABS = [
  { id: 'Overview', icon: LayoutGrid },
  { id: 'Comparables', icon: GitCompareArrows },
  { id: 'Transactions', icon: Landmark },
  { id: 'Valuation', icon: TrendingUp },
  { id: 'AI Analyst', icon: Sparkles },
];

// Small helper: each independent data domain gets its own {data, error, loading}
// slice instead of one global error flag. A failed transactions fetch should
// never block the Overview tab, and vice versa - that coupling was the root
// cause of tabs looking "broken" together when only one endpoint had an issue.
function useAsync(fn, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  const run = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((e) => setState({ data: null, error: e.message, loading: false }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => { run(); }, [run]);

  return { ...state, retry: run };
}

function Section({ state, label, skeleton, children }) {
  if (state.loading) return skeleton || <div className="loading-note">Loading {label}…</div>;
  if (state.error) {
    return (
      <div className="error-banner">
        <span>Couldn't load {label} — {state.error}</span>
        <button className="retry-btn" onClick={state.retry}>Retry</button>
      </div>
    );
  }
  return <div className="fade-in">{children}</div>;
}

export default function App() {
  const [selectedId, setSelectedId] = useState(null);
  const [tab, setTab] = useState('Overview');
  const [apiOnline, setApiOnline] = useState(null);
  const [search, setSearch] = useState('');

  const companiesState = useAsync(() => api.listCompanies(), []);
  const transactionsState = useAsync(() => api.listTransactions(), []);
  const txSummaryState = useAsync(() => api.transactionsSummary(), []);

  const metricsState = useAsync(
    () => (selectedId ? api.getMetrics(selectedId) : Promise.resolve(null)),
    [selectedId]
  );
  const compsState = useAsync(
    () => (selectedId ? api.getComps(selectedId, 5) : Promise.resolve(null)),
    [selectedId]
  );
  const valuationState = useAsync(
    () => (selectedId ? api.getValuation(selectedId, 5) : Promise.resolve(null)),
    [selectedId]
  );

  // Auto-select the first company once the list loads.
  useEffect(() => {
    if (companiesState.data?.length && !selectedId) {
      setSelectedId(companiesState.data[0].company_id);
    }
  }, [companiesState.data, selectedId]);

  // Lightweight periodic health check so connectivity issues are visible
  // immediately instead of showing up as a mysterious tab-specific failure.
  useEffect(() => {
    let cancelled = false;
    const check = () => {
      api.health()
        .then(() => !cancelled && setApiOnline(true))
        .catch(() => !cancelled && setApiOnline(false));
    };
    check();
    const id = setInterval(check, 15000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const companies = companiesState.data || [];
  const selectedCompany = companies.find((c) => c.company_id === selectedId);

  const filteredCompanies = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return companies;
    return companies.filter(
      (c) => c.name.toLowerCase().includes(q) || c.ticker.toLowerCase().includes(q)
    );
  }, [companies, search]);

  return (
    <div className="app-shell">
      <CompanySelector
        companies={filteredCompanies}
        totalCount={companies.length}
        selectedId={selectedId}
        onSelect={setSelectedId}
        apiOnline={apiOnline}
        loadError={companiesState.error}
        onRetry={companiesState.retry}
        search={search}
        onSearch={setSearch}
        loading={companiesState.loading}
      />

      <main className="main-col">
        <nav className="tab-bar">
          {TABS.map(({ id, icon: Icon }) => (
            <button
              key={id}
              className={`tab-btn ${tab === id ? 'active' : ''}`}
              onClick={() => setTab(id)}
            >
              <Icon size={15} strokeWidth={2} />
              {id}
            </button>
          ))}
        </nav>

        <div className="content-area">
          {tab === 'Overview' && (
            <Section state={metricsState} label="company overview" skeleton={<Skeleton kind="overview" />}>
              <OverviewTab company={selectedCompany} metrics={metricsState.data} />
            </Section>
          )}
          {tab === 'Comparables' && (
            <Section state={compsState} label="comparable companies" skeleton={<Skeleton kind="list" />}>
              <CompsTab comps={compsState.data} targetName={selectedCompany?.name} />
            </Section>
          )}
          {tab === 'Transactions' && (
            <Section state={transactionsState} label="transactions" skeleton={<Skeleton kind="table" />}>
              <Section state={txSummaryState} label="transaction summary" skeleton={<Skeleton kind="table" />}>
                <TransactionsTab transactions={transactionsState.data} summary={txSummaryState.data} />
              </Section>
            </Section>
          )}
          {tab === 'Valuation' && (
            <Section state={valuationState} label="valuation" skeleton={<Skeleton kind="valuation" />}>
              <ValuationTab valuation={valuationState.data} />
            </Section>
          )}
          {tab === 'AI Analyst' && (
            <AiAnalystTab companyId={selectedId} companyName={selectedCompany?.name} />
          )}
        </div>
      </main>
    </div>
  );
}
