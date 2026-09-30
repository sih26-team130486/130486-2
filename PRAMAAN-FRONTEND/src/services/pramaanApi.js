/**
 * PRAMAAN Frontend API Service
 * Connects the React/Vite UI to the Django REST Framework backend (http://127.0.0.1:8000)
 */

export const API_BASE = 'http://127.0.0.1:8000/api/v1';

class PramaanApiService {
  constructor() {
    this.tokenKey = 'pramaan_jwt_token';
    this.refreshTokenKey = 'pramaan_refresh_token';
    this.userKey = 'pramaan_user';
    this.backendStatus = { online: false, lastChecked: null };
  }

  getToken() {
    return localStorage.getItem(this.tokenKey) || '';
  }

  setToken(access, refresh = null) {
    if (access) localStorage.setItem(this.tokenKey, access);
    if (refresh) localStorage.setItem(this.refreshTokenKey, refresh);
  }

  clearToken() {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.refreshTokenKey);
  }

  /**
   * Health Check: tests if Django server is reachable
   */
  async checkHealth() {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      const res = await fetch('http://127.0.0.1:8000/admin/login/', {
        method: 'GET',
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      const online = res.status < 500;
      this.backendStatus = { online, lastChecked: new Date() };
      return online;
    } catch {
      this.backendStatus = { online: false, lastChecked: new Date() };
      return false;
    }
  }

  /**
   * Internal HTTP Request Wrapper
   */
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = options.headers || {};
    const token = this.getToken();

    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      if (response.status === 401) {
        // Token expired or invalid
        console.warn('PRAMAAN: API 401 Unauthorized - token may be expired');
      }

      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const data = await response.json();
        return { ok: response.ok, status: response.status, data };
      }

      // Non-JSON (e.g. file downloads, raw text)
      const blob = await response.blob();
      return { ok: response.ok, status: response.status, data: blob, headers: response.headers };
    } catch (err) {
      console.error(`PRAMAAN API Error on ${endpoint}:`, err);
      return { ok: false, status: 0, error: err.message, offline: true };
    }
  }

  // -------------------------------------------------------------------------
  // Auth Endpoints
  // -------------------------------------------------------------------------
  async login(username, password) {
    const res = await this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    if (res.ok && res.data.access) {
      this.setToken(res.data.access, res.data.refresh);
      if (res.data.user) {
        localStorage.setItem(this.userKey, JSON.stringify(res.data.user));
      }
    }
    return res;
  }

  async logout() {
    const refreshToken = localStorage.getItem(this.refreshTokenKey);
    if (refreshToken) {
      await this.request('/auth/logout/', {
        method: 'POST',
        body: JSON.stringify({ refresh: refreshToken }),
      });
    }
    this.clearToken();
  }

  async getProfile() {
    return this.request('/auth/profile/');
  }

  // -------------------------------------------------------------------------
  // Document Endpoints
  // -------------------------------------------------------------------------
  async uploadDocument(file, caseId = 'CASE-2026-001', description = '') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('case_id', caseId);
    if (description) formData.append('description', description);

    return this.request('/documents/upload/', {
      method: 'POST',
      body: formData,
    });
  }

  async getDocuments(params = {}) {
    const query = new URLSearchParams(params).toString();
    const endpoint = query ? `/documents/?${query}` : '/documents/';
    return this.request(endpoint);
  }

  async getDocument(docId) {
    return this.request(`/documents/${docId}/`);
  }

  async downloadDocument(docId) {
    return this.request(`/documents/${docId}/download/`);
  }

  // -------------------------------------------------------------------------
  // Verification Endpoints
  // -------------------------------------------------------------------------
  async verifyDocument(docId) {
    return this.request(`/verification/${docId}/verify/`, {
      method: 'POST',
    });
  }

  async getVerifications() {
    return this.request('/verification/');
  }

  // -------------------------------------------------------------------------
  // Audit Logs Endpoints
  // -------------------------------------------------------------------------
  async getAuditLogs(params = {}) {
    const query = new URLSearchParams(params).toString();
    const endpoint = query ? `/audit/?${query}` : '/audit/';
    return this.request(endpoint);
  }

  async getAuditStats() {
    return this.request('/audit/stats/');
  }

  // -------------------------------------------------------------------------
  // Chain of Custody Endpoints
  // -------------------------------------------------------------------------
  async getCustodyChains() {
    return this.request('/custody/');
  }

  async registerCustody(docId, location = 'Cyber Crime Unit, Mumbai') {
    return this.request('/custody/', {
      method: 'POST',
      body: JSON.stringify({ document_id: docId, location }),
    });
  }

  async initiateTransfer(chainId, toUserId, toLocation, reason = '') {
    return this.request(`/custody/${chainId}/transfer/`, {
      method: 'POST',
      body: JSON.stringify({
        to_user_id: toUserId,
        to_location: toLocation,
        transfer_reason: reason,
      }),
    });
  }

  async confirmTransfer(transferId, notes = '') {
    return this.request(`/custody/transfer/${transferId}/confirm/`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  async getCustodyHistory(chainId) {
    return this.request(`/custody/${chainId}/history/`);
  }

  // -------------------------------------------------------------------------
  // Certificates Endpoints
  // -------------------------------------------------------------------------
  async generateCertificate(docId, certType = 'COURT_EXPORT') {
    return this.request('/certificates/generate/', {
      method: 'POST',
      body: JSON.stringify({
        document_id: docId,
        certificate_type: certType,
      }),
    });
  }

  async getCertificates() {
    return this.request('/certificates/');
  }

  async downloadCertificate(certId) {
    return this.request(`/certificates/${certId}/download/`);
  }

  // -------------------------------------------------------------------------
  // PII Redaction Endpoints
  // -------------------------------------------------------------------------
  async detectPII(docId) {
    return this.request('/redaction/detect/', {
      method: 'POST',
      body: JSON.stringify({ document_id: docId }),
    });
  }

  async redactDocument(docId) {
    return this.request('/redaction/redact/', {
      method: 'POST',
      body: JSON.stringify({ document_id: docId }),
    });
  }

  async getRedactionJobs() {
    return this.request('/redaction/');
  }

  // -------------------------------------------------------------------------
  // Search Endpoints
  // -------------------------------------------------------------------------
  async searchDocuments(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/search/documents/?${query}`);
  }
}

export const pramaanApi = new PramaanApiService();
export default pramaanApi;
