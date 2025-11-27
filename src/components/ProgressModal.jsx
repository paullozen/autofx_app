import React from 'react';
import { Square, Loader2 } from 'lucide-react';

const ProgressModal = ({ progress, onStop }) => {
    if (!progress) return null;

    const { desc, current, total } = progress;
    const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100]">
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-800 p-6 w-full max-w-md transform transition-all">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                        Processing...
                    </h3>
                    <div className="text-sm font-medium text-gray-500 dark:text-gray-400">
                        {percentage}%
                    </div>
                </div>

                <div className="mb-2">
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-2 truncate" title={desc}>
                        {desc}
                    </p>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
                        <div
                            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
                            style={{ width: `${percentage}%` }}
                        ></div>
                    </div>
                </div>

                <div className="flex items-center justify-between mt-4">
                    <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                        {current} / {total} items
                    </span>

                    <button
                        onClick={onStop}
                        className="px-3 py-1.5 bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50 rounded-md text-xs font-medium transition-colors flex items-center gap-1"
                    >
                        <Square className="w-3 h-3 fill-current" />
                        Stop Process
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ProgressModal;
