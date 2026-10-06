import api from './api';

/**
 * Turn an axios error into a readable message.
 * FastAPI validation errors (422) arrive as a list of { loc, msg } objects.
 */
export function describeApiError(error) {
  if (!error.response) {
    return 'Cannot reach the prediction API. Make sure the backend is running on port 8000.';
  }
  const { status, data } = error.response;
  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((d) => `${d.loc?.[d.loc.length - 1] ?? 'input'}: ${d.msg}`)
      .join(' • ');
  }
  return data?.detail || `Request failed (HTTP ${status}).`;
}

// No mock fallbacks: if the backend fails, callers receive the error and show it to the user.
export const crimeService = {
  /** Predict the most likely crime type (primary_type) for an incident context */
  async predictCrime(payload) {
    const response = await api.post('/api/predict', payload);
    return response.data;
  },

  /** Final model metrics recorded by notebooks 11-13 */
  async getModelInfo() {
    const response = await api.get('/api/model/info');
    return response.data;
  },

  async getOverviewStats() {
    const response = await api.get('/api/stats/overview');
    return response.data;
  },

  async getCrimeTrends() {
    const response = await api.get('/api/stats/trends');
    return response.data;
  },

  async getHotspotAreas() {
    const response = await api.get('/api/stats/hotspots');
    return response.data;
  },

  async getRecentIncidents() {
    const response = await api.get('/api/incidents/recent');
    return response.data;
  }
};
