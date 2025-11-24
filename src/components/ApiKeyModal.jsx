import React, { useState } from 'react';

// Tabbed modal for editing API keys per category
const categories = {
    GPT: ['OPENAI_API_KEY', 'OPENAI_MODEL'],
    NOTION: ['NOTION_TOKEN', 'NOTION_DATABASE_ID', 'NOTION_DATA_SOURCE_ID'],
    YOUTUBE: ['YT_API_KEY', 'YOUTUBE_CHANNEL_ID'],
    GENPROAI: ['GENPROAI_API_KEY'],
    GITHUB: ['GIT_TOKEN'],
};

const ApiKeyModal = ({ isOpen, onClose }) => {
    const initialKeys = {
        OPENAI_API_KEY: '',
        OPENAI_MODEL: '',
        NOTION_TOKEN: '',
        NOTION_DATABASE_ID: '',
        NOTION_DATA_SOURCE_ID: '',
        YT_API_KEY: '',
        YOUTUBE_CHANNEL_ID: '',
        GENPROAI_API_KEY: '',
        GIT_TOKEN: '',
    };

    const [keys, setKeys] = useState(initialKeys);
    const [activeTab, setActiveTab] = useState('GPT');

    const handleChange = (e) => {
        const { name, value } = e.target;
        setKeys((prev) => ({ ...prev, [name]: value }));
    };

    const handleInsert = (field) => {
        console.log(`Inserted ${field}:`, keys[field]);
        alert(`Inserted ${field}`);
    };

    const handleClear = (field) => {
        setKeys((prev) => ({ ...prev, [field]: '' }));
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-11/12 max-w-3xl p-6 overflow-auto max-h-[90vh]">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">API Keys</h2>
                {/* Tabs */}
                <div className="flex space-x-2 mb-4">
                    {Object.keys(categories).map((cat) => (
                        <button
                            key={cat}
                            onClick={() => setActiveTab(cat)}
                            className={`px-3 py-1 rounded ${activeTab === cat ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200'}`}
                        >
                            {cat}
                        </button>
                    ))}
                </div>
                {/* Fields for active tab */}
                <div className="space-y-4">
                    {categories[activeTab].map((field) => (
                        <div key={field} className="flex items-center space-x-2">
                            <label className="w-48 text-gray-700 dark:text-gray-300" htmlFor={field}>{field}</label>
                            <input
                                id={field}
                                name={field}
                                type="text"
                                value={keys[field]}
                                onChange={handleChange}
                                className="flex-1 px-3 py-2 border rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                placeholder="Enter value"
                            />
                            <button
                                onClick={() => handleInsert(field)}
                                className="px-2 py-1 bg-green-600 text-white rounded"
                            >
                                Insert
                            </button>
                            <button
                                onClick={() => handleClear(field)}
                                className="px-2 py-1 bg-red-600 text-white rounded"
                            >
                                Clear
                            </button>
                        </div>
                    ))}
                </div>
                <div className="mt-6 flex justify-end space-x-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ApiKeyModal;
