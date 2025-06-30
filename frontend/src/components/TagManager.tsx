import { useState, useEffect } from 'react';
import {
    Card,
    Text,
    Group,
    Stack,
    Title,
    Badge,
    Button,
    ActionIcon,
    Modal,
    TextInput,
    ColorInput,
    Textarea,
    Table,
    Tooltip,
    Menu,
    Code,
    Alert,
    Select,
} from '@mantine/core';
import {
    IconPlus,
    IconEdit,
    IconTrash,
    IconFolder,
    IconWand,
    IconInfoCircle,
    IconCheck,
    IconX,
    IconSettings,
} from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import { Tag } from '../types/api';
import { tagService } from '../services/api';

interface TagManagerProps {
    onTagsUpdated?: () => void;
}

export function TagManager({ onTagsUpdated }: TagManagerProps) {
    const [tags, setTags] = useState<Tag[]>([]);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editingTag, setEditingTag] = useState<Tag | null>(null);
    const [testPattern, setTestPattern] = useState('');
    const [testResult, setTestResult] = useState<{valid: boolean; message: string} | null>(null);
    
    // Form states
    const [formData, setFormData] = useState({
        name: '',
        color: '#3b82f6',
        destination_folder: '',
        auto_assign_pattern: '',
        description: ''
    });

    const fetchTags = async () => {
        try {
            const tagsList = await tagService.getTags();
            setTags(tagsList);
        } catch (error) {
            console.error('Failed to fetch tags:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to fetch tags',
                color: 'red',
            });
        }
    };

    const handleCreateTag = async () => {
        try {
            await tagService.createTag({
                name: formData.name,
                color: formData.color,
                destination_folder: formData.destination_folder || undefined,
                auto_assign_pattern: formData.auto_assign_pattern || undefined,
                description: formData.description || undefined
            });
            
            setIsCreateModalOpen(false);
            resetForm();
            await fetchTags();
            onTagsUpdated?.();
            
            showNotification({
                title: 'Success',
                message: 'Tag created successfully',
                color: 'green',
            });
        } catch (error) {
            console.error('Failed to create tag:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to create tag',
                color: 'red',
            });
        }
    };

    const handleUpdateTag = async () => {
        if (!editingTag) return;
        
        try {
            await tagService.updateTag(editingTag.id, {
                name: formData.name,
                color: formData.color,
                destination_folder: formData.destination_folder || undefined,
                auto_assign_pattern: formData.auto_assign_pattern || undefined,
                description: formData.description || undefined
            });
            
            setIsEditModalOpen(false);
            setEditingTag(null);
            resetForm();
            await fetchTags();
            onTagsUpdated?.();
            
            showNotification({
                title: 'Success',
                message: 'Tag updated successfully',
                color: 'green',
            });
        } catch (error) {
            console.error('Failed to update tag:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to update tag',
                color: 'red',
            });
        }
    };

    const handleDeleteTag = async (tagId: number) => {
        try {
            await tagService.deleteTag(tagId);
            await fetchTags();
            onTagsUpdated?.();
            
            showNotification({
                title: 'Success',
                message: 'Tag deleted successfully',
                color: 'green',
            });
        } catch (error) {
            console.error('Failed to delete tag:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to delete tag',
                color: 'red',
            });
        }
    };

    const handleTestPattern = async () => {
        if (!formData.auto_assign_pattern || !testPattern) return;
        
        try {
            const result = await tagService.validatePattern(formData.auto_assign_pattern);
            setTestResult(result);
        } catch (error) {
            console.error('Failed to test pattern:', error);
            setTestResult({
                valid: false,
                message: 'Failed to test pattern'
            });
        }
    };

    const resetForm = () => {
        setFormData({
            name: '',
            color: '#3b82f6',
            destination_folder: '',
            auto_assign_pattern: '',
            description: ''
        });
        setTestResult(null);
    };

    const openEditModal = (tag: Tag) => {
        setEditingTag(tag);
        setFormData({
            name: tag.name,
            color: tag.color,
            destination_folder: tag.destination_folder || '',
            auto_assign_pattern: tag.auto_assign_pattern || '',
            description: tag.description || ''
        });
        setIsEditModalOpen(true);
    };

    useEffect(() => {
        fetchTags();
    }, []);

    const tagModal = (
        <Modal
            opened={isCreateModalOpen || isEditModalOpen}
            onClose={() => {
                setIsCreateModalOpen(false);
                setIsEditModalOpen(false);
                setEditingTag(null);
                resetForm();
            }}
            title={editingTag ? 'Edit Tag' : 'Create New Tag'}
            size="lg"
        >
            <Stack spacing="md">
                <Group grow>
                    <TextInput
                        label="Tag Name"
                        placeholder="Enter tag name"
                        value={formData.name}
                        onChange={(e) => setFormData({...formData, name: e.currentTarget.value})}
                        required
                    />
                    <ColorInput
                        label="Color"
                        value={formData.color}
                        onChange={(color) => setFormData({...formData, color})}
                    />
                </Group>

                <TextInput
                    label="Destination Folder"
                    placeholder="/downloads/movies"
                    icon={<IconFolder size={16} />}
                    value={formData.destination_folder}
                    onChange={(e) => setFormData({...formData, destination_folder: e.currentTarget.value})}
                    description="Downloads with this tag will be saved to this folder"
                />

                <Stack spacing="xs">
                    <TextInput
                        label="Auto-assign Pattern (Regex)"
                        placeholder=".*\\.(avi|mkv|mp4)$"
                        icon={<IconWand size={16} />}
                        value={formData.auto_assign_pattern}
                        onChange={(e) => setFormData({...formData, auto_assign_pattern: e.currentTarget.value})}
                        description="Regular expression to automatically assign this tag to matching downloads"
                    />
                    
                    {formData.auto_assign_pattern && (
                        <Group spacing="xs">
                            <TextInput
                                placeholder="Test string"
                                value={testPattern}
                                onChange={(e) => setTestPattern(e.currentTarget.value)}
                                style={{ flex: 1 }}
                            />
                            <Button size="xs" onClick={handleTestPattern}>
                                Test
                            </Button>
                        </Group>
                    )}
                    
                    {testResult && (
                        <Alert
                            c={testResult.valid ? 'green' : 'red'}
                            icon={testResult.valid ? <IconCheck size={16} /> : <IconX size={16} />}
                        >
                            {testResult.message}
                        </Alert>
                    )}
                </Stack>

                <Textarea
                    label="Description"
                    placeholder="Optional description for this tag"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.currentTarget.value})}
                />

                <Group position="right" spacing="xs">
                    <Button
                        variant="outline"
                        onClick={() => {
                            setIsCreateModalOpen(false);
                            setIsEditModalOpen(false);
                            setEditingTag(null);
                            resetForm();
                        }}
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={editingTag ? handleUpdateTag : handleCreateTag}
                        disabled={!formData.name}
                    >
                        {editingTag ? 'Update' : 'Create'}
                    </Button>
                </Group>
            </Stack>
        </Modal>
    );

    return (
        <Stack spacing="lg">
            <Group justify="space-between">
                <Title order={2}>Tag Management</Title>
                <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={() => setIsCreateModalOpen(true)}
                >
                    Create Tag
                </Button>
            </Group>

            <Card shadow="sm" p="lg" radius="md" withBorder>
                <Table>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th>Tag</Table.Th>
                            <Table.Th>Destination Folder</Table.Th>
                            <Table.Th>Auto-assign Pattern</Table.Th>
                            <Table.Th>Description</Table.Th>
                            <Table.Th>Actions</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {tags.map((tag) => (
                            <Table.Tr key={tag.id}>
                                <Table.Td>
                                    <Badge
                                        c={tag.color}
                                        style={{ backgroundColor: tag.color }}
                                    >
                                        {tag.name}
                                    </Badge>
                                </Table.Td>
                                <Table.Td>
                                    {tag.destination_folder ? (
                                        <Code>{tag.destination_folder}</Code>
                                    ) : (
                                        <Text size="sm" c="dimmed">None</Text>
                                    )}
                                </Table.Td>
                                <Table.Td>
                                    {tag.auto_assign_pattern ? (
                                        <Tooltip label={tag.auto_assign_pattern}>
                                            <Code style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {tag.auto_assign_pattern.length > 30 
                                                    ? tag.auto_assign_pattern.substring(0, 30) + '...'
                                                    : tag.auto_assign_pattern
                                                }
                                            </Code>
                                        </Tooltip>
                                    ) : (
                                        <Text size="sm" c="dimmed">None</Text>
                                    )}
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm">
                                        {tag.description || <Text c="dimmed">No description</Text>}
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Group spacing="xs">
                                        <Tooltip label="Edit tag">
                                            <ActionIcon
                                                c="blue"
                                                onClick={() => openEditModal(tag)}
                                            >
                                                <IconEdit size={16} />
                                            </ActionIcon>
                                        </Tooltip>
                                        <Tooltip label="Delete tag">
                                            <ActionIcon
                                                c="red"
                                                onClick={() => handleDeleteTag(tag.id)}
                                            >
                                                <IconTrash size={16} />
                                            </ActionIcon>
                                        </Tooltip>
                                    </Group>
                                </Table.Td>
                            </Table.Tr>
                        ))}
                    </Table.Tbody>
                </Table>

                {tags.length === 0 && (
                    <Text align="center" c="dimmed" py="xl">
                        No tags created yet. Create your first tag to get started!
                    </Text>
                )}
            </Card>

            {tagModal}
        </Stack>
    );
}

