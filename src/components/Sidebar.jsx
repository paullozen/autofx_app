import React from 'react';
import { User, Radio, Eraser, FileText, MessageSquare, Image, Palette, Film, Moon, Sun, LogIn, AudioWaveform, Download, Key, Folder } from 'lucide-react';

const Sidebar = ({ selectedStage, onSelectStage, theme, toggleTheme }) => {

  const folderMapping = {
    'channel_info': 'output',
    'get_scripts': 'txt_inbox',
    'suggestion_generator': 'output/img_suggestions',
    'image_generator': 'output/imgs_output',
    'audio_generator': 'output/audio',
    'audio_downloader': 'output/audio',
    'srt_generator': 'output/srt_outputs',
    'make_and_render': 'output/render_output',
    'clean_bases': 'txt_inbox/txt_processed',
    'profile_generator': 'backend/chrome_profiles',
  };

  const handleOpenFolder = async (e, stageId) => {
    e.stopPropagation();
    const folderPath = folderMapping[stageId];
    if (!folderPath) return;

    try {
      await fetch('http://localhost:3001/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folderPath })
      });
    } catch (error) {
      console.error('Error opening folder:', error);
    }
  };

  const [tooltip, setTooltip] = React.useState(null);

  const handleFolderHover = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltip({
      top: rect.top + rect.height / 2,
      left: rect.right + 8,
      label: 'Open folder location'
    });
  };

  const handleFolderLeave = () => {
    setTooltip(null);
  };

  const configStages = [
    { id: 'profile_generator', label: 'Create Profile', icon: User },
    { id: 'api_key', label: 'API Key', icon: Key },
  ];

  const pipelineStages = [
    // Group 1: Script & SRT
    { id: 'get_scripts', label: 'Script', icon: FileText },
    { id: 'srt_generator', label: 'SRT Generator', icon: MessageSquare },

    // Group 2: Audio
    { id: 'audio_generator', label: 'Audio Generator', icon: AudioWaveform },
    { id: 'audio_downloader', label: 'Audio Download', icon: Download },

    // Group 3: Images
    { id: 'suggestion_generator', label: 'Image Suggestions', icon: Image },
    { id: 'image_generator', label: 'Image Generator', icon: Palette },
    { id: 'make_and_render', label: 'Image Render', icon: Film },
  ];

  const utilityStages = [
    { id: 'channel_info', label: 'Channel Info', icon: Radio },
    { id: 'clean_bases', label: 'Clean Base', icon: Eraser },
  ];

  const renderStageItem = (stage) => {
    const Icon = stage.icon;
    const isSelected = selectedStage === stage.id;
    const showDividerAfter = ['srt_generator', 'audio_downloader'].includes(stage.id);
    const hasFolder = !!folderMapping[stage.id];

    return (
      <React.Fragment key={stage.id}>
        <div className={`group flex items-center w-full rounded-md transition-colors duration-150 ${isSelected
          ? 'bg-gray-100 dark:bg-gray-800'
          : 'hover:bg-gray-50 dark:hover:bg-gray-800'}`}>

          <button
            onClick={() => onSelectStage(stage.id)}
            className={`flex-1 flex items-center space-x-3 px-4 py-2 text-sm font-medium text-left ${isSelected
              ? 'text-gray-900 dark:text-white'
              : 'text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white'}`}
          >
            <Icon className="w-5 h-5 flex-shrink-0" />
            <span className="truncate">{stage.label}</span>
          </button>

          {hasFolder && (
            <button
              onClick={(e) => handleOpenFolder(e, stage.id)}
              onMouseEnter={(e) => handleFolderHover(e)}
              onMouseLeave={handleFolderLeave}
              className="p-2 mr-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 rounded-md transition-colors relative"
            >
              <Folder className="w-4 h-4" />
            </button>
          )}
        </div>
        {showDividerAfter && (
          <hr className="my-2 border-gray-200 dark:border-gray-700" />
        )}
      </React.Fragment>
    );
  };

  return (
    <>
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300 relative z-20">
        <div className="p-6 border-b border-gray-100 dark:border-gray-800">
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">YouTube Pipeline</h1>
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <div className="px-4 mb-6">
            <button
              onClick={toggleTheme}
              className="w-full flex items-center justify-between px-4 py-2 mb-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <button
              onClick={() => onSelectStage('login')}
              className={`w-full flex items-center justify-between px-4 py-2 mb-4 text-sm font-medium rounded-md transition-colors duration-150 ${selectedStage === 'login'
                ? 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100'
                : 'text-gray-600 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'}`}
            >
              <span>Login</span>
              <LogIn className="w-4 h-4" />
            </button>

            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Configurations</h2>
            <div className="space-y-1">{configStages.map(renderStageItem)}</div>
          </div>

          <div className="px-4 mb-6">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Pipeline Stages</h2>
            <div className="space-y-1">{pipelineStages.map(renderStageItem)}</div>
          </div>

          <div className="px-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Utilities</h2>
            <div className="space-y-1">{utilityStages.map(renderStageItem)}</div>
          </div>
        </div>
      </div>

      {/* Fixed Tooltip Portal */}
      {tooltip && (
        <div
          className="fixed z-[9999] px-2 py-1 bg-gray-800 text-white text-xs rounded shadow-lg pointer-events-none whitespace-nowrap"
          style={{
            top: tooltip.top,
            left: tooltip.left,
            transform: 'translateY(-50%)'
          }}
        >
          {tooltip.label}
        </div>
      )}
    </>
  );
};

export default Sidebar;
