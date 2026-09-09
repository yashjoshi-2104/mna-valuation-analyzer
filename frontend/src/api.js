const BASE = 'http://127.0.0.1:8000/api';

async function get(path, { timeout = 8000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(`${BASE}${path}`, { signal: controller.signal });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${res.status}): ${path}`);
    }
    return await res.json();
  } catch (e) {
    if (e.name === 'AbortError') throw new Error(`Timed out reaching ${path}`);
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

async function post(path, body, { timeout = 60000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) {
      const respBody = await res.json().catch(() => ({}));
      throw new Error(respBody.detail || `Request failed (${res.status}): ${path}`);
    }
    return await res.json();
  } catch (e) {
    if (e.name === 'AbortError') throw new Error(`Timed out reaching ${path}`);
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Streams a chat reply as plain-text chunks, calling onChunk(text) as each
 * piece arrives. This is what makes the AI Analyst feel responsive - the
 * first tokens typically show up in ~1-2s instead of waiting for the whole
 * answer to finish generating before anything appears.
 */
async function postStream(path, body, onChunk, { timeout = 120000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok || !res.body) {
      const respBody = await res.json().catch(() => ({}));
      throw new Error(respBody.detail || `Request failed (${res.status}): ${path}`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let full = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value, { stream: true });
      full += text;
      onChunk(text, full);
    }
    return full;
  } catch (e) {
    if (e.name === 'AbortError') throw new Error(`Timed out reaching ${path}`);
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  health: () => get('/health', { timeout: 3000 }),
  listCompanies: () => get('/companies'),
  getCompany: (id) => get(`/companies/${id}`),
  getMetrics: (id) => get(`/companies/${id}/metrics`),
  getComps: (id, topN = 5) => get(`/comps/${id}?top_n=${topN}`),
  listTransactions: () => get('/transactions'),
  transactionsSummary: () => get('/transactions/summary'),
  getValuation: (id, topNPeers = 5) => get(`/valuation/${id}?top_n_peers=${topNPeers}`),
  explainValuation: (id) => get(`/ai/valuation/${id}`),
  chat: (companyId, messages) => post('/ai/chat', { company_id: companyId, messages }, { timeout: 90000 }),
  chatStream: (companyId, messages, onChunk) =>
    postStream('/ai/chat/stream', { company_id: companyId, messages }, onChunk, { timeout: 120000 }),
};
