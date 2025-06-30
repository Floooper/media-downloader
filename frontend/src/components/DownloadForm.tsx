import { useState } from 'react';
import {
    Card,
    Text,
    Group,
    TextInput,
    Button,
    Stack,
    SegmentedControl,
    FileInput,
    Box,
    useMantineTheme,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { showNotification } from '@mantine/notifications';
import { IconUpload, IconDownload, IconMagnet } from '@tabler/icons-react';
import { DownloadType } from '../types/api';
import { downloadService } from '../services/api';

// URL validation function - only validate if field has content
const validateUrl = (value: string) => {
    if (!value) return null; // Allow empty for optional field
    
    // Check for magnet links
    if (value.startsWith("magnet:")) {
        return null; // Valid magnet link
    }
    
    // Check for HTTP/HTTPS URLs
    try {
        const url = new URL(value);
        if (url.protocol === "http:" || url.protocol === "https:") {
            return null; // Valid HTTP URL
        }
    } catch {
        // Invalid URL format
    }
    
    return "Please enter a valid magnet link or HTTP/HTTPS URL";
};

export function DownloadForm() {
    const theme = useMantineTheme();
    const [loading, setLoading] = useState(false);
    const [dragActive, setDragActive] = useState(false);

    const form = useForm({
        validate: {
            magnetLink: validateUrl,
        },
        initialValues: {
            downloadType: DownloadType.TORRENT,
            magnetLink: '',
            downloadPath: '/downloads',
            file: null as File | null,
        },
    });

    const handleSubmit = async (values: typeof form.values) => {
        try {
            setLoading(true);

            if (values.downloadType === DownloadType.TORRENT) {
                // For torrents, either magnet link OR file is required
                if (values.magnetLink && !values.file) {
                    // Submit magnet link
                    await downloadService.addTorrentMagnet(values.magnetLink, values.downloadPath);
                } else if (values.file && !values.magnetLink) {
                    // Submit torrent file
                    await downloadService.uploadTorrent(values.file, values.downloadPath);
                } else if (values.magnetLink && values.file) {
                    // User provided both - ask which one to use or use the file
                    await downloadService.uploadTorrent(values.file, values.downloadPath);
                } else {
                    throw new Error('Please provide either a magnet link or a torrent file');
                }
            } else if (values.downloadType === DownloadType.NZB) {
                if (!values.file) {
                    throw new Error('Please provide an NZB file');
                }
                await downloadService.uploadNzb(values.file, values.downloadPath);
            }

            form.reset();
            showNotification({
                title: 'Success',
                message: 'Download added to queue',
                color: 'green',
            });
        } catch (error) {
            console.error('Failed to add download:', error);
            showNotification({
                title: 'Error',
                message: error instanceof Error ? error.message : 'Failed to add download',
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            const fileType = file.name.toLowerCase().endsWith('.nzb') ? DownloadType.NZB : DownloadType.TORRENT;
            form.setValues({
                ...form.values,
                downloadType: fileType,
                file,
            });
        }
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    // Check if form is valid for submission
    const isFormValid = () => {
        if (form.values.downloadType === DownloadType.TORRENT) {
            // For torrents, either magnet link OR file is required
            return form.values.magnetLink || form.values.file;
        } else {
            // For NZB, file is required
            return !!form.values.file;
        }
    };

    return (
        <Card shadow="sm" radius="md" withBorder>
            <form onSubmit={form.onSubmit(handleSubmit)}>
                <Stack spacing="md">
                    <SegmentedControl
                        value={form.values.downloadType}
                        onChange={(value) => form.setFieldValue('downloadType', value as DownloadType)}
                        data={[
                            { label: 'Torrent', value: DownloadType.TORRENT },
                            { label: 'NZB', value: DownloadType.NZB },
                        ]}
                    />

                    {form.values.downloadType === DownloadType.TORRENT && (
                        <TextInput
                            label="Magnet Link (Optional if uploading file)"
                            placeholder="magnet:?xt=urn:btih:..."
                            icon={<IconMagnet size={16} />}
                            {...form.getInputProps('magnetLink')}
                        />
                    )}

                    <Box
                        sx={{
                            border: `2px dashed ${dragActive ? theme.colors.blue[6] : theme.colors.gray[4]}`,
                            borderRadius: theme.radius.md,
                            padding: theme.spacing.xl,
                            backgroundColor: dragActive ? theme.colors.blue[0] : theme.white,
                            transition: 'all 200ms ease',
                        }}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                    >
                        <FileInput
                            label={`${form.values.downloadType} File ${
                                form.values.downloadType === DownloadType.TORRENT ? '(Optional if using magnet link)' : ''
                            }`}
                            placeholder={`Upload ${form.values.downloadType} file`}
                            accept={form.values.downloadType === DownloadType.TORRENT ? '.torrent' : '.nzb'}
                            icon={<IconUpload size={16} />}
                            {...form.getInputProps('file')}
                        />
                        <Text align="center" size="sm" c="dimmed" mt="sm">
                            Drag and drop files here or click to select
                        </Text>
                    </Box>

                    <TextInput
                        label="Download Path"
                        placeholder="/downloads"
                        icon={<IconDownload size={16} />}
                        {...form.getInputProps('downloadPath')}
                    />

                    <Group justify="space-between">
                        <Text size="sm" c="dimmed">
                            {form.values.downloadType === DownloadType.TORRENT 
                                ? "Provide either a magnet link or upload a .torrent file"
                                : "Upload an .nzb file to start the download"
                            }
                        </Text>
                        <Button
                            type="submit"
                            loading={loading}
                            disabled={!isFormValid()}
                        >
                            Add Download
                        </Button>
                    </Group>
                </Stack>
            </form>
        </Card>
    );
}
