-- M&A Valuation Analyzer — DuckDB schema

CREATE TABLE IF NOT EXISTS companies (
    company_id      VARCHAR PRIMARY KEY,
    name            VARCHAR NOT NULL,
    ticker          VARCHAR,
    industry        VARCHAR,
    sector          VARCHAR,
    geography       VARCHAR
);

CREATE TABLE IF NOT EXISTS financials (
    company_id          VARCHAR REFERENCES companies(company_id),
    revenue_musd        DOUBLE,
    revenue_growth_pct  DOUBLE,
    ebitda_musd         DOUBLE,
    net_income_musd     DOUBLE,
    total_debt_musd     DOUBLE,
    cash_musd           DOUBLE
);

CREATE TABLE IF NOT EXISTS market_data (
    company_id           VARCHAR REFERENCES companies(company_id),
    shares_outstanding_m DOUBLE,
    share_price_usd      DOUBLE,
    market_cap_musd      DOUBLE,
    enterprise_value_musd DOUBLE
);

CREATE TABLE IF NOT EXISTS transactions (
    deal_id             VARCHAR PRIMARY KEY,
    acquirer            VARCHAR,
    target              VARCHAR,
    announce_date        DATE,
    deal_value_musd      DOUBLE,
    industry            VARCHAR,
    target_revenue_musd  DOUBLE,
    target_ebitda_musd   DOUBLE,
    ev_revenue           DOUBLE,
    ev_ebitda            DOUBLE,
    geography            VARCHAR,
    deal_type            VARCHAR
);
