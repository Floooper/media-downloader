import { useState, useEffect, useCallback } from 'react';
import {
    Card,
    Text,
    Button,
    Group,
    Stack,
    Title,
    Select,
    TextInput,
    Switch,
    Accordion,
    Badge,
    Divider,
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { mediaManagerService } from '../services/api';
import {
    MediaManagerType,
    MediaManagerCategory,
    MediaManagerRootFolder,
    MediaManagerQualityProfile,
    MediaManagerDiscovery,
    MediaManagerStatus,
    MediaManagerConfig,
} from '../types/api';

interface ConfigForm extends Omit<MediaManagerConfig, 'api_key'> {
    apiKey: string;
}

export function MediaManagerSettings() {
    const [selectedManager, setSelectedManager] = useState<MediaManagerType | null>(null);
    const [categories, setCategories] = useState<MediaManagerCategory[]>([]);
    const [rootFolders, setRootFolders] = useState<MediaManagerRootFolder[]>([]);
    const [qualityProfiles, setQualityProfiles] = useState<MediaManagerQualityProfile[]>([]);
    const [loading, setLoading] = useState(false);
    const [managerStatus, setManagerStatus] = useState<Record<MediaManagerType, MediaManagerStatus | undefined>>({} as Record<MediaManagerType, MediaManagerStatus | undefined>);
    const [discoveredManagers, setDiscoveredManagers] = useState<MediaManagerDiscovery[]>([]);
    const [configForm, setConfigForm] = useState<ConfigForm>({
        url: '',
        apiKey: '',
        enabled: true,
    });

    const discoverManagers = useCallback(async () => {
        try {
            const discovered = await mediaManagerService.discoverManagers();
            setDiscoveredManagers(discovered);
            showNotification({
                title: 'Success',
                message: `Found ${discovered.length} media managers`,
                color: 'green',
            });
        } catch (error) {
            console.error('Failed to discover managers:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to discover media managers',
                color: 'red',
            });
        }
    }, []);

    const testConnection = async (managerType: MediaManagerType): Promise<boolean> => {
        setLoading(true);
        try {
            const result = await mediaManagerService.testConnection(managerType, {
                url: configForm.url,
                api_key: configForm.apiKey,
                enabled: configForm.enabled,
            });
            showNotification({
                title: 'Success',
                message: `Successfully connected to ${managerType}`,
                color: 'green',
            });
            return result;
        } catch (error) {
            console.error('Connection test failed:', error);
            showNotification({
                title: 'Error',
                message: `Failed to connect to ${managerType}`,
                color: 'red',
            });
            return false;
        } finally {
            setLoading(false);
        }
    };

    const checkHealth = async (managerType: MediaManagerType) => {
        try {
            await mediaManagerService.triggerHealthCheck(managerType);
            const status = await mediaManagerService.getStatus(managerType);
            setManagerStatus(prev => ({ ...prev, [managerType]: status }));
        } catch (error) {
            console.error('Health check failed:', error);
            showNotification({
                title: 'Error',
                message: `Failed to check health for ${managerType}`,
                color: 'red',
            });
        }
    };

    const fetchManagerData = async (managerType: MediaManagerType) => {
        setLoading(true);
        try {
            const [cats, folders, profiles] = await Promise.all([
                mediaManagerService.getCategories(managerType),
                mediaManagerService.getRootFolders(managerType),
                mediaManagerService.getQualityProfiles(managerType),
            ]);
            setCategories(cats);
            setRootFolders(folders);
            setQualityProfiles(profiles);
        } catch (error) {
            console.error('Failed to fetch manager data:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to fetch manager data',
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (managerType: MediaManagerType) => {
        setLoading(true);
        try {
            await mediaManagerService.registerDownloader(managerType, {
                url: configForm.url,
                api_key: configForm.apiKey,
                enabled: configForm.enabled,
            });
            showNotification({
                title: 'Success',
                message: `Successfully registered with ${managerType}`,
                color: 'green',
            });
            // Refresh data after registration
            await fetchManagerData(managerType);
        } catch (error) {
            console.error('Failed to register:', error);
            showNotification({
                title: 'Error',
                message: `Failed to register with ${managerType}`,
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedManager) {
            void fetchManagerData(selectedManager);
        }
    }, [selectedManager]);

    return (
        <Stack spacing="xl">
            <Group justify="space-between">
                <Title order={2}>Media Manager Settings</Title>
                <Button
                    onClick={() => void discoverManagers()}
                    variant="light"
                    loading={loading}
                >
                    Auto-Discover
                </Button>
            </Group>

            {discoveredManagers.length > 0 && (
                <Card shadow="sm">
                    <Title order={3}>Discovered Media Managers</Title>
                    <Stack spacing="xs" mt="md">
                        {discoveredManagers.map((manager) => (
                            <Group key={`${manager.type}-${manager.url}`} justify="space-between">
                                <Text>{manager.name} ({manager.type})</Text>
                                <Button
                                    size="sm"
                                    variant="light"
                                    onClick={() => {
                                        setSelectedManager(manager.type);
                                        setConfigForm({
                                            ...configForm,
                                            url: manager.url,
                                            enabled: true,
                                        });
                                    }}
                                >
                                    Configure
                                </Button>
                            </Group>
                        ))}
                    </Stack>
                </Card>
            )}

            <Title order={2}>Media Manager Settings</Title>

            <Select
                label="Select Media Manager"
                placeholder="Choose a media manager"
                value={selectedManager}
                onChange={(value: string) => setSelectedManager(value as MediaManagerType)}
                data={[
                    { value: MediaManagerType.SONARR, label: 'Sonarr (TV Shows)' },
                    { value: MediaManagerType.RADARR, label: 'Radarr (Movies)' },
                    { value: MediaManagerType.READARR, label: 'Readarr (Books)' },
                    { value: MediaManagerType.LIDARR, label: 'Lidarr (Music)' },
                ]}
            />

            {selectedManager && (
                <Card shadow="sm">
                    <Stack spacing="md">
                        <Group justify="space-between">
                            <Stack gap={0}>
                                <Title order={3}>{selectedManager} Configuration</Title>
                                <Text size="sm" c="dimmed">
                                    Configure connection settings for {selectedManager}
                                </Text>
                            </Stack>
                        </Group>

                        <Divider />

                        <Stack spacing="sm">
                            <TextInput
                                label="URL"
                                placeholder={`Enter ${selectedManager} URL (e.g., http://localhost:8989)`}
                                value={configForm.url}
                                onChange={(e) => setConfigForm({ ...configForm, url: e.target.value })}
                            />

                            <TextInput
                                label="API Key"
                                placeholder={`Enter ${selectedManager} API Key`}
                                value={configForm.apiKey}
                                onChange={(e) => setConfigForm({ ...configForm, apiKey: e.target.value })}
                            />

                            <Switch
                                label="Enabled"
                                checked={configForm.enabled}
                                onChange={(e) => setConfigForm({ ...configForm, enabled: e.currentTarget.checked })}
                            />

                            <Group position="right" spacing="sm">
                                <Button
                                    variant="light"
                                    onClick={() => void testConnection(selectedManager)}
                                    loading={loading}
                                    disabled={!configForm.url || !configForm.apiKey}
                                >
                                    Test Connection
                                </Button>
                                <Button
                                    onClick={() => void handleRegister(selectedManager)}
                                    loading={loading}
                                    disabled={!configForm.url || !configForm.apiKey}
                                >
                                    Save & Register
                                </Button>
                            </Group>
                        </Stack>

                        <Divider />

                        <Accordion variant="separated">
                            <Accordion.Item value="categories">
                                <Accordion.Control>
                                    <Group justify="space-between">
                                        <Group spacing="xs">
                                            <Text>Download Categories</Text>
                                            <Badge size="sm">{categories.length}</Badge>
                                        </Group>
                                        <Badge
                                            color={managerStatus[selectedManager]?.health === 'ok' ? 'green' : 'yellow'}
                                            onClick={() => void checkHealth(selectedManager)}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            {managerStatus[selectedManager]?.health || 'unknown'}
                                        </Badge>
                                    </Group>
                                </Accordion.Control>
                                <Accordion.Panel>
                                    <Stack spacing="xs">
                                        {categories.map((category) => (
                                            <Group key={category.id} justify="space-between">
                                                <Text>{category.name}</Text>
                                                <Badge>{category.type}</Badge>
                                            </Group>
                                        ))}
                                        {categories.length === 0 && (
                                            <Text c="dimmed" size="sm">No categories configured</Text>
                                        )}
                                    </Stack>
                                </Accordion.Panel>
                            </Accordion.Item>

                            <Accordion.Item value="folders">
                                <Accordion.Control>
                                    <Group spacing="xs">
                                        <Text>Root Folders</Text>
                                        <Badge size="sm">{rootFolders.length}</Badge>
                                    </Group>
                                </Accordion.Control>
                                <Accordion.Panel>
                                    <Stack spacing="xs">
                                        {rootFolders.map((folder) => (
                                            <Text key={folder.id}>{folder.path}</Text>
                                        ))}
                                        {rootFolders.length === 0 && (
                                            <Text c="dimmed" size="sm">No root folders configured</Text>
                                        )}
                                    </Stack>
                                </Accordion.Panel>
                            </Accordion.Item>

                            <Accordion.Item value="profiles">
                                <Accordion.Control>
                                    <Group spacing="xs">
                                        <Text>Quality Profiles</Text>
                                        <Badge size="sm">{qualityProfiles.length}</Badge>
                                    </Group>
                                </Accordion.Control>
                                <Accordion.Panel>
                                    <Stack spacing="xs">
                                        {qualityProfiles.map((profile) => (
                                            <Group key={profile.id} justify="space-between">
                                                <Text>{profile.name}</Text>
                                                {profile.default && <Badge>Default</Badge>}
                                            </Group>
                                        ))}
                                        {qualityProfiles.length === 0 && (
                                            <Text c="dimmed" size="sm">No quality profiles configured</Text>
                                        )}
                                    </Stack>
                                </Accordion.Panel>
                            </Accordion.Item>
                        </Accordion>
                    </Stack>
                </Card>
            )}
        </Stack>
    );
}
