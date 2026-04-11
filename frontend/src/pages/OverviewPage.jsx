export default function OverviewPage({ candidates, loading, refreshCandidates }) {
  const total = candidates.length;
  const analyzed = candidates.filter((item) => item.status === 'analyzed').length;
  const processing = candidates.filter((item) => item.status === 'processing').length;

  return (
    <section className="page-grid">
      <article className="panel hero-panel reveal">
        <p className="eyebrow">SMART HR RECRUITMENT</p>
        <h2>TALASH Control Center</h2>
        <p className="muted">
          The app is now simplified into essential pages: overview, CV ingestion, and candidate insights.
        </p>
        <button className="btn" type="button" onClick={refreshCandidates} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh Candidate Data'}
        </button>
      </article>

      <section className="stats-grid reveal delay-1">
        <article className="stat-card">
          <p>Total CVs</p>
          <h3>{total}</h3>
        </article>
        <article className="stat-card">
          <p>Analyzed Profiles</p>
          <h3>{analyzed}</h3>
        </article>
        <article className="stat-card">
          <p>In Processing</p>
          <h3>{processing}</h3>
        </article>
      </section>

      <article className="panel reveal delay-2">
        <h3>How to Use</h3>
        <ul className="clean-list">
          <li>Use CV Ingestion for single, bulk, folder, or server-file parsing.</li>
          <li>Open Candidate Insights to review all sections in one place.</li>
          <li>Run analysis on selected candidate and refresh results.</li>
        </ul>
      </article>
    </section>
  );
}
