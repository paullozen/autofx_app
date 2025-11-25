import React, { useState, useEffect } from 'react';
import { X, Check, Eraser } from 'lucide-react';

// Tabbed modal for editing API keys per category
const categories = {
    GPT: ['OPENAI_API_KEY', 'OPENAI_MODEL'],
    GENAIPRO: ['GENAIPRO_API_KEY'],
    YOUTUBE: ['YT_API_KEY', 'YOUTUBE_CHANNEL_ID'],
    NOTION: ['NOTION_TOKEN', 'NOTION_DATABASE_ID', 'NOTION_DATA_SOURCE_ID'],
};

const ApiKeyModal = ({ onClose }) => {
    const initialKeys = {
        OPENAI_API_KEY: '',
        OPENAI_MODEL: '',
        NOTION_TOKEN: '',
        NOTION_DATABASE_ID: '',
        NOTION_DATA_SOURCE_ID: '',
        YT_API_KEY: '',
        YOUTUBE_CHANNEL_ID: '',
        GENAIPRO_API_KEY: '',
    };

    const [keys, setKeys] = useState(initialKeys);
    const [originalKeys, setOriginalKeys] = useState({});
    const [activeTab, setActiveTab] = useState('GPT');
    const [successField, setSuccessField] = useState(null);

    useEffect(() => {
        fetchKeys();
    }, []);

    const fetchKeys = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/env');
            const data = await response.json();
            if (data.success) {
                // Merge fetched keys with initialKeys to ensure all fields exist
                const newKeys = { ...initialKeys, ...data.keys };
                setKeys(newKeys);
                setOriginalKeys(data.keys);
            }
        } catch (error) {
            console.error('Error fetching keys:', error);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setKeys((prev) => ({ ...prev, [name]: value }));
    };

    const handleInsert = async (field) => {
        const value = keys[field];
        // Prevent saving if value hasn't changed (is still the masked version)
        if (value === originalKeys[field]) {
            return;
        }

        if (!value) {
            return;
        }

        try {
            const response = await fetch('http://localhost:3001/api/env', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: field, value })
            });
            const data = await response.json();
            if (data.success) {
                setSuccessField(field);
                setTimeout(() => setSuccessField(null), 2000);
                fetchKeys(); // Refresh to get the masked version back if needed, or just update original
            } else {
                console.error(`Error saving key: ${data.error} `);
            }
        } catch (error) {
            console.error('Error saving key:', error);
        }
    };

    const handleClear = async (field) => {
        if (!confirm(`Are you sure you want to delete ${field}?`)) return;

        try {
            const response = await fetch(`http://localhost:3001/api/env/${field}`, {
                method: 'DELETE',
            });
            const data = await response.json();
            if (data.success) {
                setKeys(prev => ({ ...prev, [field]: '' }));
                setOriginalKeys(prev => ({ ...prev, [field]: '' }));
            } else {
                console.error(`Error deleting key: ${data.error}`);
            }
        } catch (error) {
            console.error('Error deleting key:', error);
        }
    };

    return (
        <div className="flex-1 bg-transparent p-8 transition-colors duration-300">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 w-full max-w-4xl mx-auto p-6 relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                    <X className="w-5 h-5" />
                </button>
                <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-gray-100">API Key</h2>
                {/* Tabs */}
                <div className="flex space-x-2 mb-6 overflow-x-auto pb-2">
                    {Object.keys(categories).map((cat) => (
                        <button
                            key={cat}
                            onClick={() => setActiveTab(cat)}
                            className={`px-4 py-2 rounded-md font-medium transition-colors ${activeTab === cat
                                ? 'bg-blue-600 text-white shadow-sm'
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'}`}
                        >
                            {cat}
                        </button>
                    ))}
                </div>
                {/* Fields for active tab */}
                <div className="space-y-4">
                    {categories[activeTab].map((field) => (
                        <div key={field} className="flex items-center space-x-3">
                            <label className="w-48 text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor={field}>{field}</label>
                            <div className="flex-1 flex space-x-2">
                                <input
                                    id={field}
                                    name={field}
                                    type="text"
                                    value={keys[field]}
                                    onChange={handleChange}
                                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-800 dark:border-gray-700 text-gray-900 dark:text-gray-100"
                                    placeholder="Enter value"
                                />
                                <button
                                    onClick={() => handleInsert(field)}
                                    className={`px-3 py-2 text-white rounded-md transition-colors text-sm font-medium ${successField === field ? 'bg-green-700' : 'bg-green-600 hover:bg-green-700'}`}
                                    title="Save"
                                >
                                    <Check className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => handleClear(field)}
                                    className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
                                    title="Clear"
                                >
                                    <Eraser className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ApiKeyModal;
