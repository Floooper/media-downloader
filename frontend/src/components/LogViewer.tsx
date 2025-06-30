import { useState, useEffect, useMemo, useRef } from 'react';
import {
    Modal,
    Stack,
    Group,
    Text,
    Badge,
    Button,
    Select,
    TextInput,
    Code,
    ScrollArea,
    ActionIcon,
    Tooltip,
    Card,
    Divider,
    Alert,
    Collapse,
    Paper,
    Switch,
    NumberInput,
} from '@mantine/core';
import {
    IconTrash,
    IconDownload,
    IconRefresh,
    IconSearch,
    IconFilter,
    IconChevronDown,
    IconChevronRight,
    IconCopy,
    IconAlertTriangle,
    IconInfoCircle,
    IconBug,
    IconX,
} from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import logger, { LogLevel, LogEntry } from '../services/logging';

interface LogViewerProps {
    opened: boolean;
    onClose: () => void;
}

export function LogViewer({ opened, onClose }: LogViewerProps) {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
    const [levelFilter, setLevelFilter] = useState<string>('all');
    const [componentFilter, setComponentFilter] = useState<string>('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [autoScroll, setAutoScroll] = useState(true);
    const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
    const [maxLogs, setMaxLogs] = useState(100);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Subscribe to log updates
        const unsubscribe = logger.subscribe((newLogs) => {
            setLogs(newLogs);
        });

        // Initial load
        setLogs(logger.getLogs());

        return unsubscribe;
    }, []);

    useEffect(() => {
        // Auto-scroll to bottom when new logs arrive
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [filteredLogs, autoScroll]);

    // Filter logs based on selected criteria
    const filterLogs = useMemo(() => {
        let filtered = logs;

        // Filter by level
        if (levelFilter !== 'all') {
            filtered = filtered.filter(log => log.level === levelFilter);
        }

        // Filter by component
        if (componentFilter !== 'all') {
            filtered = filtered.filter(log => log.component === componentFilter);
        }

        // Filter by search term
        if (searchTerm) {
            const searchLower = searchTerm.toLowerCase();
            filtered = filtered.filter(log => 
                log.message.toLowerCase().includes(searchLower) ||
                log.component?.toLowerCase().includes(searchLower)
            );
        }

        // Limit number of logs for performance
        return filtered.slice(-maxLogs);
    }, [logs, levelFilter, componentFilter, searchTerm, maxLogs]);

    useEffect(() => {
        setFilteredLogs(filterLogs);
    }, [filterLogs]);

    const getLogLevelColor = (level: LogLevel): string => {
        switch (level) {
            case LogLevel.ERROR:
                return 'red';
            case LogLevel.WARN:
                return 'yellow';
            case LogLevel.INFO:
                return 'blue';
            case LogLevel.DEBUG:
                return 'gray';
            default:
                return 'gray';
        }
    };

    const getLogLevelIcon = (level: LogLevel) => {
        switch (level) {
            case LogLevel.ERROR:
                return <IconAlertTriangle size={14} />;
            case LogLevel.WARN:
                return <IconAlertTriangle size={14} />;
            case LogLevel.INFO:
                return <IconInfoCircle size={14} />;
            case LogLevel.DEBUG:
                return <IconBug size={14} />;
            default:
                return <IconInfoCircle size={14} />;
        }
    };

    const formatTimestamp = (timestamp: Date): string => {
        return timestamp.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            fractionalSecondDigits: 3
        });
    };

    const toggleLogExpansion = (logId: string) => {
        const newExpanded = new Set(expandedLogs);
        if (newExpanded.has(logId)) {
            newExpanded.delete(logId);
        } else {
            newExpanded.add(logId);
        }
        setExpandedLogs(newExpanded);
    };

    const copyLogToClipboard = (log: LogEntry) => {
        const logText = `[${formatTimestamp(log.timestamp)}] [${log.level.toUpperCase()}] [${log.component || 'unknown'}] ${log.message}${log.details ? '\nDetails: ' + JSON.stringify(log.details, null, 2) : ''}${log.stack ? '\nStack: ' + log.stack : ''}`;
        
        navigator.clipboard.writeText(logText).then(() => {
            showNotification({
                title: 'Copied',
                message: 'Log entry copied to clipboard',
                color: 'green',
            });
        }).catch(() => {
            showNotification({
                title: 'Error',
                message: 'Failed to copy log to clipboard',
                color: 'red',
            });
        });
    };

    const exportLogs = () => {
        const logsText = filteredLogs.map(log => 
            `[${formatTimestamp(log.timestamp)}] [${log.level.toUpperCase()}] [${log.component || 'unknown'}] ${log.message}${log.details ? '\nDetails: ' + JSON.stringify(log.details, null, 2) : ''}${log.stack ? '\nStack: ' + log.stack : ''}`
        ).join('\n\n');
        
        const blob = new Blob([logsText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `app-logs-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showNotification({
            title: 'Exported',
            message: 'Logs exported successfully',
            color: 'green',
        });
    };

    const clearLogs = () => {
        logger.clearLogs();
        setExpandedLogs(new Set());
        showNotification({
            title: 'Cleared',
            message: 'All logs cleared',
            color: 'blue',
        });
    };

    const refreshLogs = () => {
        setLogs(logger.getLogs());
        showNotification({
            title: 'Refreshed',
            message: 'Logs refreshed',
            color: 'blue',
        });
    };

    // Get unique components for filter
    const uniqueComponents = useMemo(() => {
        const components = new Set(logs.map(log => log.component).filter(Boolean));
        return Array.from(components).sort();
    }, [logs]);

    // Get log counts by level
    const logCounts = useMemo(() => {
        const counts = {
            error: logs.filter(log => log.level === LogLevel.ERROR).length,
            warn: logs.filter(log => log.level === LogLevel.WARN).length,
            info: logs.filter(log => log.level === LogLevel.INFO).length,
            debug: logs.filter(log => log.level === LogLevel.DEBUG).length,
        };
        return counts;
    }, [logs]);

    return (
        <Modal
            opened={opened}
            onClose={onClose}
            title="Application Logs"
            size="xl"
            styles={{
                modal: { height: '80vh' },
                body: { height: 'calc(80vh - 60px)', display: 'flex', flexDirection: 'column' }
            }}
        >
            <Stack spacing="md" style={{ height: '100%' }}>
                {/* Header with stats */}
                <Group justify="space-between">
                    <Group spacing="xs">
                        <Badge c="red" leftSection={getLogLevelIcon(LogLevel.ERROR)}>
                            {logCounts.error} Errors
                        </Badge>
                        <Badge c="yellow" leftSection={getLogLevelIcon(LogLevel.WARN)}>
                            {logCounts.warn} Warnings
                        </Badge>
                        <Badge c="blue" leftSection={getLogLevelIcon(LogLevel.INFO)}>
                            {logCounts.info} Info
                        </Badge>
                        <Badge c="gray" leftSection={getLogLevelIcon(LogLevel.DEBUG)}>
                            {logCounts.debug} Debug
                        </Badge>
                    </Group>
                    <Text size="sm" c="dimmed">
                        Total: {logs.length} logs
                    </Text>
                </Group>

                {/* Filters and controls */}
                <Group spacing="md">
                    <Select
                        label="Level"
                        value={levelFilter}
                        onChange={(value) => setLevelFilter(value || 'all')}
                        data={[
                            { value: 'all', label: 'All Levels' },
                            { value: LogLevel.ERROR, label: 'Error' },
                            { value: LogLevel.WARN, label: 'Warning' },
                            { value: LogLevel.INFO, label: 'Info' },
                            { value: LogLevel.DEBUG, label: 'Debug' },
                        ]}
                        style={{ minWidth: 120 }}
                    />
                    
                    <Select
                        label="Component"
                        value={componentFilter}
                        onChange={(value) => setComponentFilter(value || 'all')}
                        data={[
                            { value: 'all', label: 'All Components' },
                            ...uniqueComponents.map(comp => ({ value: comp, label: comp }))
                        ]}
                        style={{ minWidth: 150 }}
                    />
                    
                    <TextInput
                        label="Search"
                        placeholder="Search logs..."
                        icon={<IconSearch size={14} />}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.currentTarget.value)}
                        style={{ flex: 1 }}
                    />
                    
                    <NumberInput
                        label="Max Logs"
                        value={maxLogs}
                        onChange={(value) => setMaxLogs(value || 100)}
                        min={10}
                        max={1000}
                        step={10}
                        style={{ width: 100 }}
                    />
                </Group>

                {/* Controls */}
                <Group spacing="xs">
                    <Switch
                        label="Auto-scroll"
                        checked={autoScroll}
                        onChange={(e) => setAutoScroll(e.currentTarget.checked)}
                    />
                    
                    <Tooltip label="Refresh logs">
                        <ActionIcon onClick={refreshLogs}>
                            <IconRefresh size={16} />
                        </ActionIcon>
                    </Tooltip>
                    
                    <Tooltip label="Export logs">
                        <ActionIcon onClick={exportLogs}>
                            <IconDownload size={16} />
                        </ActionIcon>
                    </Tooltip>
                    
                    <Tooltip label="Clear all logs">
                        <ActionIcon c="red" onClick={clearLogs}>
                            <IconTrash size={16} />
                        </ActionIcon>
                    </Tooltip>
                </Group>

                <Divider />

                {/* Log entries */}
                <ScrollArea 
                    style={{ flex: 1 }} 
                    viewportRef={scrollRef}
                    scrollbarSize={6}
                >
                    <Stack spacing="xs">
                        {filteredLogs.length === 0 ? (
                            <Alert icon={<IconInfoCircle size={16} />} c="blue">
                                No logs match the current filters.
                            </Alert>
                        ) : (
                            filteredLogs.map((log) => {
                                const isExpanded = expandedLogs.has(log.id);
                                const hasDetails = log.details || log.stack;
                                
                                return (
                                    <Paper key={log.id} p="xs" withBorder radius="sm">
                                        <Group justify="space-between" spacing="xs">
                                            <Group spacing="xs" style={{ flex: 1 }}>
                                                {hasDetails && (
                                                    <ActionIcon
                                                        size="xs"
                                                        onClick={() => toggleLogExpansion(log.id)}
                                                    >
                                                        {isExpanded ? 
                                                            <IconChevronDown size={12} /> : 
                                                            <IconChevronRight size={12} />
                                                        }
                                                    </ActionIcon>
                                                )}
                                                
                                                <Badge
                                                    c={getLogLevelColor(log.level)}
                                                    size="xs"
                                                    leftSection={getLogLevelIcon(log.level)}
                                                >
                                                    {log.level.toUpperCase()}
                                                </Badge>
                                                
                                                <Text size="xs" c="dimmed" style={{ minWidth: 80 }}>
                                                    {formatTimestamp(log.timestamp)}
                                                </Text>
                                                
                                                {log.component && (
                                                    <Badge size="xs" variant="outline">
                                                        {log.component}
                                                    </Badge>
                                                )}
                                                
                                                <Text size="sm" style={{ flex: 1 }}>
                                                    {log.message}
                                                </Text>
                                            </Group>
                                            
                                            <Tooltip label="Copy log entry">
                                                <ActionIcon
                                                    size="xs"
                                                    onClick={() => copyLogToClipboard(log)}
                                                >
                                                    <IconCopy size={12} />
                                                </ActionIcon>
                                            </Tooltip>
                                        </Group>
                                        
                                        {hasDetails && (
                                            <Collapse in={isExpanded}>
                                                <Stack spacing="xs" mt="xs">
                                                    {log.details && (
                                                        <div>
                                                            <Text size="xs" fw={500} c="dimmed">Details:</Text>
                                                            <Code block size="xs">
                                                                {typeof log.details === 'string' 
                                                                    ? log.details 
                                                                    : JSON.stringify(log.details, null, 2)
                                                                }
                                                            </Code>
                                                        </div>
                                                    )}
                                                    
                                                    {log.stack && (
                                                        <div>
                                                            <Text size="xs" fw={500} c="dimmed">Stack Trace:</Text>
                                                            <Code block size="xs">
                                                                {log.stack}
                                                            </Code>
                                                        </div>
                                                    )}
                                                </Stack>
                                            </Collapse>
                                        )}
                                    </Paper>
                                );
                            })
                        )}
                    </Stack>
                </ScrollArea>

                {/* Footer */}
                <Group justify="space-between">
                    <Text size="xs" c="dimmed">
                        Showing {filteredLogs.length} of {logs.length} logs
                    </Text>
                    <Button variant="outline" onClick={onClose}>
                        Close
                    </Button>
                </Group>
            </Stack>
        </Modal>
    );
}

