import React from 'react';
import Sidebar from './Sidebar';
import ExecutionLog from './ExecutionLog';
import MainPanel from './MainPanel';

const Layout = ({ selectedStage, onSelectStage, logs, onClearLogs, theme, toggleTheme, onExecuteScript, profiles, onSendInput, onDeleteProfile, currentScript, outputFolder, onOpenFolder, onStop, isProcessing }) => {
    return (
        <div className="flex h-screen bg-gray-50 overflow-hidden dark:bg-gray-950 transition-colors duration-300">
            {/* Left Section: Sidebar */}
            <Sidebar selectedStage={selectedStage} onSelectStage={onSelectStage} theme={theme} toggleTheme={toggleTheme} />

            {/* Right Section: Terminal is always visible */}
            <div className="flex flex-col flex-1 overflow-hidden relative">
                {/* Terminal takes full height */}
                <div className="flex-1 flex flex-col h-full">
                    <ExecutionLog
                        logs={logs}
                        onClearLogs={onClearLogs}
                        onSendInput={onSendInput}
                        currentScript={currentScript}
                        outputFolder={outputFolder}
                        onOpenFolder={onOpenFolder}
                        onStop={onStop}
                        isProcessing={isProcessing}
                    />
                </div>

                {/* Configuration Modal Overlay */}
                {selectedStage && (
                    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-8">
                        <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-transparent shadow-2xl rounded-xl">
                            <MainPanel
                                selectedStage={selectedStage}
                                onExecuteScript={(script, args) => {
                                    onExecuteScript(script, args);
                                    onSelectStage(null); // Close modal on execute
                                }}
                                profiles={profiles}
                                onDeleteProfile={onDeleteProfile}
                                onClose={() => onSelectStage(null)} // Pass close handler
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Layout;
