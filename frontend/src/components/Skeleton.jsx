export default function Skeleton({ kind = 'list' }) {
  if (kind === 'overview') {
    return (
      <div className="skel-block">
        <div className="skel skel-title" />
        <div className="skel-grid">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="skel skel-card" />
          ))}
        </div>
      </div>
    );
  }
  if (kind === 'table') {
    return (
      <div className="skel-block">
        <div className="skel skel-title" />
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skel skel-row" />
        ))}
      </div>
    );
  }
  if (kind === 'valuation') {
    return (
      <div className="skel-block">
        <div className="skel skel-title" />
        <div className="skel skel-hero" />
        <div className="skel skel-row" style={{ height: 90 }} />
      </div>
    );
  }
  // 'list' (comparables)
  return (
    <div className="skel-block">
      <div className="skel skel-title" />
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="skel skel-row" />
      ))}
    </div>
  );
}
