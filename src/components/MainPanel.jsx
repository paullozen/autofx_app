import React, { useState } from 'react';
import { Camera, Mail, Lock, User, Plus, FolderOpen, Trash2, X, Settings } from 'lucide-react';
import ApiKeyModal from './ApiKeyModal';
import ImageSuggestionsConfigModal from './ImageSuggestionsConfigModal';

const MainPanel = ({ selectedStage, onExecuteScript, profiles = [], onDeleteProfile, onClose }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [profileName, setProfileName] = useState('');

    // Channel Info states
    const [mode, setMode] = useState('channel');
    const [channelHandle, setChannelHandle] = useState('');
    const [orderByPopularity, setOrderByPopularity] = useState(false);
    const [collectionType, setCollectionType] = useState('general');
    const [maxVideos, setMaxVideos] = useState('');
    const [maxComments, setMaxComments] = useState('');
    const [videoInput, setVideoInput] = useState('');

    // Get Scripts states
    const [showAddScript, setShowAddScript] = useState(false);
    const [scriptText, setScriptText] = useState('');
    const [filename, setFilename] = useState('');

    if (selectedStage === 'login') {
        return (
            <div className="flex-1 flex flex-col items-center justify-center bg-transparent p-8 transition-colors duration-300">
                <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8 dark:bg-gray-900 dark:border dark:border-gray-800 relative">
                    <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                        <X className="w-5 h-5" />
                    </button>
                    <div className="flex justify-center mb-6">
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                            {isLogin ? 'Welcome Back' : 'Create Account'}
                        </h2>
                    </div>
                    <p className="text-gray-500 dark:text-gray-400 text-center mb-8">
                        {isLogin ? 'Enter your credentials to access your pipeline.' : 'Sign up to start automating your content.'}
                    </p>

                    <form className="space-y-4">
                        {!isLogin && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                    <input
                                        type="text"
                                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                                        placeholder="John Doe"
                                    />
                                </div>
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                <input
                                    type="email"
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                                    placeholder="you@example.com"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                <input
                                    type="password"
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
                        >
                            {isLogin ? 'Sign In' : 'Create Account'}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-sm">
                        <span className="text-gray-500 dark:text-gray-400">
                            {isLogin ? "Don't have an account? " : "Already have an account? "}
                        </span>
                        <button
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-blue-600 hover:text-blue-500 font-medium dark:text-blue-400"
                        >
                            {isLogin ? 'Sign up' : 'Log in'}
                        </button>
                    </div>
                </div>
            </div >
        );
    }

    if (selectedStage === 'api_key') {
        return <ApiKeyModal onClose={onClose} />;
    }

    if (selectedStage === 'profile_generator') {
        const handleCreateProfile = (e) => {
            e.preventDefault();
            if (profileName.trim()) {
                onExecuteScript('profile_generator', profileName);
                setProfileName('');
            }
        };

        return (
            <div className="flex-1 bg-gray-50 p-8 dark:bg-gray-950 transition-colors duration-300">
                <div className="grid grid-cols-2 gap-6 h-full">
                    {/* Configuration Panel */}
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 dark:bg-gray-900 dark:border-gray-800">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4 dark:text-white">
                            Create Profile
                        </h2>
                        <p className="text-gray-500 dark:text-gray-400 mb-6">
                            Create a new profile for your YouTube content pipeline.
                        </p>

                        <form onSubmit={handleCreateProfile} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    New Profile Name
                                </label>
                                <div className="flex gap-2">
                                    <div className="relative flex-1">
                                        <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                        <input
                                            type="text"
                                            value={profileName}
                                            onChange={(e) => setProfileName(e.target.value)}
                                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                                            placeholder="Enter profile name..."
                                        />
                                    </div>
                                    <button
                                        type="submit"
                                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium flex items-center space-x-2"
                                    >
                                        <Plus className="w-4 h-4" />
                                        <span>Create</span>
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setProfileName('')}
                                        className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 transition-colors"
                                    >
                                        Clear
                                    </button>
                                </div>
                            </div>

                            {/* Info message */}
                            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
                                <p className="text-sm text-blue-800 dark:text-blue-300">
                                    💡 <strong>Attention:</strong> After the browser opens, configure your profile. When finished, simply <strong>close the browser window</strong> to complete the setup.
                                </p>
                            </div>
                        </form>
                    </div>

                    {/* Profiles List Panel */}
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 dark:bg-gray-900 dark:border-gray-800">
                        <h3 className="text-xl font-bold text-gray-900 mb-4 dark:text-white">
                            Existing Profiles
                        </h3>

                        {profiles.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                                <FolderOpen className="w-16 h-16 mb-4" />
                                <p className="text-sm">No profiles created yet</p>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {profiles.map((profile, index) => (
                                    <div
                                        key={index}
                                        className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-2">
                                                <User className="w-4 h-4 text-gray-500" />
                                                <span className="text-gray-900 dark:text-white font-medium">
                                                    {profile}
                                                </span>
                                            </div>
                                            <button
                                                onClick={() => onDeleteProfile && onDeleteProfile(profile)}
                                                className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 transition-colors"
                                                title="Delete profile"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }



    if (selectedStage === 'get_scripts') {
        const handleStart = (e) => {
            e.preventDefault();
            onExecuteScript('get_scripts', '');
        };

        const handleAdd = (e) => {
            e.preventDefault();
            fetch('http://localhost:3001/save-script', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: scriptText, filename: filename })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        setScriptText('');
                        setFilename('');
                        setShowAddScript(false);
                        alert(`Script salvo com sucesso: ${data.file}`);
                    } else {
                        alert(`Erro ao salvar script: ${data.error}`);
                    }
                })
                .catch(err => {
                    console.error('Error saving script:', err);
                    alert('Erro de conexão ao tentar salvar o script.');
                });
        };

        return (
            <div className="flex-1 bg-transparent p-8 transition-colors duration-300">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 h-full dark:bg-gray-900 dark:border-gray-800 relative">
                    <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                        <X className="w-5 h-5" />
                    </button>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6 dark:text-white">Get Scripts</h2>

                    {!showAddScript ? (
                        <div className="flex flex-col space-y-6 max-w-2xl">
                            {/* Start Option */}
                            <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                                <button onClick={handleStart}
                                    className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-bold shadow-sm min-w-[140px]">
                                    Start
                                </button>
                                <div className="flex flex-col">
                                    <span className="text-gray-900 font-medium dark:text-white">Download from Notion</span>
                                    <span className="text-sm text-gray-500 dark:text-gray-400">Download scripts stored in Notion database</span>
                                </div>
                            </div>

                            {/* Add Script Option */}
                            <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                                <button onClick={() => setShowAddScript(true)}
                                    className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 hover:text-blue-600 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:hover:bg-gray-600 transition-colors font-bold shadow-sm min-w-[140px] flex items-center justify-center space-x-2">
                                    <Plus className="w-4 h-4" />
                                    <span>Add Script</span>
                                </button>
                                <div className="flex flex-col">
                                    <span className="text-gray-900 font-medium dark:text-white">Manual Entry</span>
                                    <span className="text-sm text-gray-500 dark:text-gray-400">Manually add a script to the inbox</span>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <form onSubmit={handleAdd} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Filename (optional)
                                </label>
                                <input
                                    type="text"
                                    value={filename}
                                    onChange={e => setFilename(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                                    placeholder="my_script_name"
                                />
                                <p className="text-xs text-gray-500 mt-1">If empty, a timestamp will be used.</p>
                            </div>
                            <textarea
                                value={scriptText}
                                onChange={e => setScriptText(e.target.value)}
                                className="w-full h-48 p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                                placeholder="Paste your script here..."
                                required
                            />
                            <div className="flex space-x-4">
                                <button type="submit"
                                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
                                    Save
                                </button>
                                <button type="button"
                                    onClick={() => setShowAddScript(false)}
                                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 transition-colors">
                                    Cancel
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        );
    }

    // Image Suggestions - Special handler with Add Suggestions option
    if (selectedStage === 'suggestion_generator') {
        const [showAddDialog, setShowAddDialog] = useState(false);
        const [showConfigModal, setShowConfigModal] = useState(false);
        const [suggestionTitle, setSuggestionTitle] = useState('');
        const [suggestionContent, setSuggestionContent] = useState('');

        const handleStartProcess = (e) => {
            e.preventDefault();
            onExecuteScript(selectedStage, '');
        };

        const formatSuggestions = (rawContent) => {
            // Split by lines and filter out empty lines
            const lines = rawContent.split('\n').map(line => line.trim()).filter(line => line);

            const formatted = [];
            let sceneNumber = 1;

            for (const line of lines) {
                // If line starts with "Suggestion:", add scene number
                if (line.toLowerCase().startsWith('suggestion:')) {
                    formatted.push(`Scene ${sceneNumber}`);
                    formatted.push(line);
                    formatted.push(''); // Empty line between scenes
                    sceneNumber++;
                } else if (line.toLowerCase().startsWith('scene ')) {
                    // If user already added scene numbers, keep them
                    formatted.push(line);
                } else {
                    // Any other line, just add it
                    formatted.push(line);
                }
            }

            return formatted.join('\n');
        };

        const handleAddSuggestion = async () => {
            if (!suggestionTitle.trim() || !suggestionContent.trim()) {
                alert('Please fill in both title and suggestions');
                return;
            }

            // Format the suggestions with Scene numbers
            const formattedContent = formatSuggestions(suggestionContent);
            console.log('Formatted content:', formattedContent);

            try {
                const payload = {
                    baseName: suggestionTitle.trim(),
                    suggestions: formattedContent
                };
                console.log('Sending payload:', payload);

                // Save suggestions to backend
                const response = await fetch('http://localhost:3001/api/save-manual-suggestions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                });

                console.log('Response status:', response.status);
                console.log('Response ok:', response.ok);

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('Error response:', errorText);
                    throw new Error(`Failed to save suggestions: ${response.status}`);
                }

                const result = await response.json();
                console.log('Success result:', result);

                // Close dialog and reset
                setShowAddDialog(false);
                setSuggestionTitle('');
                setSuggestionContent('');

                // Execute manual_suggestions script
                onExecuteScript('manual_suggestions', '');

            } catch (error) {
                console.error('Error saving suggestions:', error);
                alert(`Failed to save suggestions. Please try again.\nError: ${error.message}`);
            }
        };

        return (
            <div className="flex-1 bg-transparent p-8 transition-colors duration-300">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 h-full dark:bg-gray-900 dark:border-gray-800 relative">
                    <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                        <X className="w-5 h-5" />
                    </button>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6 dark:text-white">Image Suggestions</h2>

                    {!showAddDialog ? (
                        <div className="flex flex-col space-y-6 max-w-2xl">
                            {/* Start Option */}
                            <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                                <button onClick={handleStartProcess}
                                    className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-bold shadow-sm min-w-[140px]">
                                    Start Process
                                </button>
                                <div className="flex flex-col">
                                    <span className="text-gray-900 font-medium dark:text-white">Generate Suggestions</span>
                                    <span className="text-sm text-gray-500 dark:text-gray-400">Create image prompts from scripts</span>
                                </div>
                            </div>

                            {/* Add Manual Suggestions Option */}
                            <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                                <button onClick={() => setShowAddDialog(true)}
                                    className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 hover:text-blue-600 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:hover:bg-gray-600 transition-colors font-bold shadow-sm min-w-[140px] flex items-center justify-center space-x-2">
                                    <Plus className="w-4 h-4" />
                                    <span>Add Manual</span>
                                </button>
                                <div className="flex flex-col">
                                    <span className="text-gray-900 font-medium dark:text-white">Manual Entry</span>
                                    <span className="text-sm text-gray-500 dark:text-gray-400">Manually add suggestions for a script</span>
                                </div>
                            </div>

                            {/* Configuration Option */}
                            <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                                <button onClick={() => setShowConfigModal(true)}
                                    className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 hover:text-blue-600 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:hover:bg-gray-600 transition-colors font-bold shadow-sm min-w-[140px] flex items-center justify-center space-x-2">
                                    <Settings className="w-4 h-4" />
                                    <span>Config</span>
                                </button>
                                <div className="flex flex-col">
                                    <span className="text-gray-900 font-medium dark:text-white">Configuration</span>
                                    <span className="text-sm text-gray-500 dark:text-gray-400">Edit prompts and image patterns</span>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="max-w-4xl mx-auto">
                            <div className="mb-4 flex items-center justify-between">
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Add Manual Suggestions</h3>
                                <button
                                    onClick={() => setShowAddDialog(false)}
                                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Base Name (e.g., script_name)
                                    </label>
                                    <input
                                        type="text"
                                        value={suggestionTitle}
                                        onChange={e => setSuggestionTitle(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                                        placeholder="my_video_script"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Suggestions Content
                                    </label>
                                    <textarea
                                        value={suggestionContent}
                                        onChange={e => setSuggestionContent(e.target.value)}
                                        className="w-full h-64 p-4 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white font-mono text-sm"
                                        placeholder="Paste your suggestions here..."
                                    />
                                    <p className="text-xs text-gray-500 mt-1">
                                        Format: Suggestion: [prompt]
                                    </p>
                                </div>
                                <div className="flex space-x-4 pt-4">
                                    <button onClick={handleAddSuggestion}
                                        className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium">
                                        Save Suggestions
                                    </button>
                                    <button onClick={() => setShowAddDialog(false)}
                                        className="px-6 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 transition-colors font-medium">
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {showConfigModal && (
                        <ImageSuggestionsConfigModal onClose={() => setShowConfigModal(false)} />
                    )}
                </div>
            </div>
        );
    }

    // Generic handler for other pipeline stages
    if (['audio_generator', 'audio_downloader', 'srt_generator', 'image_generator', 'make_and_render', 'clean_bases', 'channel_info'].includes(selectedStage)) {
        const handleStart = (e) => {
            e.preventDefault();
            onExecuteScript(selectedStage, '');
        };

        return (
            <div className="flex-1 bg-transparent p-8 transition-colors duration-300">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 dark:bg-gray-900 dark:border-gray-800 max-w-4xl mx-auto relative">
                    <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                        <X className="w-5 h-5" />
                    </button>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6 capitalize dark:text-white">
                        {selectedStage.replace(/_/g, ' ')}
                    </h2>

                    <div className="p-6 bg-gray-50 rounded-lg border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                        <p className="text-gray-600 dark:text-gray-300 mb-6">
                            Click the button below to start the <strong>{selectedStage.replace(/_/g, ' ')}</strong> process.
                            Follow the instructions in the terminal below.
                        </p>

                        <button
                            onClick={handleStart}
                            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-bold shadow-sm flex items-center space-x-2"
                        >
                            <div className="w-3 h-3 bg-white rounded-full animate-pulse mr-2"></div>
                            <span>Start Process</span>
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (!selectedStage) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 text-center p-8 dark:bg-gray-950 transition-colors duration-300">
                <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm mb-6 dark:bg-gray-800 dark:text-gray-200">
                    <Camera className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2 dark:text-white">
                    Content Production Pipeline
                </h2>
                <p className="text-gray-500 max-w-md dark:text-gray-400">
                    Select a pipeline stage from the sidebar to configure and execute.
                </p>
            </div>
        );
    }

    return (
        <div className="flex-1 bg-gray-50 p-8 dark:bg-gray-950 transition-colors duration-300">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 h-full dark:bg-gray-900 dark:border-gray-800">
                <h2 className="text-2xl font-bold text-gray-900 mb-4 capitalize dark:text-white">
                    {selectedStage.replace(/-/g, ' ')}
                </h2>
                <div className="text-gray-500 dark:text-gray-400">
                    Stage configuration for <span className="font-medium text-gray-900 dark:text-white">{selectedStage}</span> will appear here.
                </div>
            </div>
        </div>
    );
};

export default MainPanel;
