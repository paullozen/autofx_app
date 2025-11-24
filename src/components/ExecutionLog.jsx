import React, { useEffect, useRef, useState } from 'react';
import { Trash2, Send, FolderOpen, Square } from 'lucide-react';

const ExecutionLog = ({ logs = [], onClearLogs, onSendInput, currentScript, outputFolder, onOpenFolder, onStop, isProcessing }) => {
    const logEndRef = useRef(null);
    const [terminalInput, setTerminalInput] = useState('');

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const handleSendInput = (e) => {
        e.preventDefault();
        if (onSendInput && terminalInput !== undefined) {
            onSendInput(terminalInput);
            setTerminalInput('');
        }
    };

    return (
        <div className="bg-gray-900 text-gray-200 flex flex-col h-full border-b border-gray-800 transition-all duration-300">
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                <div className="flex items-center space-x-4">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                        Execution Log
                    </h3>

                    <div className="flex items-center space-x-2 border-l border-gray-700 pl-4">
                        <button
                            onClick={onStop}
                            disabled={!isProcessing}
                            className={`flex items-center space-x-1 text-xs transition-colors ${isProcessing
                                    ? 'text-red-400 hover:text-red-300 cursor-pointer'
                                    : 'text-gray-600 cursor-not-allowed'
                                }`}
                            title="Stop execution"
                        >
                            <Square className="w-3 h-3 fill-current" />
                            <span>Stop</span>
                        </button>

                        <button
                            onClick={onClearLogs}
                            className="flex items-center space-x-1 text-xs text-gray-400 hover:text-white transition-colors"
                        >
                            <Trash2 className="w-3 h-3" />
                            <span>Clear</span>
                        </button>
                    </div>
                </div>

                <div className="flex items-center space-x-2">
                    {outputFolder && (
                        <button
                            onClick={() => onOpenFolder(outputFolder)}
                            className="flex items-center space-x-1 text-xs text-green-400 hover:text-green-300 transition-colors"
                            title="Open output folder"
                        >
                            <FolderOpen className="w-3 h-3" />
                            <span>Open Folder</span>
                        </button>
                    )}
                </div>
            </div>

            <div className="flex-1 p-4 overflow-y-auto font-mono text-sm space-y-1 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                {logs.length === 0 && (
                    <div className="text-gray-500 italic mb-2">&gt; Ready...</div>
                )}

                {logs.map((log, index) => (
                    <div
                        key={index}
                        className={`flex space-x-2 px-2 py-0.5 rounded ${currentScript ? 'bg-blue-900/10' : ''}`}
                    >
                        <span className="text-gray-500 flex-shrink-0 select-none">&gt;</span>
                        <span className="whitespace-pre-wrap break-all">{log}</span>
                    </div>
                ))}

                {/* Input Field at the bottom, following logs */}
                <form onSubmit={handleSendInput} className="flex items-center px-2 py-1 mt-2 group bg-green-900/20 rounded border border-green-900/30">
                    <span className="text-green-400 mr-2 font-bold animate-pulse select-none">&gt;</span>
                    <input
                        type="text"
                        value={terminalInput}
                        onChange={(e) => setTerminalInput(e.target.value)}
                        className="flex-1 bg-transparent text-green-300 font-mono text-sm outline-none placeholder-green-700"
                        placeholder="Type command..."
                        autoFocus
                    />
                </form>

                <div ref={logEndRef} />
            </div>
        </div>
    );
};

export default ExecutionLog;
