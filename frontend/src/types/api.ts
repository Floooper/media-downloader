export interface Download {
    id: number;
    name: string;
    size: number;
    progress: number;
    status: DownloadStatus;
    path: string;
    created_at: string;
    updated_at: string;
    tags: Tag[];
}

export enum DownloadStatus {
    QUEUED = 'queued',
    DOWNLOADING = 'downloading',
    PAUSED = 'paused',
    COMPLETED = 'completed',
    FAILED = 'failed',
    CANCELLED = 'cancelled'
}

export interface Tag {
    id: number;
    name: string;
    created_at: string;
    updated_at: string;
}

export interface SystemStatus {
    usenet: {
        connected: boolean;
        max_connections: number;
        active_connections: number;
        download_rate: number;
    };
    downloads: {
        active: number;
        queued: number;
        completed: number;
        failed: number;
    };
    system: {
        cpu_usage: number;
        memory_usage: number;
        disk_usage: number;
    };
}
