import axios from 'axios';

const API_URL = '/api';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const recognitionService = {
  recognizeImage: async (formData: FormData) => {
    const response = await apiClient.post('/recognition/recognize', formData);
    return response.data;
  },
  
  getRecognitionHistory: async () => {
    const response = await apiClient.get('/recognition/history');
    return response.data;
  },
  
  submitHumanReview: async (workflowId: string, corrections: any) => {
    const response = await apiClient.post(`/recognition/human-review`, {
      workflow_id: workflowId,
      ...corrections
    });
    return response.data;
  }
};

export const modelService = {
  getAvailableModels: async () => {
    const response = await apiClient.get('/models');
    return response.data;
  },
  
  testModel: async (modelName: string, text: string) => {
    const response = await apiClient.post('/models/test', {
      model_name: modelName,
      text
    });
    return response.data;
  }
};

export default apiClient;
