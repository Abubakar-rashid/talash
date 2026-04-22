import { useMemo, useState } from 'react';
import {
  detectMissingInformation,
  draftMissingInfoEmail,
  extractEducationSignals,
  extractExperienceSignals,
  extractResearchSignals,
} from '../lib/profileParsers';
import { preprocessCandidate } from '../lib/api';

export default function CandidateInsightsPage({
  candidates,
  loading,
  candidatesError,
  selectedCandidate,
  selectedCandidateId,
  detailLoading,
  selectCandidate,
  onAnalyzeSelected,
  activeAnalyses,
  refreshCandidates,
}) {
  const selectedId = selectedCandidateId || selectedCandidate?.id;
  const [preprocessStatus, setPreprocessStatus] = useState('');

  const education = useMemo(
    () => extractEducationSignals(selectedCandidate?.raw_text),
    [selectedCandidate?.raw_text],
  );
  const research = useMemo(
    () => extractResearchSignals(selectedCandidate?.raw_text),
    [selectedCandidate?.raw_text],
  );
  const experience = useMemo(
    () => extractExperienceSignals(selectedCandidate?.raw_text),
    [selectedCandidate?.raw_text],
  );
  const missingFields = useMemo(
    () => detectMissingInformation(selectedCandidate),
    [selectedCandidate],
  );

  async function handlePreprocessSelected() {
    if (!selectedCandidate?.id) {
      return;
    }

    setPreprocessStatus('Generating structured CSV and Excel outputs for this candidate...');

    try {
      const result = await preprocessCandidate(selectedCandidate.id);
      setPreprocessStatus(`Preprocessing complete. Files are saved in ${result.exports.directory}.`);
    } catch (error) {
      setPreprocessStatus(error.message || 'Failed to preprocess candidate.');
    }
  }

  return (
    <section className="page-grid">
      <section className="summary-strip reveal">
        <article className="summary-tile">
          <p>Total Candidates</p>
          <strong>{candidates.length}</strong>
        </article>
        <article className="summary-tile">
          <p>Analyzed</p>
          <strong>{candidates.filter((item) => item.status === 'completed').length}</strong>
        </article>
        <article className="summary-tile">
          <p>Pending/Processing</p>
          <strong>{candidates.filter((item) => item.status !== 'completed').length}</strong>
        </article>
      </section>

      <div className="candidate-layout reveal delay-1">
        <article className="panel">
          <h2>Candidate List</h2>
          <button type="button" className="btn" onClick={refreshCandidates}>Refresh</button>

          {loading && <p>Loading candidates...</p>}
          {candidatesError && <p className="error-text">{candidatesError}</p>}
          {!loading && candidates.length === 0 && <p>No parsed candidates found yet.</p>}

          <ul className="candidate-list">
            {candidates.map((candidate) => (
              <li
                key={candidate.id}
                className={`candidate-item ${selectedId === candidate.id ? 'selected' : ''}`}
                onClick={() => selectCandidate(candidate.id)}
              >
                <strong>{candidate.full_name || candidate.filename}</strong>
                <div className="muted small-text">
                  {candidate.filename}
                  <br />
                  Status: {candidate.status}
                  {activeAnalyses[candidate.id] && <span className="busy-tag"> (Processing...)</span>}
                </div>
              </li>
            ))}
          </ul>
        </article>

        <article className="panel">
          {detailLoading && <p>Loading candidate details...</p>}
          {!selectedCandidate && !detailLoading && (
            <div className="empty-insight">
              <h3>Select a candidate to open organized insights</h3>
              <p className="muted">Once selected, this area shows all sections in one place: education, research, experience, and missing information draft.</p>
              <div className="insight-grid">
                <article className="placeholder-card">
                  <h4>Education</h4>
                  <p className="muted small-text">Degrees, score/CGPA hints, school-to-university continuity, and gap windows.</p>
                </article>
                <article className="placeholder-card">
                  <h4>Research</h4>
                  <p className="muted small-text">Publication, indexing, collaboration, and topic signals extracted from parsed text.</p>
                </article>
                <article className="placeholder-card">
                  <h4>Experience</h4>
                  <p className="muted small-text">Employment timeline markers plus teaching and industry indicators.</p>
                </article>
                <article className="placeholder-card">
                  <h4>Missing Information</h4>
                  <p className="muted small-text">Auto-detected missing profile fields with personalized email draft.</p>
                </article>
              </div>
            </div>
          )}

          {selectedCandidate && !detailLoading && (
            <div className="page-grid">
              <section className="info-box">
                <h3>Profile Summary</h3>
                <p><strong>Name:</strong> {selectedCandidate.full_name || '—'}</p>
                <p><strong>Email:</strong> {selectedCandidate.email || '—'}</p>
                <p><strong>Phone:</strong> {selectedCandidate.phone || '—'}</p>
                <p><strong>LinkedIn:</strong> {selectedCandidate.linkedin_url || '—'}</p>
                <p><strong>Overall Score:</strong> {selectedCandidate.overall_score ?? '—'}</p>
                <p><strong>Summary:</strong> {selectedCandidate.overall_summary || 'Not generated yet.'}</p>
                <button
                  type="button"
                  className="btn"
                  onClick={onAnalyzeSelected}
                  disabled={activeAnalyses[selectedCandidate.id]}
                >
                  {activeAnalyses[selectedCandidate.id] ? 'Analyzing...' : 'Run/Refresh LLM Analysis'}
                </button>
                <button type="button" className="btn" onClick={handlePreprocessSelected} style={{ marginLeft: 12 }}>
                  Generate Structured Preprocessing
                </button>
                {preprocessStatus && <p className="status-spacing small-text">{preprocessStatus}</p>}
              </section>

              <section className="info-box">
                <h3>Education</h3>
                <p><strong>Detected Degrees:</strong> {education.detectedDegrees.join(', ') || 'None detected'}</p>
                <p><strong>School Data:</strong> {education.hasSchoolData ? 'Yes' : 'No'}</p>
                <p><strong>University Data:</strong> {education.hasUniversityData ? 'Yes' : 'No'}</p>
                <p><strong>Score/CGPA Data:</strong> {education.hasScoreData ? 'Yes' : 'No'}</p>
                <p><strong>Potential Gaps:</strong> {education.gapHints.join(' | ') || 'No major gaps detected'}</p>
              </section>

              <section className="info-box">
                <h3>Research</h3>
                <p><strong>Publication Mentions:</strong> {research.publicationHints}</p>
                <p><strong>Indexing Signals:</strong> {research.indexingHints.join(', ') || 'None detected'}</p>
                <p><strong>Collaboration Signals:</strong> {research.collaborationHints.join(', ') || 'None detected'}</p>
                <p><strong>Topic Signals:</strong> {research.topicHints.join(', ') || 'None detected'}</p>
              </section>

              <section className="info-box">
                <h3>Experience and Skills</h3>
                <p><strong>Employment Evidence:</strong> {experience.hasEmploymentEvidence ? 'Yes' : 'No'}</p>
                <p><strong>Teaching Evidence:</strong> {experience.hasTeachingEvidence ? 'Yes' : 'No'}</p>
                <p><strong>Industry Evidence:</strong> {experience.hasIndustryEvidence ? 'Yes' : 'No'}</p>
                <p><strong>Timeline Years:</strong> {experience.timelineHints.join(', ') || 'None detected'}</p>
              </section>

              <section className="info-box">
                <h3>Missing Information</h3>
                <p><strong>Missing Fields:</strong> {missingFields.join(', ') || 'No key fields missing'}</p>
                {missingFields.length > 0 && (
                  <pre className="email-draft">{draftMissingInfoEmail(selectedCandidate, missingFields)}</pre>
                )}
              </section>

              <section className="raw-box">
                <h3>Raw Parsed Text</h3>
                <p>{selectedCandidate.raw_text || 'No raw text available.'}</p>
              </section>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}