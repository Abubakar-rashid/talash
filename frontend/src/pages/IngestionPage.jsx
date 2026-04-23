import { useMemo, useState } from 'react';
import {
  ingestCandidateFolder,
  parseCandidateByFilename,
  uploadCandidateCV,
  uploadCandidateCVBulk,
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

  const totalQueued = useMemo(
    () => (singleFile ? 1 : 0) + bulkFiles.length + folderFiles.length,
    [singleFile, bulkFiles.length, folderFiles.length],
  );

  async function uploadOne(file) {
    const result = await uploadCandidateCV(file);
    return result?.filename || file.name;
  }

  async function uploadMany(files, label) {
    if (!files.length) {
      setStatus(`No PDF files selected for ${label}.`);
      return;
    }

    setRunning(true);
    setStatus(`Uploading ${files.length} file(s) from ${label}...`);

    try {
      const result = await uploadCandidateCVBulk(files);
      setStatus(
        `Uploaded ${result.processed}/${result.total_received} file(s) from ${label}. Failed: ${result.failed}.`,
      );
      await refreshCandidates?.();
    } catch (error) {
      setStatus(`Bulk upload failed: ${error.message}`);
    } finally {
      setRunning(false);
    }
  }

  async function handleServerFolderIngest() {
    if (!serverFolderPath.trim()) {
      setStatus('Please provide a valid server folder path.');
      return;
    }

    setRunning(true);
    setStatus(`Reading and parsing PDFs from server folder: ${serverFolderPath} ...`);

    try {
      const result = await ingestCandidateFolder(serverFolderPath.trim(), deleteAfterFolderParse);
      setStatus(
        `Folder ingestion complete. Processed ${result.processed}/${result.total_found}. Failed: ${result.failed}.`,
      );
      await refreshCandidates?.();
    } catch (error) {
      setStatus(`Folder ingestion failed: ${error.message}`);
    } finally {
      setRunning(false);
    }
  }

  async function handleSingleUpload() {
    if (!singleFile) {
      setStatus('Please select a single PDF first.');
      return;
    }

    setRunning(true);
    try {
      const name = await uploadOne(singleFile);
      setStatus(`Single CV uploaded successfully: ${name}`);
      setSingleFile(null);
      await refreshCandidates?.();
    } catch (error) {
      setStatus(`Single upload failed: ${error.message}`);
    } finally {
      setRunning(false);
    }
  }

  async function handleParseExisting() {
    if (!serverFilename.trim()) {
      setStatus('Enter a PDF filename available on backend uploads folder.');
      return;
    }

    setRunning(true);
    try {
      const result = await parseCandidateByFilename(serverFilename.trim());
      setStatus(`Parsed existing file successfully: ${result.filename}`);
      setServerFilename('');
      await refreshCandidates?.();
    } catch (error) {
      setStatus(`Parse failed: ${error.message}`);
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="page-grid two-columns">
      <article className="panel reveal">
        <h2>CV Ingestion</h2>
        <p className="muted">Use one place for single upload, bulk upload, folder upload, and parsing existing uploaded files.</p>

        <div className="upload-card">
          <h3>Single CV Upload</h3>
          <div className="upload-row">
            <input
              type="file"
              accept=".pdf"
              onChange={(event) => setSingleFile(event.target.files?.[0] || null)}
              disabled={running}
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
            />
            <button className="btn compact" type="button" onClick={handleParseExisting} disabled={running || !serverFilename.trim()}>
              Parse Existing File
            </button>
          </div>
          <p className="hint-text">Use this only when a PDF already exists in backend uploads folder.</p>
        </div>

        <p className="muted small-text">Total currently selected files: {totalQueued}</p>
        {status && <p className={status.toLowerCase().includes('failed') ? 'error-text' : 'success-text'}>{status}</p>}
      </article>
    </section>
  );
}
