import { useMemo, useState } from 'react';
import {
  ingestCandidateFolder,
  parseCandidateByFilename,
  uploadCandidateCV,
} from '../lib/api';

function pickPdfFiles(fileList) {
  return Array.from(fileList || []).filter((file) => file.name.toLowerCase().endsWith('.pdf'));
}

export default function IngestionPage({ refreshCandidates }) {
  const [singleFile, setSingleFile] = useState(null);
  const [bulkFiles, setBulkFiles] = useState([]);
  const [folderFiles, setFolderFiles] = useState([]);
  const [serverFilename, setServerFilename] = useState('');
  const [serverFolderPath, setServerFolderPath] = useState('uploads');
  const [deleteAfterFolderParse, setDeleteAfterFolderParse] = useState(false);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);

  const totalQueued = useMemo(
    () => (singleFile ? 1 : 0) + bulkFiles.length + folderFiles.length,
    [singleFile, bulkFiles.length, folderFiles.length],
  );

  function emit(message, variant = 'info') {
    if (typeof window !== 'undefined' && typeof window.__talashNotify === 'function') {
      window.__talashNotify(message, variant);
    }
  }

  function setQueuedFiles(files) {
    const pdfFiles = pickPdfFiles(files);
    if (pdfFiles.length === 1) {
      setSingleFile(pdfFiles[0]);
      setBulkFiles([]);
      setFolderFiles([]);
    } else if (pdfFiles.length > 1) {
      setBulkFiles(pdfFiles);
      setSingleFile(null);
      setFolderFiles([]);
    }
  }

  async function uploadOne(file) {
    const result = await uploadCandidateCV(file);
    return result?.filename || file.name;
  }

  async function uploadMany(files, label) {
    if (!files.length) {
      setStatus(`No PDF files selected for ${label}.`);
      emit(`No PDF files selected for ${label}.`, 'error');
      return;
    }

    setRunning(true);
    setProgress(5);
    setStatus(`Uploading ${files.length} file(s) from ${label}...`);

    try {
      let processed = 0;
      let failed = 0;

      for (const file of files) {
        try {
          await uploadOne(file);
          processed += 1;
        } catch {
          failed += 1;
        }
        setProgress(Math.round((processed + failed) / files.length * 100));
      }

      setStatus(`Uploaded ${processed}/${files.length} file(s) from ${label}. Failed: ${failed}.`);
      emit(`Uploaded ${processed}/${files.length} PDF(s).`, failed ? 'error' : 'success');
      await refreshCandidates?.();
    } catch (error) {
      setStatus(`Bulk upload failed: ${error.message}`);
      emit(`Bulk upload failed: ${error.message}`, 'error');
    } finally {
      setRunning(false);
      setProgress(0);
    }
  }

  async function handleServerFolderIngest() {
    if (!serverFolderPath.trim()) {
      setStatus('Please provide a valid server folder path.');
      return;
    }

    setRunning(true);
    setProgress(10);
    setStatus(`Reading and parsing PDFs from server folder: ${serverFolderPath} ...`);

    try {
      const result = await ingestCandidateFolder(serverFolderPath.trim(), deleteAfterFolderParse);
      setStatus(
        `Folder ingestion complete. Processed ${result.processed}/${result.total_found}. Failed: ${result.failed}.`,
      );
      emit(`Folder ingestion complete: ${result.processed}/${result.total_found}.`, result.failed ? 'error' : 'success');
      await refreshCandidates?.();
    } catch (error) {
      setStatus(`Folder ingestion failed: ${error.message}`);
      emit(`Folder ingestion failed: ${error.message}`, 'error');
    } finally {
      setRunning(false);
      setProgress(0);
    }
  }

  async function handleSingleUpload() {
    if (!singleFile) {
      setStatus('Please select a single PDF first.');
      return;
    }

    setRunning(true);
    setProgress(15);
    try {
      const name = await uploadOne(singleFile);
      setStatus(`Single CV uploaded successfully: ${name}`);
      emit(`Single CV uploaded successfully: ${name}`, 'success');
      setSingleFile(null);
      await refreshCandidates?.();
    } catch (error) {
      setStatus(`Single upload failed: ${error.message}`);
      emit(`Single upload failed: ${error.message}`, 'error');
    } finally {
      setRunning(false);
      setProgress(0);
    }
  }

  async function handleParseExisting() {
    if (!serverFilename.trim()) {
      setStatus('Enter a PDF filename available on backend uploads folder.');
      return;
    }

    setRunning(true);
    setProgress(20);
    try {
      const result = await parseCandidateByFilename(serverFilename.trim());
      setStatus(`Parsed existing file successfully: ${result.filename}`);
      emit(`Parsed existing file successfully: ${result.filename}`, 'success');
      setServerFilename('');
      await refreshCandidates?.();
    } catch (error) {
      setStatus(`Parse failed: ${error.message}`);
      emit(`Parse failed: ${error.message}`, 'error');
    } finally {
      setRunning(false);
      setProgress(0);
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragActive(false);
    setQueuedFiles(event.dataTransfer.files);
    setStatus('Files dropped. Ready to upload.');
  }

  function handleDragOver(event) {
    event.preventDefault();
    setDragActive(true);
  }

  function handleDragLeave() {
    setDragActive(false);
  }

  return (
    <section className="page-grid two-columns">
      <article className="panel reveal">
        <h2>CV Ingestion</h2>
        <p className="muted">Use one place for single upload, bulk upload, folder upload, and parsing existing uploaded files.</p>

        <div
          className={`drop-zone ${dragActive ? 'active' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          role="button"
          tabIndex={0}
          aria-label="Drop PDF files here to queue them for upload"
        >
          <strong>Drop PDF files here</strong>
          <p className="muted small-text">Drag one PDF to queue a single upload, or drop multiple PDFs to queue bulk upload.</p>
        </div>

        <div className="upload-card">
          <h3>Single CV Upload</h3>
          <div className="upload-row">
            <input
              type="file"
              accept=".pdf"
              onChange={(event) => setSingleFile(event.target.files?.[0] || null)}
              disabled={running}
              aria-label="Choose one PDF file to upload"
            />
            <button className="btn compact" type="button" onClick={handleSingleUpload} disabled={running || !singleFile}>
              Upload Single CV
            </button>
          </div>
        </div>

        <div className="upload-card">
          <h3>Bulk CV Upload</h3>
          <div className="upload-row">
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={(event) => setBulkFiles(pickPdfFiles(event.target.files))}
              disabled={running}
              aria-label="Choose multiple PDF files to upload"
            />
            <button className="btn compact" type="button" onClick={() => uploadMany(bulkFiles, 'bulk selection')} disabled={running || bulkFiles.length === 0}>
              Upload Bulk CVs ({bulkFiles.length})
            </button>
          </div>
        </div>
      </article>

      <article className="panel reveal delay-1">
        <h2>Folder and Existing File Options</h2>
        <p className="muted">Process a full local folder or trigger parsing for an already uploaded server file.</p>

        <div className="upload-card">
          <h3>Select Local Folder</h3>
          <div className="upload-row">
            <input
              type="file"
              accept=".pdf"
              multiple
              webkitdirectory="true"
              directory="true"
              onChange={(event) => setFolderFiles(pickPdfFiles(event.target.files))}
              disabled={running}
              aria-label="Choose a folder of PDF files to upload"
            />
            <button className="btn compact" type="button" onClick={() => uploadMany(folderFiles, 'folder selection')} disabled={running || folderFiles.length === 0}>
              Upload Folder PDFs ({folderFiles.length})
            </button>
          </div>
        </div>

        <div className="upload-card">
          <h3>Ingest PDFs from Server Folder Path</h3>
          <div className="upload-row">
            <input
              type="text"
              value={serverFolderPath}
              onChange={(event) => setServerFolderPath(event.target.value)}
              placeholder="uploads"
              disabled={running}
              className="text-input"
              aria-label="Server folder path"
            />
            <button
              className="btn compact"
              type="button"
              onClick={handleServerFolderIngest}
              disabled={running || !serverFolderPath.trim()}
            >
              Ingest Server Folder
            </button>
          </div>
          <label className="muted small-text" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={deleteAfterFolderParse}
              onChange={(event) => setDeleteAfterFolderParse(event.target.checked)}
              disabled={running}
            />
            Delete PDFs after parse
          </label>
        </div>

        <div className="upload-card">
          <h3>Parse File Already on Server</h3>
          <div className="upload-row">
            <input
              type="text"
              value={serverFilename}
              onChange={(event) => setServerFilename(event.target.value)}
              placeholder="example_cv.pdf"
              disabled={running}
              className="text-input"
              aria-label="Filename already on server"
            />
            <button className="btn compact" type="button" onClick={handleParseExisting} disabled={running || !serverFilename.trim()}>
              Parse Existing File
            </button>
          </div>
          <p className="hint-text">Use this only when a PDF already exists in backend uploads folder.</p>
        </div>

        <p className="muted small-text">Total currently selected files: {totalQueued}</p>
        {running && (
          <div className="progress-block" aria-label="Upload progress">
            <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
            <p className="muted small-text">{progress > 0 ? `Processing... ${progress}%` : 'Processing...'}</p>
          </div>
        )}
        {status && <p className={status.toLowerCase().includes('failed') ? 'error-text' : 'success-text'}>{status}</p>}
      </article>
    </section>
  );
}
