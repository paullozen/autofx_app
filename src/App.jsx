import React, { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import Layout from './components/Layout';

function App() {
  const [selectedStage, setSelectedStage] = useState(null);
  const [logs, setLogs] = useState([]);
  const [theme, setTheme] = useState('dark');
  const [profiles, setProfiles] = useState([]);
  const [currentProcessId, setCurrentProcessId] = useState(null);
  const [currentScript, setCurrentScript] = useState(null);
  const [outputFolder, setOutputFolder] = useState(null);

  const [progress, setProgress] = useState({});

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    // Load existing profiles on mount
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const response = await fetch('/list-profiles');
      const data = await response.json();
      if (data.success) {
        setProfiles(data.profiles);
      }
    } catch (error) {
      console.error('Error loading profiles:', error);
    }
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const handleSelectStage = (stageId) => {
    setSelectedStage(prevStage => prevStage === stageId ? null : stageId);
  };

  const addLog = (message) => {
    setLogs((prevLogs) => [...prevLogs, `${message}`]);
  };

  const handleClearLogs = () => {
    setLogs([]);
  };

  useWebSocket({
    onLog: addLog,
    onProgress: (progData) => setProgress(prev => ({ ...prev, [progData.profile]: progData })),
    onProcessClose: (code) => {
      setCurrentProcessId(null);
      setCurrentScript(null);
      setProgress({});
      if (currentScript === 'profile_generator') {
        loadProfiles();
      }
    },
    onOutputFolder: setOutputFolder,
    currentScript
  });

  const executeScript = async (scriptName, input) => {
    try {
      // Clear previous logs and set current script
      setLogs([]);
      setCurrentScript(scriptName);
      setOutputFolder(null);

      const processId = `${scriptName}_${Date.now()}`;
      setCurrentProcessId(processId);
      addLog(`Executing ${scriptName}.py...`);

      // Just trigger the execution, logs will come via WebSocket
      await fetch('/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          script: scriptName,
          input: input,
          processId: processId
        })
      });

    } catch (error) {
      addLog(`Error executing script: ${error.message}`);
      setCurrentProcessId(null);
      setCurrentScript(null);
    }
  };

  const stopExecution = async () => {
    if (!currentProcessId) return;

    try {
      await fetch('/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ processId: currentProcessId })
      });
      // The WebSocket will handle the 'close' event or we can manually log
      addLog('Process Stoped.');
    } catch (error) {
      addLog(`Error stopping process: ${error.message}`);
    }
  };

  const sendInput = async (input) => {
    if (!currentProcessId) {
      addLog(`> ${input}`);
      return;
    }

    try {
      const response = await fetch('/send-input', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          processId: currentProcessId,
          input: input
        })
      });

      const data = await response.json();

      if (data.success) {
        addLog(`> ${input}`);
      } else {
        addLog(`Error sending input: ${data.error}`);
      }
    } catch (error) {
      addLog(`Error: ${error.message}`);
    }
  };

  const openFolder = async (folderPath) => {
    try {
      const response = await fetch('/open-folder', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ folderPath })
      });

      const data = await response.json();

      if (data.success) {
        addLog(`Folder opened: ${folderPath}`);
      } else {
        addLog(`Error opening folder: ${data.error}`);
      }
    } catch (error) {
      addLog(`Error: ${error.message}`);
    }
  };

  const deleteProfile = async (profileName) => {
    if (window.confirm(`Are you sure you want to delete profile "${profileName}"?`)) {
      try {
        const response = await fetch(`/delete-profile/${encodeURIComponent(profileName)}`, {
          method: 'DELETE',
        });

        const data = await response.json();

        if (data.success) {
          setProfiles(prev => prev.filter(p => p !== profileName));
          addLog(`Profile "${profileName}" deleted successfully`);
        } else {
          addLog(`Error deleting profile: ${data.error}`);
        }
      } catch (error) {
        addLog(`Error deleting profile: ${error.message}`);
      }
    }
  };

  return (
    <Layout
      selectedStage={selectedStage}
      onSelectStage={handleSelectStage}
      logs={logs}
      onClearLogs={handleClearLogs}
      theme={theme}
      toggleTheme={toggleTheme}
      onExecuteScript={executeScript}
      profiles={profiles}
      onSendInput={sendInput}
      onDeleteProfile={deleteProfile}
      currentScript={currentScript}
      outputFolder={outputFolder}
      onOpenFolder={openFolder}
      onStop={stopExecution}
      isProcessing={!!currentProcessId}
      progress={progress}
    />
  );
}

export default App;
