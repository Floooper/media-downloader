import { useState, useEffect } from 'react';
import {
    Card,
    Text,
    Button,
    Group,
    Stack,
    Title,
    Badge,
    Divider,
    Tabs,
    Code,
    CopyButton,
    ActionIcon,
    Tooltip,
    Grid,
    Alert,
    Accordion,
    List,
    ThemeIcon,
    Progress,
    Anchor,
} from '@mantine/core';
import {
    IconCheck,
    IconCopy,
    IconExternalLink,
    IconInfoCircle,
    IconServer,
    IconSettings,
    IconDownload,
    IconDatabase,
    IconCloudDownload,
    IconCloud,
    IconApi,
    IconActivity,
} from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import { mediaManagerService } from '../services/api';

interface SystemInfo {
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

interface ClientConfig {
    transmission: {
        name: string;
        host: string;
        port: number;
        url_base: string;
        full_url: string;
        instructions: {
            readarr: string[];
            sonarr: string[];
            radarr: string[];
        };
    };
    json_config: {
        readarr: any;
        sonarr: any;
        radarr: any;
    };
}

export function SystemSettings() {
    const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
    const [clientConfig, setClientConfig] = useState<ClientConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<string | null>('overview');

    useEffect(() => {
        fetchSystemInfo();
        fetchClientConfig();
    }, []);

    const fetchSystemInfo = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/system/info');
            const info = await response.json();
            setSystemInfo(info);
        } catch (error) {
            console.error('Failed to fetch system info:', error);
            // Fallback to mock data if API fails
            setSystemInfo({
                version: '0.1.0',
                uptime: 'Unknown',
                api_host: 'localhost',
                api_port: 8000,
                download_clients: {
                    transmission_url: 'http://localhost:8000/api/transmission/rpc',
                    config_endpoint: 'http://localhost:8000/api/transmission/client-config'
                },
                supported_formats: ['Torrent', 'Magnet Links', 'NZB'],
                active_connections: 0
            });
        }
    };

    const fetchClientConfig = async () => {
        console.log("=== FETCHING CLIENT CONFIG ===");
        try {
            const response = await fetch('http://localhost:8000/api/transmission/client-config');
            const config = await response.json();
            console.log("=== CLIENT CONFIG RECEIVED ===", config);
            setClientConfig(config);
            console.log("=== CLIENT CONFIG SET ===", config);
        } catch (error) {
            console.error('Failed to fetch client config:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to load download client configuration',
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = (text: string, label: string) => {
        navigator.clipboard.writeText(text);
        showNotification({
            title: 'Copied!',
            message: `${label} copied to clipboard`,
            color: 'green',
            icon: <IconCheck size={16} />,
        });
    };

    const renderSystemOverview = () => (
        <Stack spacing="lg">
            <Card shadow="sm" padding="lg">
                <Group justify="space-between" mb="md">
                    <Group>
                        <ThemeIcon c="blue" size="lg">
                            <IconServer size={20} />
                        </ThemeIcon>
                        <Title order={3}>System Information</Title>
                    </Group>
                    <Badge c="green">Online</Badge>
                </Group>
                
                <Grid>
                    <Grid.Col span={6}>
                        <Text size="sm" c="dimmed">Version</Text>
                        <Text fw={500}>{systemInfo?.version}</Text>
                    </Grid.Col>
                    <Grid.Col span={6}>
                        <Text size="sm" c="dimmed">Uptime</Text>
                        <Text fw={500}>{systemInfo?.uptime}</Text>
                    </Grid.Col>
                    <Grid.Col span={6}>
                        <Text size="sm" c="dimmed">API Host</Text>
                        <Text fw={500}>{systemInfo?.api_host}:{systemInfo?.api_port}</Text>
                    </Grid.Col>
                    <Grid.Col span={6}>
                        <Text size="sm" c="dimmed">Active Connections</Text>
                        <Text fw={500}>{systemInfo?.active_connections}</Text>
                    </Grid.Col>
                </Grid>
            </Card>

            <Card shadow="sm" padding="lg">
                <Group mb="md">
                    <ThemeIcon c="grape" size="lg">
                        <IconDownload size={20} />
                    </ThemeIcon>
                    <Title order={3}>Download Capabilities</Title>
                </Group>
                
                <List
                    spacing="xs"
                    size="sm"
                    center
                    icon={
                        <ThemeIcon c="teal" size={24} radius="xl">
                            <IconCheck size={16} />
                        </ThemeIcon>
                    }
                >
                    {systemInfo?.supported_formats.map((format) => (
                        <List.Item key={format}>{format}</List.Item>
                    ))}
                </List>
            </Card>

            <Card shadow="sm" padding="lg">
                <Group mb="md">
                    <ThemeIcon c="orange" size="lg">
                        <IconActivity size={20} />
                    </ThemeIcon>
                    <Title order={3}>API Endpoints</Title>
                </Group>
                
                <Stack spacing="xs">
                    <Group justify="space-between">
                        <Text size="sm">Main API</Text>
                        <Badge variant="light">http://localhost:8000/api</Badge>
                    </Group>
                    <Group justify="space-between">
                        <Text size="sm">Transmission RPC</Text>
                        <Badge variant="light">http://localhost:8000/api/transmission/rpc</Badge>
                    </Group>
                    <Group justify="space-between">
                        <Text size="sm">Health Check</Text>
                        <Badge variant="light">http://localhost:8000/health</Badge>
                    </Group>
                </Stack>
            </Card>
        </Stack>
    );

    const renderDownloadClientConfig = () => {
        console.log("=== RENDERING CLIENT CONFIG ===", clientConfig);
        if (!clientConfig) return <Text>Loading configuration...</Text>;

        return (
            <Stack spacing="lg">
                <Alert icon={<IconInfoCircle size={16} />} title="Download Client Integration" c="blue">
                    Use these settings to configure media managers (Readarr, Sonarr, Radarr) to use this application as a download client.
                </Alert>

                <Tabs defaultValue="readarr">
                    <Tabs.List>
                        <Tabs.Tab value="readarr" icon={<IconDatabase size={14} />}>Readarr</Tabs.Tab>
                        <Tabs.Tab value="sonarr" icon={<IconCloudDownload size={14} />}>Sonarr</Tabs.Tab>
                        <Tabs.Tab value="radarr" icon={<IconCloudDownload size={14} />}>Radarr</Tabs.Tab>
                    </Tabs.List>

                    {['readarr', 'sonarr', 'radarr'].map((app) => (
                        <Tabs.Panel key={app} value={app} pt="xs">
                            <Stack spacing="md">
                                <Card shadow="sm" padding="md">
                                    <Title order={4} mb="md">Manual Configuration</Title>
                                    <Grid>
                                        <Grid.Col span={6}>
                                            <Text size="sm" c="dimmed">Name</Text>
                                            <Group spacing="xs">
                                                <Code>{clientConfig.transmission.name}</Code>
                                                <CopyButton value={clientConfig.transmission.name}>
                                                    {({ copied, copy }) => (
                                                        <Tooltip label={copied ? 'Copied' : 'Copy'}>
                                                            <ActionIcon c={copied ? 'teal' : 'gray'} onClick={copy}>
                                                                {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                                            </ActionIcon>
                                                        </Tooltip>
                                                    )}
                                                </CopyButton>
                                            </Group>
                                        </Grid.Col>
                                        <Grid.Col span={6}>
                                            <Text size="sm" c="dimmed">Implementation</Text>
                                            <Code>Transmission</Code>
                                        </Grid.Col>
                                        <Grid.Col span={6}>
                                            <Text size="sm" c="dimmed">Host</Text>
                                            <Group spacing="xs">
                                                <Code>{clientConfig.transmission.host}</Code>
                                                <CopyButton value={clientConfig.transmission.host}>
                                                    {({ copied, copy }) => (
                                                        <Tooltip label={copied ? 'Copied' : 'Copy'}>
                                                            <ActionIcon c={copied ? 'teal' : 'gray'} onClick={copy}>
                                                                {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                                            </ActionIcon>
                                                        </Tooltip>
                                                    )}
                                                </CopyButton>
                                            </Group>
                                        </Grid.Col>
                                        <Grid.Col span={6}>
                                            <Text size="sm" c="dimmed">Port</Text>
                                            <Group spacing="xs">
                                                <Code>{clientConfig.transmission.port}</Code>
                                                <CopyButton value={clientConfig.transmission.port.toString()}>
                                                    {({ copied, copy }) => (
                                                        <Tooltip label={copied ? 'Copied' : 'Copy'}>
                                                            <ActionIcon c={copied ? 'teal' : 'gray'} onClick={copy}>
                                                                {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                                            </ActionIcon>
                                                        </Tooltip>
                                                    )}
                                                </CopyButton>
                                            </Group>
                                        </Grid.Col>
                                        <Grid.Col span={12}>
                                            <Text size="sm" c="dimmed">URL Base</Text>
                                            <Group spacing="xs">
                                                <Code>{clientConfig.transmission.url_base}</Code>
                                                <CopyButton value={clientConfig.transmission.url_base}>
                                                    {({ copied, copy }) => (
                                                        <Tooltip label={copied ? 'Copied' : 'Copy'}>
                                                            <ActionIcon c={copied ? 'teal' : 'gray'} onClick={copy}>
                                                                {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                                            </ActionIcon>
                                                        </Tooltip>
                                                    )}
                                                </CopyButton>
                                            </Group>
                                        </Grid.Col>
                                        <Grid.Col span={12}>
                                            <Text size="sm" c="dimmed">Category</Text>
                                            <Group spacing="xs">
                                                <Code>{app}</Code>
                                                <CopyButton value={app}>
                                                    {({ copied, copy }) => (
                                                        <Tooltip label={copied ? 'Copied' : 'Copy'}>
                                                            <ActionIcon c={copied ? 'teal' : 'gray'} onClick={copy}>
                                                                {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                                            </ActionIcon>
                                                        </Tooltip>
                                                    )}
                                                </CopyButton>
                                            </Group>
                                        </Grid.Col>
                                    </Grid>
                                    
                                    <Divider my="md" />
                                    
                                    <Group justify="space-between">
                                        <Text size="sm" fw={500}>Full RPC URL</Text>
                                        <Group spacing="xs">
                                            <Anchor href={clientConfig.transmission.full_url} target="_blank">
                                                <Code>{clientConfig.transmission.full_url}</Code>
                                            </Anchor>
                                            <ActionIcon
                                                variant="light"
                                                onClick={() => window.open(clientConfig.transmission.full_url, '_blank')}
                                            >
                                                <IconExternalLink size={16} />
                                            </ActionIcon>
                                            <CopyButton value={clientConfig.transmission.full_url}>
                                                {({ copied, copy }) => (
                                                    <Tooltip label={copied ? 'Copied' : 'Copy'}>
                                                        <ActionIcon c={copied ? 'teal' : 'gray'} onClick={copy}>
                                                            {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                                        </ActionIcon>
                                                    </Tooltip>
                                                )}
                                            </CopyButton>
                                        </Group>
                                    </Group>
                                </Card>

                                <Card shadow="sm" padding="md">
                                    <Title order={4} mb="md">Step-by-Step Instructions</Title>
                                    <List size="sm" spacing="xs">
                                        {clientConfig.transmission.instructions[app as keyof typeof clientConfig.transmission.instructions].map((step, index) => (
                                            <List.Item key={index}>{step}</List.Item>
                                        ))}
                                    </List>
                                </Card>

                                <Accordion variant="separated">
                                    <Accordion.Item value="json-config">
                                        <Accordion.Control icon={<IconApi size={16} />}>
                                            JSON Configuration (Advanced)
                                        </Accordion.Control>
                                        <Accordion.Panel>
                                            <Group justify="space-between" mb="xs">
                                                <Text size="sm" c="dimmed">Use this JSON for API-based configuration</Text>
                                                <CopyButton value={JSON.stringify(clientConfig.json_config[app as keyof typeof clientConfig.json_config], null, 2)}>
                                                    {({ copied, copy }) => (
                                                        <Button
                                                            size="xs"
                                                            variant="light"
                                                            leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
                                                            onClick={copy}
                                                        >
                                                            {copied ? 'Copied' : 'Copy JSON'}
                                                        </Button>
                                                    )}
                                                </CopyButton>
                                            </Group>
                                            <Code block>
                                                {JSON.stringify(clientConfig.json_config[app as keyof typeof clientConfig.json_config], null, 2)}
                                            </Code>
                                        </Accordion.Panel>
                                    </Accordion.Item>
                                </Accordion>
                            </Stack>
                        </Tabs.Panel>
                    ))}
                </Tabs>
            </Stack>
        );
    };

    const renderAppSettings = () => (
        <Stack spacing="lg">
            <Card shadow="sm" padding="lg">
                <Title order={3} mb="md">Application Settings</Title>
                <Text c="dimmed" mb="md">
                    Configure global application settings and preferences.
                </Text>
                
                <Stack spacing="md">
                    <Group justify="space-between">
                        <div>
                            <Text size="sm" fw={500}>Default Download Path</Text>
                            <Text size="xs" c="dimmed">Default location for new downloads</Text>
                        </div>
                        <Code>./downloads</Code>
                    </Group>
                    
                    <Group justify="space-between">
                        <div>
                            <Text size="sm" fw={500}>Max Concurrent Downloads</Text>
                            <Text size="xs" c="dimmed">Maximum number of simultaneous downloads</Text>
                        </div>
                        <Badge>5</Badge>
                    </Group>
                    
                    <Group justify="space-between">
                        <div>
                            <Text size="sm" fw={500}>Auto-tag Downloads</Text>
                            <Text size="xs" c="dimmed">Automatically assign tags based on patterns</Text>
                        </div>
                        <Badge c="green">Enabled</Badge>
                    </Group>
                    
                    <Group justify="space-between">
                        <div>
                            <Text size="sm" fw={500}>Cleanup Completed</Text>
                            <Text size="xs" c="dimmed">Remove completed downloads from queue</Text>
                        </div>
                        <Badge c="orange">Disabled</Badge>
                    </Group>
                </Stack>
            </Card>
            
            <Card shadow="sm" padding="lg">
                <Title order={3} mb="md">Media Manager Integration</Title>
                <Text c="dimmed" mb="md">
                    Status of connected media management applications.
                </Text>
                
                <Stack spacing="sm">
                    <Group justify="space-between">
                        <Group>
                            <ThemeIcon c="blue" size="sm">
                                <IconDatabase size={12} />
                            </ThemeIcon>
                            <Text size="sm">Readarr</Text>
                        </Group>
                        <Badge c="green">Connected</Badge>
                    </Group>
                    
                    <Group justify="space-between">
                        <Group>
                            <ThemeIcon c="grape" size="sm">
                                <IconCloudDownload size={12} />
                            </ThemeIcon>
                            <Text size="sm">Sonarr</Text>
                        </Group>
                        <Badge c="gray">Not Configured</Badge>
                    </Group>
                    
                    <Group justify="space-between">
                        <Group>
                            <ThemeIcon c="red" size="sm">
                                <IconCloudDownload size={12} />
                            </ThemeIcon>
                            <Text size="sm">Radarr</Text>
                        </Group>
                        <Badge c="gray">Not Configured</Badge>
                    </Group>
                </Stack>
            </Card>
        </Stack>
    );

    if (loading) {
        return (
            <Stack spacing="xl" align="center" justify="center" style={{ minHeight: 400 }}>
                <Progress value={65} size="lg" style={{ width: 200 }} animated />
                <Text>Loading system information...</Text>
            </Stack>
        );
    }

    return (
        <Stack spacing="xl">
            <Group justify="space-between">
                <Title order={2}>System & Settings</Title>
                <Badge size="lg" variant="gradient" gradient={{ from: 'teal', to: 'blue' }}>
                    v{systemInfo?.version}
                </Badge>
            </Group>

            <Tabs value={activeTab} onTabChange={setActiveTab}>
                <Tabs.List>
                    <Tabs.Tab value="overview" icon={<IconServer size={14} />}>Overview</Tabs.Tab>
                    <Tabs.Tab value="download-client" icon={<IconCloud size={14} />}>Download Client</Tabs.Tab>
                    <Tabs.Tab value="settings" icon={<IconSettings size={14} />}>Settings</Tabs.Tab>
                </Tabs.List>

                <Tabs.Panel value="overview" pt="xs">
                    {renderSystemOverview()}
                </Tabs.Panel>

                <Tabs.Panel value="download-client" pt="xs">
                    {renderDownloadClientConfig()}
                </Tabs.Panel>

                <Tabs.Panel value="settings" pt="xs">
                    {renderAppSettings()}
                </Tabs.Panel>
            </Tabs>
        </Stack>
    );
}

