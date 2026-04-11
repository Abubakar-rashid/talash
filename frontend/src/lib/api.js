const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload?.detail
        ? payload.detail
        : typeof payload === 'string' && payload
          ? payload
          : 'Request failed';
    throw new Error(detail);
  }

  return payload;
}

export async function listCandidates() {
  const response = await fetch(`${API_BASE_URL}/cv/candidates`);
  const payload = await parseResponse(response);
  return payload?.candidates || [];
}

export async function getCandidateById(candidateId) {
  const response = await fetch(`${API_BASE_URL}/cv/candidate/${candidateId}`);
  return parseResponse(response);
}

export async function uploadCandidateCV(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/cv/upload`, {
    method: 'POST',
    body: formData,
  });

  return parseResponse(response);
}

export async function analyzeCandidate(candidateId) {
  const response = await fetch(`${API_BASE_URL}/cv/candidate/${candidateId}/analyze`, {
    method: 'POST',
  });

  return parseResponse(response);
}

export async function parseCandidateByFilename(filename) {
  const params = new URLSearchParams({ filename });
  const response = await fetch(`${API_BASE_URL}/cv/parse?${params.toString()}`, {
    method: 'POST',
  });

  return parseResponse(response);
}

export { API_BASE_URL };
