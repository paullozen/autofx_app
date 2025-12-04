import { useEffect } from 'react';

export const useWebSocket = ({
    onLog,
    onProgress,
    onProcessClose,
    onOutputFolder,
    currentScript
}) => {
    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = process.env.NODE_ENV === 'production'
            ? `${protocol}//${window.location.host}`
            : 'ws://localhost:3001';

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('Connected to WebSocket');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'stdout') {
                    const lines = data.output.split('\n');
                    lines.forEach(rawLine => {
                        const line = rawLine.trimEnd();

                        // Check for tagged JSON progress message
                        const progressMatch = line.match(/<<PROGRESS>>(.+?)<<PROGRESS>>/);
                        if (progressMatch) {
                            try {
                                const progData = JSON.parse(progressMatch[1]);
                                onProgress(progData);
                                // Remove the progress part from the line so we don't log it
                                const remainingLine = line.replace(progressMatch[0], '').trim();
                                if (remainingLine) onLog(remainingLine);
                                return; // Prevent further processing of this line if progress was handled
                            } catch (e) {
                                // If parse fails, just log the original line later
                            }
                        }

                        if (line || rawLine === '') {
                            if (line) onLog(line);
                        }

                        // Extract folder path
                        if (line && (line.includes('salvas em:') || line.includes('salvos em') || line.includes('compactados em:'))) {
                            const match = line.match(/(?:em:|em)\s+(.+?)(?:\s|$)/);
                            if (match) {
                                const filePath = match[1].trim();
                                const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
                                if (folderPath) {
                                    onOutputFolder(folderPath);
                                }
                            }
                        }
                    });
                } else if (data.type === 'stderr') {
                    onLog(data.output);
                } else if (data.type === 'close') {
                    onLog(`Process finished with code ${data.code}`);
                    onProcessClose(data.code);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        return () => {
            ws.close();
        };
    }, [currentScript, onLog, onProgress, onProcessClose, onOutputFolder]);
};
