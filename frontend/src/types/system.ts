export interface SystemInfo {
    version: string;
    uptime: string;
    api_host: string;
    api_port: number;
    download_clients: {
        transmission_url: string;
        config_endpoint: string;
    };
    supported_formats: string[];
    active_connections: number;
}

export interface TransmissionConfig {
    name: string;
    host: string;
    port: number;
    url_base: string;
    full_url: string;
    instructions: Record<string, string[]>;
}

export interface ClientConfig {
    transmission: TransmissionConfig;
    json_config: Record<string, unknown>;
}

export type MediaManagerApp = 'readarr' | 'sonarr' | 'radarr';
