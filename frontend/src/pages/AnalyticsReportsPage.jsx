import { useMemo, useState } from 'react';
import {
  PieChart, Pie, Cell,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  detectMissingInformation,
  draftMissingInfoEmail,
  extractEducationSignals,
  extractExperienceSignals,
  extractResearchSignals,
} from '../lib/profileParsers';

function pct(value, total) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}

function scoreBand(score) {
  if (score == null || Number.isNaN(Number(score))) return 'unknown';
  const numeric = Number(score);
  if (numeric >= 75) return 'high';
  if (numeric >= 50) return 'medium';
  return 'low';
}

const COLORS = {
  completed: '#10b981',
  processing: '#f59e0b',
  pending: '#6b7280',
  failed: '#ef4444',
  high: '#10b981',
  medium: '#f59e0b',
  low: '#ef4444',
};

export default function AnalyticsReportsPage({
  candidates,
  loading,
  selectedCandidate,
  selectedCandidateId,
  selectCandidate,
}) {
  const [copied, setCopied] = useState(false);
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  const reportRows = useMemo(
    () =>
      (candidates || []).map((candidate) => {
        const missing = detectMissingInformation(candidate);
        return {
          id: candidate.id,
          name: candidate.full_name || candidate.filename || `candidate_${candidate.id}`,
          email: candidate.email || '—',
          status: candidate.status || 'pending',
          score: candidate.overall_score,
          missingCount: missing.length,
          missing,
          uploadedAt: candidate.uploaded_at,
        };
      }),
    [candidates],
  );

  // Sort rows
  const sortedRows = useMemo(() => {
    const rows = [...reportRows];
    rows.sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];
      
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    });
    return rows;
  }, [reportRows, sortBy, sortOrder]);

  const chartStats = useMemo(() => {
    const total = reportRows.length;
    const completed = reportRows.filter((row) => row.status === 'completed').length;
    const processing = reportRows.filter((row) => row.status === 'processing').length;
    const pending = reportRows.filter((row) => row.status === 'pending').length;
    const failed = reportRows.filter((row) => row.status === 'failed').length;

    const withMissing = reportRows.filter((row) => row.missingCount > 0).length;

    const scoreHigh = reportRows.filter((row) => scoreBand(row.score) === 'high').length;
    const scoreMedium = reportRows.filter((row) => scoreBand(row.score) === 'medium').length;
    const scoreLow = reportRows.filter((row) => scoreBand(row.score) === 'low').length;
    const scoreUnknown = total - scoreHigh - scoreMedium - scoreLow;

    return {
      total,
      completed,
      processing,
      pending,
      failed,
      withMissing,
      scoreHigh,
      scoreMedium,
      scoreLow,
      scoreUnknown,
    };
  }, [reportRows]);

  // Data for pie chart - Status
  const statusChartData = useMemo(() => [
    { name: 'Completed', value: chartStats.completed, fill: COLORS.completed },
    { name: 'Processing', value: chartStats.processing, fill: COLORS.processing },
    { name: 'Pending', value: chartStats.pending, fill: COLORS.pending },
    { name: 'Failed', value: chartStats.failed, fill: COLORS.failed },
  ].filter(d => d.value > 0), [chartStats]);

  // Data for bar chart - Score Bands
  const scoreChartData = useMemo(() => [
    { name: 'High (75+)', value: chartStats.scoreHigh, fill: COLORS.high },
    { name: 'Medium (50-74)', value: chartStats.scoreMedium, fill: COLORS.medium },
    { name: 'Low (0-49)', value: chartStats.scoreLow, fill: COLORS.low },
    { name: 'Unknown', value: chartStats.scoreUnknown, fill: '#d1d5db' },
  ].filter(d => d.value > 0), [chartStats]);

  const details = useMemo(() => {
    if (!selectedCandidate) return null;

    const missingFields = detectMissingInformation(selectedCandidate);
    const emailDraft = draftMissingInfoEmail(selectedCandidate, missingFields);

    return {
      missingFields,
      emailDraft,
      education: extractEducationSignals(selectedCandidate.raw_text),
      research: extractResearchSignals(selectedCandidate.raw_text),
      experience: extractExperienceSignals(selectedCandidate.raw_text),
    };
  }, [selectedCandidate]);

  async function copyDraftEmail() {
    if (!details?.emailDraft) return;
    try {
      await navigator.clipboard.writeText(details.emailDraft);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  function handleSort(field) {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  }

  return (
    <section className="page-grid">
      <section className="summary-strip reveal">
        <article className="summary-tile">
          <p>Total Candidates</p>
          <strong>{chartStats.total}</strong>
        </article>
        <article className="summary-tile">
          <p>Completed Analyses</p>
          <strong>{chartStats.completed}</strong>
        </article>
        <article className="summary-tile">
          <p>Profiles Missing Data</p>
          <strong>{chartStats.withMissing}</strong>
        </article>
        <article className="summary-tile">
          <p>High Scoring</p>
          <strong>{chartStats.scoreHigh}</strong>
        </article>
      </section>

      <section className="panel reveal delay-1">
        <h2>Analytics Dashboard</h2>
        <div className="charts-grid">
          {/* Status Distribution Pie Chart */}
          <div className="chart-container">
            <h3>Status Distribution</h3>
            {statusChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {statusChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p>No data available</p>
            )}
          </div>

          {/* Score Distribution Bar Chart */}
          <div className="chart-container">
            <h3>Score Distribution</h3>
            {scoreChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={scoreChartData}
                  margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3b82f6" radius={[8, 8, 0, 0]}>
                    {scoreChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p>No data available</p>
            )}
          </div>
        </div>
      </section>

      <div className="candidate-layout reveal delay-2">
        <article className="panel">
          <h2>Candidate Comparison Table</h2>
          {loading && <p>Loading candidate records...</p>}
          {!loading && reportRows.length === 0 && <p>No candidate records available yet.</p>}

          {!loading && reportRows.length > 0 && (
            <div className="table-scroll">
              <table className="report-table">
                <thead>
                  <tr>
                    <th onClick={() => handleSort('id')}>ID {sortBy === 'id' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                    <th onClick={() => handleSort('name')}>Candidate {sortBy === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                    <th onClick={() => handleSort('email')}>Email {sortBy === 'email' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                    <th onClick={() => handleSort('status')}>Status {sortBy === 'status' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                    <th onClick={() => handleSort('score')}>Score {sortBy === 'score' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                    <th onClick={() => handleSort('missingCount')}>Missing {sortBy === 'missingCount' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                    <th onClick={() => handleSort('uploadedAt')}>Uploaded {sortBy === 'uploadedAt' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedRows.map((row) => (
                    <tr
                      key={row.id}
                      className={selectedCandidateId === row.id ? 'active-row' : ''}
                      onClick={() => selectCandidate(row.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td>{row.id}</td>
                      <td>{row.name}</td>
                      <td className="email-cell">{row.email}</td>
                      <td><span className={`status-badge status-${row.status}`}>{row.status}</span></td>
                      <td><strong>{row.score ?? '—'}</strong></td>
                      <td>{row.missingCount}</td>
                      <td>{row.uploadedAt ? new Date(row.uploadedAt).toLocaleString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <article className="panel">
          <h2>Personalized Missing-Info Email</h2>
          {!selectedCandidate && <p className="muted">Select a candidate row to view profile details and draft email.</p>}

          {selectedCandidate && details && (
            <div className="page-grid">
              <section className="info-box">
                <h3>{selectedCandidate.full_name || selectedCandidate.filename || `Candidate ${selectedCandidate.id}`}</h3>
                <p><strong>Missing Fields:</strong> {details.missingFields.length === 0 ? 'Complete ✓' : details.missingFields.join(', ')}</p>
                {details.education.detectedDegrees.length > 0 && (
                  <div>
                    <p><strong>Education:</strong></p>
                    <div className="tag-row">
                      {details.education.detectedDegrees.map((degree) => (
                        <span className="tag" key={degree}>{degree}</span>
                      ))}
                    </div>
                  </div>
                )}
                {details.research.topicHints.length > 0 && (
                  <div>
                    <p><strong>Research Areas:</strong></p>
                    <div className="tag-row">
                      {details.research.topicHints.map((topic) => (
                        <span className="tag" key={topic}>{topic}</span>
                      ))}
                    </div>
                  </div>
                )}
              </section>

              <section className="email-panel">
                <div className="email-toolbar">
                  <p className="muted">Ready-to-send draft</p>
                  <button type="button" className="btn compact" onClick={copyDraftEmail}>
                    {copied ? '✓ Copied' : 'Copy Email'}
                  </button>
                </div>
                <pre className="email-draft-pretty">{details.emailDraft}</pre>
              </section>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
