import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export interface Download {
  id: number;
  filename: string;
  status: 'PENDING' | 'DOWNLOADING' | 'COMPLETED' | 'FAILED' | 'PAUSED';
  progress: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  file_size?: number;
  download_path: string;
}

export interface Tag {
  id: number;
  name: string;
}

export interface UsenetConfig {
  host: string;
  port: number;
  ssl: boolean;
  username: string;
  connections: number;
  retention: number;
}

export interface DownloadsConfig {
  path: string;
  temp_path: string;
  completed_path: string;
  failed_path: string;
}

export interface WebConfig {
  host: string;
  port: number;
}

export interface SystemConfig {
  usenet: UsenetConfig;
  downloads: DownloadsConfig;
  web: WebConfig;
}

// Downloads
export const getDownloads = async (): Promise<Download[]> => {
  const response = await api.get('/downloads/');
  return response.data;
};

export const uploadNzb = async (file: File): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);
  await api.post('/downloads/nzb-file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const pauseDownload = async (id: number): Promise<void> => {
  await api.post(`/queue/${id}/pause`);
};

export const resumeDownload = async (id: number): Promise<void> => {
  await api.post(`/queue/${id}/resume`);
};

export const deleteDownload = async (id: number): Promise<void> => {
  await api.delete(`/queue/${id}`);
};

// Tags
export const getTags = async (): Promise<Tag[]> => {
  const response = await api.get('/tags/');
  return response.data;
};

// System Configuration
export const getSystemConfig = async (): Promise<SystemConfig> => {
  const response = await api.get('/system/config');
  return response.data;
};

export const getUsenetConfig = async (): Promise<UsenetConfig> => {
  const response = await api.get('/system/usenet');
  return response.data;
};

export default api;
