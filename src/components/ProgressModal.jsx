import React from 'react';
import { Square, Loader2 } from 'lucide-react';

const ProgressModal = ({ progress, onStop }) => {
    const profiles = Object.keys(progress || {});
    if (profiles.length === 0) return null;

    // Calculate global totals
    const globalCurrent = profiles.reduce((acc, p) => acc + progress[p].current, 0);
    const globalTotal = profiles.reduce((acc, p) => acc + progress[p].total, 0);
    const globalPercentage = globalTotal > 0 ? Math.round((globalCurrent / globalTotal) * 100) : 0;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100]">
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-800 p-6 w-full max-w-md transform transition-all">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                        Processing Images
                    </h3>
                    <div className="flex flex-col items-end">
                        <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                            {globalCurrent} <span className="text-sm text-gray-400 font-normal">/ {globalTotal}</span>
                        </span>
                        <span className="text-xs text-gray-500 uppercase tracking-wider">Total Images</span>
                    </div>
                </div>

                <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar">
                    {profiles.map(profile => {
                        const pData = progress[profile];
                        const percentage = pData.total > 0 ? Math.round((pData.current / pData.total) * 100) : 0;

                        return (
                            <div key={profile} className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 border border-gray-100 dark:border-gray-800">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="font-medium text-sm text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-green-500"></div>
                                        {profile}
                                    </span>
                                    <span className="text-xs font-mono text-gray-500">
                                        {pData.current}/{pData.total}
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                                        style={{ width: `${percentage}%` }}
                                    ></div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className="flex items-center justify-end mt-6 pt-4 border-t border-gray-100 dark:border-gray-800">
                    <button
                        onClick={onStop}
                        className="px-4 py-2 bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                    >
                        <Square className="w-4 h-4 fill-current" />
                        Stop All Processes
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ProgressModal;
