export enum MediaManagerType {
  SONARR = 'sonarr',
  RADARR = 'radarr',
  READARR = 'readarr',
  LIDARR = 'lidarr'
}

export interface MediaManagerCategory {
  id: number;
  name: string;
  type: string;
}

export interface MediaManagerRootFolder {
  id: number;
  path: string;
  accessible: boolean;
  freeSpace?: number;
}

export interface MediaManagerQualityProfile {
  id: number;
  name: string;
  default: boolean;
  upgrades: boolean;
  cutoff: number;
}

export interface MediaManagerConfig {
  url: string;
  api_key: string;
  enabled: boolean;
}

export interface MediaManagerDiscovery {
  name: string;
  type: MediaManagerType;
  url: string;
}

export interface MediaManagerStatus {
  health: 'ok' | 'warning' | 'error';
  version: string;
  startTime: string;
  uptime: string;
}

export interface DownloadStatus {
  id: number;
  name: string;
  status: string;
  progress: number;
  size: number;
  speed: number;
  eta: string;
  files: string[];
}
