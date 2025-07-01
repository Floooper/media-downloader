export interface UsenetStatus {
  connected: boolean;
  active_connections: number;
  max_connections: number;
  download_rate: number;
}

export interface SystemStats {
  memory_usage: number;
  disk_usage: number;
}

export interface SystemStatusData {
  usenet: UsenetStatus;
  system: SystemStats;
}
