const API_BASE_URL = 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const recordPageVisit = async (pageId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/pages/${pageId}/visit`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return await response.json();
  } catch (error) {
    console.error('Error recording page visit:', error);
  }
};

export const updatePageTime = async (pageId, timeSeconds) => {
  try {
    const response = await fetch(`${API_BASE_URL}/pages/${pageId}/time`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ time_seconds: timeSeconds }),
    });
    return await response.json();
  } catch (error) {
    console.error('Error updating page time:', error);
  }
};

export const getAllKPI = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/kpi`, {
      headers: getAuthHeaders(),
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching KPI data:', error);
    return [];
  }
};
