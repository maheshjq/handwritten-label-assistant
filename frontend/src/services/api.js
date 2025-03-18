import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';
// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * Fetches available models from the API
 */
export const fetchAvailableModels = async () => {
  try {
    const response = await api.get('/models');
    return response.data;
  } catch (error) {
    console.error('Error fetching models:', error);
    throw error;
  }
};

/**
 * Recognizes handwriting in an uploaded image
 * @param {FormData} formData - Form data with file and options
 */
export const recognizeHandwriting = async (formData) => {
  try {
    const response = await api.post('/recognition/recognize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error recognizing handwriting:', error);
    throw error;
  }
};

/**
 * Recognizes handwriting from a base64 encoded image
 * @param {string} imageBase64 - Base64 encoded image
 * @param {object} options - Recognition options
 */
export const recognizeHandwritingBase64 = async (imageBase64, options = {}) => {
  try {
    const response = await api.post('/recognition/recognize/base64', {
      image_base64: imageBase64,
      ...options
    });
    return response.data;
  } catch (error) {
    console.error('Error recognizing handwriting:', error);
    throw error;
  }
};

/**
 * Submits human review corrections
 * @param {FormData} formData - Form data with corrections
 */
export const submitHumanReview = async (formData) => {
  try {
    const response = await api.post('/recognition/human-review', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error submitting human review:', error);
    throw error;
  }
};

/**
 * Tests a model with a simple text prompt
 * @param {string} modelName - Name of the model to test
 * @param {string} text - Text to process
 */
export const testModel = async (modelName, text) => {
  try {
    const response = await api.post('/models/test', {
      model_name: modelName,
      text
    });
    return response.data;
  } catch (error) {
    console.error('Error testing model:', error);
    throw error;
  }
};

export default api;
