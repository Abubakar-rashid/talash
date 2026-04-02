import React, { useState, useEffect } from 'react';

export default function CandidateDashboard() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [activeAnalyses, setActiveAnalyses] = useState({});

  // Fetch all candidates on mount
  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/cv/candidates");
      if (!response.ok) throw new Error("Failed to fetch candidates");
      const data = await response.json();
      setCandidates(data.candidates);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRowClick = async (id) => {
    setDetailsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/cv/candidate/${id}`);
      if (!response.ok) throw new Error("Failed to fetch candidate details");
      const data = await response.json();
      setSelectedCandidate(data);
    } catch (err) {
      alert(err.message);
    } finally {
      setDetailsLoading(false);
    }
  };

  const analyzeSelectedCandidate = async () => {
    const idToAnalyze = selectedCandidate?.id;
    if (!idToAnalyze) return;

    setActiveAnalyses(prev => ({ ...prev, [idToAnalyze]: true }));
    
    // Optimistically update status to show processing
    setCandidates(prev => prev.map(c => 
      c.id === idToAnalyze ? { ...c, status: 'processing' } : c
    ));
    setSelectedCandidate(prev => prev?.id === idToAnalyze ? { ...prev, status: 'processing' } : prev);

    try {
      const response = await fetch(
        `http://localhost:8000/cv/candidate/${idToAnalyze}/analyze`,
        { method: "POST" }
      );

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to analyze candidate");
      }

      await fetchCandidates();
      
      // If we are still looking at the one that just finished, refresh its data completely
      // We do a fresh fetch to ensure we don't end up with stale closures
      const detailResponse = await fetch(`http://localhost:8000/cv/candidate/${idToAnalyze}`);
      if (detailResponse.ok) {
        const detailData = await detailResponse.json();
        // Only override if the user hasn't clicked away during the wait
        setSelectedCandidate(current => current?.id === idToAnalyze ? detailData : current);
      }
      
      alert("Analysis complete and saved to database.");
    } catch (err) {
      alert(err.message);
    } finally {
      setActiveAnalyses(prev => ({ ...prev, [idToAnalyze]: false }));
    }
  };

  return (
    <div style={{ display: 'flex', gap: '20px', width: '100%', maxWidth: '1000px', margin: '0 auto', textAlign: 'left' }}>
      
      {/* Left side: List of candidates */}
      <div style={{ flex: '1', border: '1px solid var(--border)', borderRadius: '8px', padding: '15px', maxHeight: '600px', overflowY: 'auto' }}>
        <h2>Database Entries</h2>
        <button onClick={fetchCandidates} style={{ marginBottom: '15px' }}>Refresh</button>
        
        {loading && <p>Loading candidates...</p>}
        {error && <p style={{ color: 'red' }}>{error}</p>}
        
        {!loading && candidates.length === 0 && <p>No CVs found in database.</p>}
        
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {candidates.map((c) => (
            <li 
              key={c.id} 
              onClick={() => handleRowClick(c.id)}
              style={{ 
                padding: '10px', 
                borderBottom: '1px solid var(--border)', 
                cursor: 'pointer',
                backgroundColor: selectedCandidate?.id === c.id ? 'var(--accent-bg)' : 'transparent',
                borderRadius: '4px'
              }}
            >
              <strong>{c.filename} {activeAnalyses[c.id] && <span style={{ color: 'var(--accent)', fontSize: '12px' }}>(Processing...)</span>}</strong>
              <div style={{ fontSize: '14px', color: 'var(--text)' }}>
                Status: {c.status} <br/>
                ID: {c.id}
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Right side: Detailed view of parsed text */}
      <div style={{ flex: '2', border: '1px solid var(--border)', borderRadius: '8px', padding: '15px', maxHeight: '600px', overflowY: 'auto' }}>
        {detailsLoading && <p>Loading details...</p>}
        
        {!selectedCandidate && !detailsLoading && (
          <p style={{ color: 'var(--text)', textAlign: 'center', marginTop: '100px' }}>
            Select a candidate from the left to view parsed text.
          </p>
        )}

        {selectedCandidate && !detailsLoading && (
          <div>
            <h2>Parsed parsed Info: {selectedCandidate.filename}</h2>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '15px', fontSize: '14px' }}>
              <span style={{ padding: '4px 8px', background: 'var(--accent-bg)', borderRadius: '4px' }}>
                ID: {selectedCandidate.id}
              </span>
              <span style={{ padding: '4px 8px', background: 'var(--code-bg)', borderRadius: '4px' }}>
                Status: {selectedCandidate.status}
              </span>
            </div>

            <button
              onClick={analyzeSelectedCandidate}
              disabled={activeAnalyses[selectedCandidate.id]}
              style={{ marginBottom: '15px' }}
            >
              {activeAnalyses[selectedCandidate.id] ? 'Analyzing with Groq...' : 'Analyze with Groq and Save'}
            </button>

            <h3>Structured Profile:</h3>
            <div style={{ background: 'var(--code-bg)', padding: '15px', borderRadius: '8px', marginBottom: '15px' }}>
              <p><strong>Full Name:</strong> {selectedCandidate.full_name || '—'}</p>
              <p><strong>Email:</strong> {selectedCandidate.email || '—'}</p>
              <p><strong>Phone:</strong> {selectedCandidate.phone || '—'}</p>
              <p><strong>LinkedIn:</strong> {selectedCandidate.linkedin_url || '—'}</p>
              <p><strong>Nationality:</strong> {selectedCandidate.nationality || '—'}</p>
              <p><strong>Overall Score:</strong> {selectedCandidate.overall_score ?? '—'}</p>
              <p><strong>Summary:</strong> {selectedCandidate.overall_summary || '—'}</p>
            </div>
            
            <h3>Raw Parsed Text:</h3>
            <div style={{ 
              background: 'var(--code-bg)', 
              padding: '15px', 
              borderRadius: '8px', 
              whiteSpace: 'pre-wrap', 
              wordBreak: 'break-word',
              fontFamily: 'var(--mono)',
              fontSize: '13px'
            }}>
              {selectedCandidate.raw_text || "No text parsed / extracted."}
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
