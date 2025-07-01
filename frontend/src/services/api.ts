import axios from 'axios';
import { Download, Tag } from '../types/api';
import logger from './logging';

// Create Axios instance with base URL
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  }
});

// Remove withCredentials setting
delete api.defaults.withCredentials;

// Downloads API
export const getDownloads = async (): Promise<Download[]> => {
  try {
    const response = await api.get('/downloads');
    return response.data;
  } catch (error) {
    logger.error('Failed to fetch downloads', error);
    throw error;
  }
};

export const downloadNZB = async (file: File): Promise<void> => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    await api.post('/downloads/nzb', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    logger.info('NZB file uploaded successfully');
  } catch (error) {
    logger.error('Failed to upload NZB file', error);
    throw error;
  }
};

export const pauseDownload = async (id: number): Promise<void> => {
  try {
    await api.post(`/downloads/${id}/pause`);
    logger.info(`Download ${id} paused`);
  } catch (error) {
    logger.error(`Failed to pause download ${id}`, error);
    throw error;
  }
};

export const resumeDownload = async (id: number): Promise<void> => {
  try {
    await api.resumeDownload(id);
    logger.info(`Download ${id} resumed`);
  } catch (error) {
    logger.error(`Failed to resume download ${id}`, error);
    throw error;
  }
};

export const cancelDownload = async (id: number): Promise<void> => {
  try {
    await api.post(`/downloads/${id}/cancel`);
    logger.info(`Download ${id} cancelled`);
  } catch (error) {
    logger.error(`Failed to cancel download ${id}`, error);
    throw error;
  }
};

export const retryDownload = async (id: number): Promise<void> => {
  try {
    await api.post(`/downloads/${id}/retry`);
    logger.info(`Download ${id} retried`);
  } catch (error) {
    logger.error(`Failed to retry download ${id}`, error);
    throw error;
  }
};

// Tags API
export const getTags = async (): Promise<Tag[]> => {
  try {
    const response = await api.get('/tags');
    return response.data;
  } catch (error) {
    logger.error('Failed to fetch tags', error);
    throw error;
  }
};

export const createTag = async (name: string): Promise<Tag> => {
  try {
    const response = await api.post('/tags', { name });
    logger.info(`Tag ${name} created`);
    return response.data;
  } catch (error) {
    logger.error(`Failed to create tag ${name}`, error);
    throw error;
  }
};

export const deleteTag = async (id: number): Promise<void> => {
  try {
    await api.delete(`/tags/${id}`);
    logger.info(`Tag ${id} deleted`);
  } catch (error) {
    logger.error(`Failed to delete tag ${id}`, error);
    throw error;
  }
};

export const updateTag = async (id: number, name: string): Promise<Tag> => {
  try {
    const response = await api.put(`/tags/${id}`, { name });
    logger.info(`Tag ${id} updated to ${name}`);
    return response.data;
  } catch (error) {
    logger.error(`Failed to update tag ${id}`, error);
    throw error;
  }
};

// System API
export const getSystemStatus = async () => {
  try {
    const response = await api.get('/system/status');
    return response.data;
  } catch (error) {
    logger.error('Failed to fetch system status', error);
    throw error;
  }
};
