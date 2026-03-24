import axios from 'axios';
import type { 
  UploadResponse, 
  ProcessResponse, 
  ProcessRequest   // now it will be used
} from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

export const uploadFiles = async (files: File[]): Promise<UploadResponse> => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const res = await api.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const processFiles = async (filenames: string[] = []): Promise<ProcessResponse> => {
  const payload: ProcessRequest = { filenames };
  const res = await api.post<ProcessResponse>('/process', payload);
  return res.data;
};