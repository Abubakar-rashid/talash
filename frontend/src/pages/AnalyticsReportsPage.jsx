import { useMemo, useState } from 'react';
import {
  PieChart, Pie, Cell,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, Area, AreaChart
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
  const [emailRegenLoading, setEmailRegenLoading] = useState(false);
  const [emailRegeneratedAt, setEmailRegeneratedAt] = useState(null);
  const [comparisonCandidateIds, setComparisonCandidateIds] = useState([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [showStatistics, setShowStatistics] = useState(false);

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

  async function regenerateEmail() {
    if (!selectedCandidate?.id) return;
    setEmailRegenLoading(true);
    try {
      const resp = await fetch(`http://localhost:8000/analysis/candidate/${selectedCandidate.id}/email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (resp.ok) {
        const result = await resp.json();
        setEmailRegeneratedAt(new Date().toLocaleString());
        // Refresh details to show new email
        setTimeout(() => {
          selectCandidate(selectedCandidate.id);
        }, 500);
      }
    } catch (err) {
      console.error('Failed to regenerate email:', err);
    } finally {
      setEmailRegenLoading(false);
    }
  }

  async function batchExportEmails() {
    const rowsToExport = comparisonCandidateIds.length > 0
      ? sortedRows.filter(r => comparisonCandidateIds.includes(r.id))
      : sortedRows;
    
    if (rowsToExport.length === 0) {
      alert('Please select candidates to export');
      return;
    }

    try {
      // Fetch email for each candidate
      const emailLines = [];
      for (const row of rowsToExport) {
        const candidate = candidates.find(c => c.id === row.id);
        if (candidate) {
          const missing = detectMissingInformation(candidate);
          const email = draftMissingInfoEmail(candidate, missing);
          emailLines.push(`=== CANDIDATE: ${row.name} ===`);
          emailLines.push(`Email: ${row.email}`);
          emailLines.push(`Score: ${row.score ?? 'N/A'}`);
          emailLines.push('');
          emailLines.push(email);
          emailLines.push('');
          emailLines.push('---');
          emailLines.push('');
        }
      }

      // Create download
      const text = emailLines.join('\n');
      const blob = new Blob([text], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `emails_${new Date().toISOString().slice(0, 10)}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  }

  function toggleComparisonCandidate(candidateId) {
    if (comparisonCandidateIds.includes(candidateId)) {
      setComparisonCandidateIds(comparisonCandidateIds.filter(id => id !== candidateId));
    } else {
      setComparisonCandidateIds([...comparisonCandidateIds, candidateId]);
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

  // Leaderboard data: ranked by score
  const leaderboardData = useMemo(() => {
    return sortedRows
      .filter(r => r.score != null)
      .sort((a, b) => b.score - a.score)
      .map((row, idx) => ({
        ...row,
        rank: idx + 1,
        medal: idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '',
      }));
  }, [sortedRows]);

  // Comparison data
  const comparisonRows = useMemo(() => {
    return sortedRows.filter(r => comparisonCandidateIds.includes(r.id));
  }, [sortedRows, comparisonCandidateIds]);

  // Cohort statistics
  const cohortStats = useMemo(() => {
    const scores = reportRows.filter(r => r.score != null).map(r => r.score);
    const avgScore = scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 0;
    const maxScore = scores.length > 0 ? Math.max(...scores) : 0;
    const minScore = scores.length > 0 ? Math.min(...scores) : 0;
    
    const experienceYears = reportRows
      .map(r => extractExperienceSignals(candidates.find(c => c.id === r.id)?.raw_text || ''))
      .map(e => e.totalYears || 0);
    const avgExp = experienceYears.length > 0 
      ? (experienceYears.reduce((a, b) => a + b, 0) / experienceYears.length).toFixed(1)
      : 0;

    return {
      totalCandidates: reportRows.length,
      avgScore,
      maxScore,
      minScore,
      avgExp,
      completionRate: pct(chartStats.completed, chartStats.total),
      withData: chartStats.completed,
      incomplete: chartStats.pending + chartStats.processing,
    };
  }, [reportRows, candidates, chartStats]);

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
          <div className="toolbar">
            <button className="btn compact" onClick={() => setShowLeaderboard(!showLeaderboard)}>
              {showLeaderboard ? '← Back to Table' : '🏆 Leaderboard'}
            </button>
            <button className="btn compact" onClick={() => setShowStatistics(!showStatistics)}>
              {showStatistics ? '← Back to Table' : '📊 Statistics'}
            </button>
            {comparisonCandidateIds.length > 0 && (
              <button className="btn compact" onClick={() => setShowComparisonModal(true)}>
                ⚖️ Compare {comparisonCandidateIds.length}
              </button>
            )}
            <button className="btn compact" onClick={batchExportEmails}>
              📥 Export Emails
            </button>
          </div>

          {loading && <p>Loading candidate records...</p>}
          {!loading && reportRows.length === 0 && <p>No candidate records available yet.</p>}

          {!loading && !showLeaderboard && !showStatistics && reportRows.length > 0 && (
            <div className="table-scroll">
              <table className="report-table">
                <thead>
                  <tr>
                    <th style={{ width: '40px' }}>
                      <input type="checkbox" onChange={(e) => {
                        if (e.target.checked) {
                          setComparisonCandidateIds(sortedRows.map(r => r.id));
                        } else {
                          setComparisonCandidateIds([]);
                        }
                      }} />
                    </th>
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
                      style={{ cursor: 'pointer' }}
                    >
                      <td onClick={(e) => e.stopPropagation()}>
                        <input 
                          type="checkbox"
                          checked={comparisonCandidateIds.includes(row.id)}
                          onChange={() => toggleComparisonCandidate(row.id)}
                        />
                      </td>
                      <td onClick={() => selectCandidate(row.id)}>{row.id}</td>
                      <td onClick={() => selectCandidate(row.id)}>{row.name}</td>
                      <td onClick={() => selectCandidate(row.id)} className="email-cell">{row.email}</td>
                      <td onClick={() => selectCandidate(row.id)}><span className={`status-badge status-${row.status}`}>{row.status}</span></td>
                      <td onClick={() => selectCandidate(row.id)}><strong>{row.score ?? '—'}</strong></td>
                      <td onClick={() => selectCandidate(row.id)}>{row.missingCount}</td>
                      <td onClick={() => selectCandidate(row.id)}>{row.uploadedAt ? new Date(row.uploadedAt).toLocaleString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && showLeaderboard && leaderboardData.length > 0 && (
            <div className="leaderboard">
              <h3>🏆 Candidate Leaderboard (by Score)</h3>
              <div className="leaderboard-list">
                {leaderboardData.map((row) => (
                  <div key={row.id} className="leaderboard-row" onClick={() => selectCandidate(row.id)} style={{ cursor: 'pointer' }}>
                    <span className="rank">{row.medal || `#${row.rank}`}</span>
                    <span className="name">{row.name}</span>
                    <span className="score" style={{ color: row.score >= 75 ? '#10b981' : row.score >= 50 ? '#f59e0b' : '#ef4444' }}>
                      {row.score.toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!loading && showStatistics && (
            <div className="statistics-panel">
              <h3>📊 Cohort Statistics</h3>
              <div className="stats-grid">
                <div className="stat-card">
                  <p className="stat-label">Total Candidates</p>
                  <p className="stat-value">{cohortStats.totalCandidates}</p>
                </div>
                <div className="stat-card">
                  <p className="stat-label">Avg Score</p>
                  <p className="stat-value">{cohortStats.avgScore}</p>
                </div>
                <div className="stat-card">
                  <p className="stat-label">Score Range</p>
                  <p className="stat-value">{cohortStats.minScore} — {cohortStats.maxScore}</p>
                </div>
                <div className="stat-card">
                  <p className="stat-label">Avg Experience</p>
                  <p className="stat-value">{cohortStats.avgExp} yrs</p>
                </div>
                <div className="stat-card">
                  <p className="stat-label">Completion Rate</p>
                  <p className="stat-value">{cohortStats.completionRate}%</p>
                </div>
                <div className="stat-card">
                  <p className="stat-label">Analyzed</p>
                  <p className="stat-value">{cohortStats.withData} / {cohortStats.totalCandidates}</p>
                </div>
              </div>
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
                  <div>
                    <p className="muted">Ready-to-send draft{emailRegeneratedAt && ` (updated: ${emailRegeneratedAt})`}</p>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button 
                      type="button" 
                      className="btn compact" 
                      onClick={regenerateEmail}
                      disabled={emailRegenLoading}
                    >
                      {emailRegenLoading ? '⟳ Regenerating...' : '🔄 Regenerate'}
                    </button>
                    <button type="button" className="btn compact" onClick={copyDraftEmail}>
                      {copied ? '✓ Copied' : '📋 Copy'}
                    </button>
                  </div>
                </div>
                <pre className="email-draft-pretty">{details.emailDraft}</pre>
              </section>
            </div>
          )}
        </article>
      </div>
      
      {showComparisonModal && comparisonRows.length > 0 && (
        <div className="comparison-modal" onClick={() => setShowComparisonModal(false)}>
          <div className="comparison-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="comparison-modal-header">
              <h2>⚖️ Candidate Comparison</h2>
              <button className="comparison-modal-close" onClick={() => setShowComparisonModal(false)}>×</button>
            </div>
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Missing</th>
                  <th>Uploaded</th>
                </tr>
              </thead>
              <tbody>
                {comparisonRows.map((row) => (
                  <tr key={row.id}>
                    <td><strong>{row.name}</strong></td>
                    <td>{row.email}</td>
                    <td style={{ fontWeight: 'bold', color: row.score >= 75 ? '#10b981' : row.score >= 50 ? '#f59e0b' : '#ef4444' }}>
                      {row.score?.toFixed(1) ?? '—'}
                    </td>
                    <td><span className={`status-badge status-${row.status}`}>{row.status}</span></td>
                    <td>{row.missingCount}</td>
                    <td style={{ fontSize: '12px' }}>{row.uploadedAt ? new Date(row.uploadedAt).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
