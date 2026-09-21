import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export const getDisagreements = async (params = {}) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/disagreements/`, { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching disagreements:', error);
    throw error;
  }
};

export const getDisagreement = async (id) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/disagreements/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching disagreement:', error);
    throw error;
  }
};