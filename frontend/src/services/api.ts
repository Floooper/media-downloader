import axios from 'axios';
import { Download, Tag } from '../types/api';
import { logError, logInfo } from './logging';

// Create Axios instance with base URL
const api = axios.create({
    baseURL: '/api',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Add response interceptor for error handling
api.interceptors.response.use(
    response => response,
    error => {
        logError('API request failed:', error);
        return Promise.reject(error);
    }
);

// Typed API functions
export const downloadNZB = async (file: File): Promise<Download> => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await api.post('/downloads/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        logInfo('NZB file uploaded successfully');
        return response.data;
    } catch (error: any) {
        logError('Failed to upload NZB file', error);
        throw error;
    }
};

export const getDownloads = async (): Promise<Download[]> => {
    try {
        const response = await api.get('/downloads');
        return response.data;
    } catch (error: any) {
        logError('Failed to fetch downloads', error);
        throw error;
    }
};

export const getTags = async (): Promise<Tag[]> => {
    try {
        const response = await api.get('/tags');
        return response.data;
    } catch (error: any) {
        logError('Failed to fetch tags', error);
        throw error;
    }
};

export const createTag = async (name: string): Promise<Tag> => {
    try {
        const response = await api.post('/tags', { name });
        logInfo('Tag created successfully');
        return response.data;
    } catch (error: any) {
        logError('Failed to create tag', error);
        throw error;
    }
};

export const updateTag = async (id: number, name: string): Promise<Tag> => {
    try {
        const response = await api.put(`/tags/${id}`, { name });
        logInfo('Tag updated successfully');
        return response.data;
    } catch (error: any) {
        logError('Failed to update tag', error);
        throw error;
    }
};

export const deleteTag = async (id: number): Promise<void> => {
    try {
        await api.delete(`/tags/${id}`);
        logInfo('Tag deleted successfully');
    } catch (error: any) {
        logError('Failed to delete tag', error);
        throw error;
    }
};

export const pauseDownload = async (id: number): Promise<void> => {
    try {
        await api.post(`/downloads/${id}/pause`);
        logInfo('Download paused successfully');
    } catch (error: any) {
        logError('Failed to pause download', error);
        throw error;
    }
};

export const resumeDownload = async (id: number): Promise<void> => {
    try {
        await api.post(`/downloads/${id}/resume`);
        logInfo('Download resumed successfully');
    } catch (error: any) {
        logError('Failed to resume download', error);
        throw error;
    }
};

export const cancelDownload = async (id: number): Promise<void> => {
    try {
        await api.post(`/downloads/${id}/cancel`);
        logInfo('Download cancelled successfully');
    } catch (error: any) {
        logError('Failed to cancel download', error);
        throw error;
    }
};

export const retryDownload = async (id: number): Promise<void> => {
    try {
        await api.post(`/downloads/${id}/retry`);
        logInfo('Download retry initiated');
    } catch (error: any) {
        logError('Failed to retry download', error);
        throw error;
    }
};

export const getSystemStatus = async (): Promise<any> => {
    try {
        const response = await api.get('/system/status');
        return response.data;
    } catch (error: any) {
        logError('Failed to fetch system status', error);
        throw error;
    }
};
