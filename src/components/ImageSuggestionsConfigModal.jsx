import React, { useState, useEffect } from 'react';
import { X, Save, FileText, Image as ImageIcon } from 'lucide-react';

const ImageSuggestionsConfigModal = ({ onClose }) => {
    const [scenePrompt, setScenePrompt] = useState('');
    const [imagePattern, setImagePattern] = useState('');
    const [loading, setLoading] = useState(true);
    const [savingScene, setSavingScene] = useState(false);
    const [savingPattern, setSavingPattern] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [sceneRes, patternRes] = await Promise.all([
                    fetch('http://localhost:3001/api/prompts/Scene_Suggestion.txt'),
                    fetch('http://localhost:3001/api/prompts/IMG_PATTERNS.txt')
                ]);

                const sceneData = await sceneRes.json();
                const patternData = await patternRes.json();

                if (sceneData.success) setScenePrompt(sceneData.content);
                if (patternData.success) setImagePattern(patternData.content);
            } catch (error) {
                console.error('Error fetching prompts:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleSaveScene = async () => {
        setSavingScene(true);
        try {
            await fetch('http://localhost:3001/api/prompts/Scene_Suggestion.txt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: scenePrompt })
            });
        } catch (error) {
            console.error('Error saving scene prompt:', error);
        } finally {
            setSavingScene(false);
        }
    };

    const handleSavePattern = async () => {
        setSavingPattern(true);
        try {
            await fetch('http://localhost:3001/api/prompts/IMG_PATTERNS.txt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: imagePattern })
            });
        } catch (error) {
            console.error('Error saving image pattern:', error);
        } finally {
            setSavingPattern(false);
        }
    };

    return (
        <div className="fixed inset-0 flex items-center justify-center z-[100] pointer-events-none">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-800 w-11/12 max-w-5xl p-6 pointer-events-auto max-h-[90vh] overflow-y-auto flex flex-col">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <ImageIcon className="w-6 h-6 text-blue-600" />
                        Image Suggestions Configuration
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {loading ? (
                    <div className="flex-1 flex items-center justify-center min-h-[300px]">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1">
                        {/* Scene Suggestions Prompt */}
                        <div className="flex flex-col h-full">
                            <div className="flex items-center justify-between mb-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                    <FileText className="w-4 h-4" />
                                    Scene Suggestions Prompt
                                </label>
                                <button
                                    onClick={handleSaveScene}
                                    disabled={savingScene}
                                    className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium text-white transition-colors ${savingScene ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
                                        }`}
                                >
                                    <Save className="w-4 h-4" />
                                    {savingScene ? 'Saving...' : 'Save'}
                                </button>
                            </div>
                            <textarea
                                value={scenePrompt}
                                onChange={(e) => setScenePrompt(e.target.value)}
                                className="flex-1 w-full p-4 border border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-mono text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none min-h-[400px]"
                                placeholder="Enter prompt for generating scene suggestions..."
                            />
                            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                                This prompt defines how the AI should generate scene descriptions from the script.
                            </p>
                        </div>

                        {/* Image Pattern */}
                        <div className="flex flex-col h-full">
                            <div className="flex items-center justify-between mb-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                    <ImageIcon className="w-4 h-4" />
                                    Image Pattern
                                </label>
                                <button
                                    onClick={handleSavePattern}
                                    disabled={savingPattern}
                                    className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium text-white transition-colors ${savingPattern ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
                                        }`}
                                >
                                    <Save className="w-4 h-4" />
                                    {savingPattern ? 'Saving...' : 'Save'}
                                </button>
                            </div>
                            <textarea
                                value={imagePattern}
                                onChange={(e) => setImagePattern(e.target.value)}
                                className="flex-1 w-full p-4 border border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-mono text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none min-h-[400px]"
                                placeholder="Enter image generation pattern..."
                            />
                            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                                This pattern defines the style and negative prompts for the image generator.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ImageSuggestionsConfigModal;
