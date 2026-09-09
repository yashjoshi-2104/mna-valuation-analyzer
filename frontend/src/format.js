export function fmtMoney(musd) {
  if (musd === null || musd === undefined || Number.isNaN(musd)) return '—';
  const abs = Math.abs(musd);
  if (abs >= 1000) return `$${(musd / 1000).toFixed(1)}B`;
  return `$${musd.toFixed(0)}M`;
}

export function fmtPct(v, digits = 1) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return `${v.toFixed(digits)}%`;
}

export function fmtX(v, digits = 1) {
  if (v === null || v === undefined || Number.isNaN(v)) return 'NM';
  return `${v.toFixed(digits)}x`;
}

export function fmtNum(v, digits = 2) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return v.toFixed(digits);
}
