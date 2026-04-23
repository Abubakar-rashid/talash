import { useEffect, useMemo, useState } from 'react';
import {
  detectMissingInformation,
  draftMissingInfoEmail,
  extractEducationSignals,
  extractExperienceSignals,
  extractResearchSignals,
} from '../lib/profileParsers';
import {
  getCandidateAnalysis,
  preprocessCandidate,
  redraftCandidateEmail,
  runFullCandidateAnalysis,
} from '../lib/api';

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
  const [analysisStatus, setAnalysisStatus] = useState('');
  const [storedAnalysis, setStoredAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

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

  const resolvedMissingFields = storedAnalysis?.missing_fields?.length
    ? storedAnalysis.missing_fields
    : missingFields;

  const resolvedEmailDraft = storedAnalysis?.draft_email?.trim()
    ? storedAnalysis.draft_email
    : draftMissingInfoEmail(selectedCandidate, resolvedMissingFields);

  useEffect(() => {
    async function loadStoredAnalysis() {
      if (!selectedCandidate?.id) {
        setStoredAnalysis(null);
        return;
      }

      setAnalysisLoading(true);
      try {
        const analysis = await getCandidateAnalysis(selectedCandidate.id);
        setStoredAnalysis(analysis);
      } catch {
        setStoredAnalysis(null);
      } finally {
        setAnalysisLoading(false);
      }
    }

    loadStoredAnalysis();
  }, [selectedCandidate?.id]);

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

  async function handleRunFullAnalysis() {
    if (!selectedCandidate?.id) {
      return;
    }

    setAnalysisStatus('Running full backend analysis (education, experience, research, missing info)...');
    try {
      await runFullCandidateAnalysis(selectedCandidate.id);
      const analysis = await getCandidateAnalysis(selectedCandidate.id);
      setStoredAnalysis(analysis);
      setAnalysisStatus('Full backend analysis completed and loaded.');
    } catch (error) {
      setAnalysisStatus(error.message || 'Failed to run full backend analysis.');
    }
  }

  async function handleRedraftEmail() {
    if (!selectedCandidate?.id) {
      return;
    }

    setAnalysisStatus('Generating personalized draft email from backend...');
    try {
      await redraftCandidateEmail(selectedCandidate.id);
      const analysis = await getCandidateAnalysis(selectedCandidate.id);
      setStoredAnalysis(analysis);
      setAnalysisStatus('Draft email refreshed from backend analysis.');
    } catch (error) {
      setAnalysisStatus(error.message || 'Failed to redraft email.');
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
                <button type="button" className="btn" onClick={handleRunFullAnalysis} style={{ marginLeft: 12 }}>
                  Run Full Backend Analysis
                </button>
                <button type="button" className="btn" onClick={handleRedraftEmail} style={{ marginLeft: 12 }}>
                  Refresh Draft Email
                </button>
                {analysisLoading && <p className="status-spacing small-text">Loading stored backend analysis...</p>}
                {analysisStatus && <p className="status-spacing small-text">{analysisStatus}</p>}
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
                {!!storedAnalysis?.experience?.timeline_checks && (
                  <>
                    <p><strong>Education-Employment Overlaps:</strong> {storedAnalysis.experience.timeline_checks.education_employment_overlaps?.length || 0}</p>
                    <p><strong>Job-Job Overlaps:</strong> {storedAnalysis.experience.timeline_checks.job_overlaps?.length || 0}</p>
                    <p><strong>Professional Gaps:</strong> {storedAnalysis.experience.timeline_checks.professional_gaps?.length || 0}</p>
                    <p><strong>Progression Signal:</strong> {storedAnalysis.experience.timeline_checks.progression_signal || 'n/a'}</p>
                  </>
                )}
              </section>

              <section className="info-box">
                <h3>Missing Information</h3>
                <p><strong>Missing Fields:</strong> {resolvedMissingFields.join(', ') || 'No key fields missing'}</p>
                {resolvedMissingFields.length > 0 && (
                  <pre className="email-draft">{resolvedEmailDraft}</pre>
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