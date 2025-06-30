// This script will fix the QueueManager.tsx file
const fs = require('fs');

let content = fs.readFileSync('src/components/QueueManager.tsx', 'utf8');

// Add a helper function for move operations after handleRemove
const handleRemoveEnd = content.indexOf('        } finally {\n            setLoading(prev => ({ ...prev, [downloadId]: false }));\n        }\n    };');
const insertPoint = content.indexOf('\n', handleRemoveEnd + 100) + 1;

const moveHandlerFunction = `
    const handleMoveDownload = async (downloadId: number, direction: 'up' | 'down', currentIndex: number) => {
        try {
            const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
            await downloadService.reorderQueue(downloadId, newIndex);
            await fetchDownloads();
            showNotification({
                title: 'Success',
                message: \`Download moved \${direction}\`,
                color: 'green',
            });
        } catch (error) {
            console.error('Failed to move download:', error);
            showNotification({
                title: 'Error',
                message: 'Failed to move download',
                color: 'red',
            });
        }
    };
`;

content = content.slice(0, insertPoint) + moveHandlerFunction + content.slice(insertPoint);

// Replace the onClick handlers for Move Up
content = content.replace(
    /onClick=\{\(\) => downloadService\.reorderQueue\(download\.id, index - 1\)\}/g,
    'onClick={() => handleMoveDownload(download.id, "up", index)}'
);

// Replace the onClick handlers for Move Down  
content = content.replace(
    /onClick=\{\(\) => downloadService\.reorderQueue\(download\.id, index \+ 1\)\}/g,
    'onClick={() => handleMoveDownload(download.id, "down", index)}'
);

fs.writeFileSync('src/components/QueueManager.tsx', content);
console.log('QueueManager.tsx fixed successfully');
