import { useEffect, useMemo, useState } from 'react';
import './App.css';
import { analyzeCandidate, getCandidateById, listCandidates } from './lib/api';
import OverviewPage from './pages/OverviewPage';
import IngestionPage from './pages/IngestionPage';
import CandidateInsightsPage from './pages/CandidateInsightsPage';
import AnalyticsReportsPage from './pages/AnalyticsReportsPage';

const ROUTES = [
  {
    id: 'overview',
    label: 'Overview',
    title: 'Project Overview',
    description: 'System status and milestone-aligned quick controls.',
    component: OverviewPage,
  },
  {
    id: 'ingestion',
    label: 'CV Ingestion',
    title: 'Single/Bulk/Folder CV Upload',
    description: 'Upload one CV, multiple CVs, folder PDFs, or parse a server-side filename.',
    component: IngestionPage,
  },
  {
    id: 'insights',
    label: 'Candidate Insights',
    title: 'Parsed and Researched Candidate Information',
    description: 'All candidate sections in one place: Education, Research, Experience, Missing Info, and Summary.',
    component: CandidateInsightsPage,
  },
  {
    id: 'reports',
    label: 'Reports & Emails',
    title: 'Tabular Outputs, Charts, and Draft Emails',
    description: 'Review candidate tables, initial charts, and personalized missing-information draft emails.',
    component: AnalyticsReportsPage,
  },
];

function readHashRoute() {
  const raw = window.location.hash.replace('#/', '');
  return ROUTES.some((route) => route.id === raw) ? raw : 'overview';
}

function App() {
  const [activeRoute, setActiveRoute] = useState(readHashRoute);
  const [candidates, setCandidates] = useState([]);
  const [loadingCandidates, setLoadingCandidates] = useState(true);
  const [candidatesError, setCandidatesError] = useState('');

  const [selectedCandidateId, setSelectedCandidateId] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [activeAnalyses, setActiveAnalyses] = useState({});

  const activeRouteMeta = useMemo(
    () => ROUTES.find((route) => route.id === activeRoute) || ROUTES[0],
    [activeRoute],
  );

  const ActivePage = activeRouteMeta.component;

  useEffect(() => {
    const handleHashChange = () => {
      setActiveRoute(readHashRoute());
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);

  useEffect(() => {
    refreshCandidates();
  }, []);

  async function refreshCandidates() {
    setLoadingCandidates(true);
    setCandidatesError('');

    try {
      const items = await listCandidates();
      setCandidates(items);

      if (selectedCandidateId && !items.some((candidate) => candidate.id === selectedCandidateId)) {
        setSelectedCandidateId(null);
        setSelectedCandidate(null);
      }
    } catch (error) {
      setCandidatesError(error.message || 'Failed to fetch candidate records');
    } finally {
      setLoadingCandidates(false);
    }
  }

  async function selectCandidate(candidateId) {
    setSelectedCandidateId(candidateId);
    setLoadingDetails(true);

    try {
      const details = await getCandidateById(candidateId);
      setSelectedCandidate(details);
    } catch (error) {
      setCandidatesError(error.message || 'Failed to load candidate details');
      setSelectedCandidate(null);
    } finally {
      setLoadingDetails(false);
    }
  }

  async function runAnalysisForSelectedCandidate() {
    if (!selectedCandidateId) {
      return;
    }

    setActiveAnalyses((prev) => ({ ...prev, [selectedCandidateId]: true }));

    try {
      await analyzeCandidate(selectedCandidateId);
      await refreshCandidates();
      await selectCandidate(selectedCandidateId);
    } catch (error) {
      setCandidatesError(error.message || 'Failed to analyze candidate');
    } finally {
      setActiveAnalyses((prev) => ({ ...prev, [selectedCandidateId]: false }));
    }
  }

  function navigate(routeId) {
    window.location.hash = `/${routeId}`;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">CS 417 Spring 2026</p>
          <h1>TALASH</h1>
          <p className="muted">Talent Acquisition & Learning Automation for Smart Hiring</p>
        </div>

        <nav className="nav-list" aria-label="Main navigation">
          {ROUTES.map((route) => (
            <button
              key={route.id}
              type="button"
              className={`nav-item ${activeRoute === route.id ? 'active' : ''}`}
              onClick={() => navigate(route.id)}
            >
              {route.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="content">
        <header className="page-header reveal">
          <h2>{activeRouteMeta.title}</h2>
          <p>{activeRouteMeta.description}</p>
          {candidatesError && <p className="error-text">{candidatesError}</p>}
        </header>

        <ActivePage
          candidates={candidates}
          loading={loadingCandidates}
          refreshCandidates={refreshCandidates}
          selectedCandidate={selectedCandidate}
          selectedCandidateId={selectedCandidateId}
          detailLoading={loadingDetails}
          selectCandidate={selectCandidate}
          onAnalyzeSelected={runAnalysisForSelectedCandidate}
          activeAnalyses={activeAnalyses}
          candidatesError={candidatesError}
          onUploaded={refreshCandidates}
        />
      </main>
    </div>
  );
}

export default App;
