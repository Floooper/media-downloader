import React from 'react';
import {
    Paper,
    Text,
    Progress,
    Group,
    Stack,
    Badge,
    ActionIcon,
    Tooltip,
    Box,
} from '@mantine/core';
import {
    IconCheck,
    IconAlertTriangle,
    IconRotate,
    IconPlayerPause,
    IconPlayerPlay,
} from '@tabler/icons-react';
import { NZBDownloadDetails } from '../types/api';

interface NZBDetailsProps {
    details: NZBDownloadDetails;
    onPause?: (fileIndex: number) => void;
    onResume?: (fileIndex: number) => void;
    onRetry?: (fileIndex: number) => void;
}

export function NZBDetails({ details, onPause, onResume, onRetry }: NZBDetailsProps) {
    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'completed':
                return 'green';
            case 'downloading':
                return 'blue';
            case 'paused':
                return 'yellow';
            case 'verification_failed':
                return 'red';
            default:
                return 'gray';
        }
    };

    return (
        <Paper p="md" radius="md" withBorder>
            <Stack spacing="md">
                <Group justify="space-between">
                    <Group>
                        <Badge
                            c={getStatusColor(details.status)}
                            variant="filled"
                            size="lg"
                        >
                            {details.status}
                        </Badge>
                        {details.failedSegments > 0 && (
                            <Badge c="red" variant="outline">
                                {details.failedSegments} failed segments
                            </Badge>
                        )}
                    </Group>
                    <Text size="sm" c="dimmed">
                        {Math.round(details.downloadedBytes / 1024 / 1024)}MB /
                        {Math.round(details.totalBytes / 1024 / 1024)}MB
                    </Text>
                </Group>

                <Progress
                    value={details.progress}
                    size="xl"
                    radius="xl"
                    label={`${Math.round(details.progress)}%`}
                    c={getStatusColor(details.status)}
                />

                <Stack spacing="xs">
                    {details.files.map((file, index) => (
                        <Box
                            key={file.subject}
                            p="xs"
                            sx={(theme) => ({
                                backgroundColor:
                                    theme.colorScheme === 'dark'
                                        ? theme.colors.dark[6]
                                        : theme.colors.gray[0],
                                borderRadius: theme.radius.sm,
                            })}
                        >
                            <Group justify="space-between" align="center">
                                <Stack gap={4}>
                                    <Text size="sm" fw={500}>
                                        {file.subject}
                                    </Text>
                                    <Group spacing="xs">
                                        <Progress
                                            value={file.progress}
                                            size="sm"
                                            style={{ width: 100 }}
                                        />
                                        <Text size="xs" c="dimmed">
                                            {Math.round(file.progress)}%
                                        </Text>
                                        {file.verified && (
                                            <Tooltip label="Verified">
                                                <ActionIcon
                                                    c="green"
                                                    variant="subtle"
                                                    size="sm"
                                                >
                                                    <IconCheck size={14} />
                                                </ActionIcon>
                                            </Tooltip>
                                        )}
                                        {file.repairNeeded && (
                                            <Tooltip label="Repair needed">
                                                <ActionIcon
                                                    c="yellow"
                                                    variant="subtle"
                                                    size="sm"
                                                >
                                                    <IconAlertTriangle size={14} />
                                                </ActionIcon>
                                            </Tooltip>
                                        )}
                                    </Group>
                                </Stack>

                                <Group spacing="xs">
                                    {onRetry && (
                                        <Tooltip label="Retry failed segments">
                                            <ActionIcon
                                                onClick={() => onRetry(index)}
                                                c="blue"
                                                variant="light"
                                            >
                                                <IconRotate size={16} />
                                            </ActionIcon>
                                        </Tooltip>
                                    )}
                                    {file.paused ? (
                                        onResume && (
                                            <Tooltip label="Resume">
                                                <ActionIcon
                                                    onClick={() => onResume(index)}
                                                    c="green"
                                                    variant="light"
                                                >
                                                    <IconPlayerPlay size={16} />
                                                </ActionIcon>
                                            </Tooltip>
                                        )
                                    ) : (
                                        onPause && (
                                            <Tooltip label="Pause">
                                                <ActionIcon
                                                    onClick={() => onPause(index)}
                                                    c="yellow"
                                                    variant="light"
                                                >
                                                    <IconPlayerPause size={16} />
                                                </ActionIcon>
                                            </Tooltip>
                                        )
                                    )}
                                </Group>
                            </Group>
                        </Box>
                    ))}
                </Stack>
            </Stack>
        </Paper>
    );
}

