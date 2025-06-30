import { useState, useEffect } from 'react';
import {
    Modal,
    Stack,
    Group,
    Button,
    Badge,
    Select,
    Text,
    ActionIcon,
    Tooltip,
} from '@mantine/core';
import {
    IconPlus,
    IconX,
    IconWand,
} from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import { Download, Tag } from '../types/api';
import { tagService } from '../services/api';

interface DownloadTagManagerProps {
    download: Download;
    opened: boolean;
    onClose: () => void;
    onTagsUpdated: () => void;
}

export function DownloadTagManager({ download, opened, onClose, onTagsUpdated }: DownloadTagManagerProps) {
    const [allTags, setAllTags] = useState<Tag[]>([]);
    const [selectedTagId, setSelectedTagId] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const fetchTags = async () => {
        try {
            const tags = await tagService.getTags();
            setAllTags(tags);
        } catch (error) {
            console.error('Failed to fetch tags:', error);
        }
    };

    const handleAddTag = async () => {
        if (!selectedTagId) return;
        
        setLoading(true);
        try {
            await tagService.addTagToDownload(download.id, parseInt(selectedTagId));
            setSelectedTagId(null);
            onTagsUpdated();
            showNotification({
                title: 'Success',
                message: 'Tag added to download',
                color: 'green',
            });
        } catch (error) {
            console.error('Failed to add tag:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to add tag to download',
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleRemoveTag = async (tagId: number) => {
        setLoading(true);
        try {
            await tagService.removeTagFromDownload(download.id, tagId);
            onTagsUpdated();
            showNotification({
                title: 'Success',
                message: 'Tag removed from download',
                color: 'green',
            });
        } catch (error) {
            console.error('Failed to remove tag:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to remove tag',
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleAutoAssignTags = async () => {
        setLoading(true);
        try {
            const result = await tagService.autoAssignTags(download.id);
            onTagsUpdated();
            showNotification({
                title: 'Success',
                message: result.message,
                color: 'green',
            });
        } catch (error) {
            console.error('Failed to auto-assign tags:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to auto-assign tags',
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (opened) {
            fetchTags();
        }
    }, [opened]);

    const availableTags = allTags.filter(
        tag => !download.tags.some(downloadTag => downloadTag.id === tag.id)
    );

    return (
        <Modal
            opened={opened}
            onClose={onClose}
            title={`Manage Tags - ${download.name}`}
            size="md"
        >
            <Stack spacing="md">
                <Group justify="space-between">
                    <Text fw={500}>Current Tags</Text>
                    <Tooltip label="Auto-assign tags based on filename">
                        <ActionIcon
                            c="blue"
                            onClick={handleAutoAssignTags}
                            loading={loading}
                        >
                            <IconWand size={16} />
                        </ActionIcon>
                    </Tooltip>
                </Group>
                
                <Group spacing="xs">
                    {download.tags.length === 0 ? (
                        <Text size="sm" c="dimmed">No tags assigned</Text>
                    ) : (
                        download.tags.map((tag) => (
                            <Badge
                                key={tag.id}
                                style={{ backgroundColor: tag.color }}
                                rightSection={
                                    <ActionIcon
                                        size="xs"
                                        c="white"
                                        variant="transparent"
                                        onClick={() => handleRemoveTag(tag.id)}
                                    >
                                        <IconX size={10} />
                                    </ActionIcon>
                                }
                            >
                                {tag.name}
                            </Badge>
                        ))
                    )}
                </Group>

                {availableTags.length > 0 && (
                    <>
                        <Text fw={500}>Add Tag</Text>
                        <Group>
                            <Select
                                placeholder="Select a tag to add"
                                data={availableTags.map(tag => ({
                                    value: tag.id.toString(),
                                    label: tag.name,
                                    color: tag.color
                                }))}
                                value={selectedTagId}
                                onChange={setSelectedTagId}
                                style={{ flex: 1 }}
                            />
                            <Button
                                leftSection={<IconPlus size={16} />}
                                onClick={handleAddTag}
                                disabled={!selectedTagId}
                                loading={loading}
                            >
                                Add
                            </Button>
                        </Group>
                    </>
                )}

                <Group position="right" mt="md">
                    <Button variant="outline" onClick={onClose}>
                        Close
                    </Button>
                </Group>
            </Stack>
        </Modal>
    );
}

