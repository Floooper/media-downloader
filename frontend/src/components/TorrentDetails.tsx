import {
    Card,
    Text,
    Group,
    Stack,
    Progress,
    ActionIcon,
    Menu,
    Button,
    Collapse,
    SimpleGrid,
    Table,
    NumberInput,
    UnstyledButton,
    Box,
} from '@mantine/core';
import {
    IconChevronDown,
    IconChevronUp,
    IconFileDownload,
    IconUpload,
    IconUsers,
    IconUserCheck,
    IconPuzzle,
} from '@tabler/icons-react';
import { useState } from 'react';
import { Download, FileInfo } from '../types/api';

interface TorrentDetailsProps {
    download: Download;
    onSetPriority: (fileIndex: number, priority: number) => void;
}

export function TorrentDetails({ download, onSetPriority }: TorrentDetailsProps) {
    const [expanded, setExpanded] = useState(false);

    const formatSize = (bytes: number): string => {
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        return `${size.toFixed(2)} ${units[unitIndex]}`;
    };

    const getPriorityLabel = (priority: number): string => {
        switch (priority) {
            case 7:
                return 'Maximum';
            case 4:
                return 'High';
            case 1:
                return 'Normal';
            case 0:
                return 'Skip';
            default:
                return 'Normal';
        }
    };

    const getPriorityColor = (priority: number): string => {
        switch (priority) {
            case 7:
                return 'green';
            case 4:
                return 'blue';
            case 1:
                return 'gray';
            case 0:
                return 'red';
            default:
                return 'gray';
        }
    };

    return (
        <Card radius="md" withBorder>
            <UnstyledButton onClick={() => setExpanded(!expanded)} w="100%">
                <Group justify="space-between">
                    <Group>
                        <IconPuzzle size={20} />
                        <Text fw={500}>Torrent Details</Text>
                    </Group>
                    {expanded ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
                </Group>
            </UnstyledButton>

            <Collapse in={expanded} mt="md">
                <Stack spacing="md">
                    <SimpleGrid cols={4}>
                        <Box>
                            <Text size="sm" c="dimmed">Download Rate</Text>
                            <Group spacing="xs">
                                <IconFileDownload size={16} />
                                <Text>{((download.torrent_stats?.download_rate || 0) / 1024).toFixed(2)} MB/s</Text>
                            </Group>
                        </Box>
                        <Box>
                            <Text size="sm" c="dimmed">Upload Rate</Text>
                            <Group spacing="xs">
                                <IconUpload size={16} />
                                <Text>{((download.torrent_stats?.upload_rate || 0) / 1024).toFixed(2)} MB/s</Text>
                            </Group>
                        </Box>
                        <Box>
                            <Text size="sm" c="dimmed">Peers</Text>
                            <Group spacing="xs">
                                <IconUsers size={16} />
                                <Text>{download.torrent_stats?.num_peers || 0}</Text>
                            </Group>
                        </Box>
                        <Box>
                            <Text size="sm" c="dimmed">Seeds</Text>
                            <Group spacing="xs">
                                <IconUserCheck size={16} />
                                <Text>{download.torrent_stats?.total_seeds || 0}</Text>
                            </Group>
                        </Box>
                    </SimpleGrid>

                    <Progress
                        sections={[
                            {
                                value: ((download.torrent_stats?.downloaded_pieces || 0) / (download.torrent_stats?.total_pieces || 1)) * 100,
                                color: 'blue',
                                label: 'Downloaded Pieces',
                                tooltip: `${download.torrent_stats?.downloaded_pieces || 0}/${download.torrent_stats?.total_pieces || 0} pieces`,
                            },
                        ]}
                        size="xl"
                    />

                    {download.files && download.files.length > 0 && (
                        <Table>
                            <Table.Thead>
                                <Table.Tr>
                                    <Table.Th>File</Table.Th>
                                    <Table.Th>Size</Table.Th>
                                    <Table.Th>Progress</Table.Th>
                                    <Table.Th>Priority</Table.Th>
                                </Table.Tr>
                            </Table.Thead>
                            <Table.Tbody>
                                {download.files.map((file: FileInfo, index: number) => (
                                    <Table.Tr key={file.path}>
                                        <Table.Td>
                                            <Text size="sm" truncate>
                                                {file.path.split('/').pop()}
                                            </Text>
                                        </Table.Td>
                                        <Table.Td>
                                            <Text size="sm">{formatSize(file.size)}</Text>
                                        </Table.Td>
                                        <Table.Td style={{ width: '30%' }}>
                                            <Progress
                                                value={file.progress}
                                                label={`${Math.round(file.progress)}%`}
                                                size="sm"
                                                c={file.priority === 0 ? 'gray' : 'blue'}
                                            />
                                        </Table.Td>
                                        <Table.Td>
                                            <Menu>
                                                <Menu.Target>
                                                    <Button
                                                        variant="light"
                                                        c={getPriorityColor(file.priority)}
                                                        size="xs"
                                                        compact
                                                    >
                                                        {getPriorityLabel(file.priority)}
                                                    </Button>
                                                </Menu.Target>
                                                <Menu.Dropdown>
                                                    <Menu.Item onClick={() => onSetPriority(index, 7)}>Maximum</Menu.Item>
                                                    <Menu.Item onClick={() => onSetPriority(index, 4)}>High</Menu.Item>
                                                    <Menu.Item onClick={() => onSetPriority(index, 1)}>Normal</Menu.Item>
                                                    <Menu.Item onClick={() => onSetPriority(index, 0)} c="red">Skip</Menu.Item>
                                                </Menu.Dropdown>
                                            </Menu>
                                        </Table.Td>
                                    </Table.Tr>
                                ))}
                            </Table.Tbody>
                        </Table>
                    )}
                </Stack>
            </Collapse>
        </Card>
    );
}

