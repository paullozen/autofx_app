import express from 'express';
import cors from 'cors';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import { WebSocketServer } from 'ws';
import http from 'http';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

// Create HTTP server
const server = http.createServer(app);

// Create WebSocket server
const wss = new WebSocketServer({ server });

// Broadcast function to send data to all connected clients
const broadcast = (data) => {
    wss.clients.forEach((client) => {
        if (client.readyState === 1) { // OPEN
            client.send(JSON.stringify(data));
        }
    });
};

wss.on('connection', (ws) => {
    console.log('Client connected to WebSocket');
    ws.send(JSON.stringify({ type: 'info', message: 'Connected to backend terminal' }));
});

// Store active processes
const activeProcesses = new Map();

// Endpoint to list existing profiles
app.get('/list-profiles', (req, res) => {
    const profilesDir = path.join(__dirname, 'backend', 'chrome_profiles');

    try {
        if (!fs.existsSync(profilesDir)) {
            return res.json({ success: true, profiles: [] });
        }

        const items = fs.readdirSync(profilesDir);
        const profiles = items.filter(item => {
            const itemPath = path.join(profilesDir, item);
            return fs.statSync(itemPath).isDirectory();
        });

        res.json({ success: true, profiles });
    } catch (error) {
        res.json({ success: false, error: error.message, profiles: [] });
    }
});

// Endpoint to delete a profile
app.delete('/delete-profile/:profileName', (req, res) => {
    const { profileName } = req.params;
    const profilePath = path.join(__dirname, 'backend', 'chrome_profiles', profileName);

    try {
        if (!fs.existsSync(profilePath)) {
            return res.json({ success: false, error: 'Profile not found' });
        }

        // Recursively delete the profile directory
        fs.rmSync(profilePath, { recursive: true, force: true });

        res.json({ success: true, message: `Profile "${profileName}" deleted successfully` });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// Endpoint to open folder in file explorer
app.post('/open-folder', (req, res) => {
    const { folderPath } = req.body;

    try {
        const fullPath = path.isAbsolute(folderPath)
            ? folderPath
            : path.join(__dirname, 'backend', folderPath);

        if (!fs.existsSync(fullPath)) {
            return res.json({ success: false, error: 'Folder not found' });
        }

        // Open folder based on OS
        const { exec } = require('child_process');
        const command = process.platform === 'win32'
            ? `explorer "${fullPath}"`
            : process.platform === 'darwin'
                ? `open "${fullPath}"`
                : `xdg-open "${fullPath}"`;

        exec(command, (error) => {
            if (error) {
                return res.json({ success: false, error: error.message });
            }
            res.json({ success: true, message: 'Folder opened' });
        });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// Endpoint to save manual suggestions
app.post('/api/save-manual-suggestions', (req, res) => {
    console.log('Received save-manual-suggestions request:', req.body);
    const { baseName, suggestions } = req.body;

    if (!baseName || !suggestions) {
        console.error('Missing baseName or suggestions');
        return res.status(400).json({ success: false, error: 'Missing baseName or suggestions' });
    }

    try {
        // Create suggestions directory if it doesn't exist
        const suggestionsDir = path.join(__dirname, 'output', 'img_suggestions', baseName);
        console.log('Creating directory:', suggestionsDir);

        if (!fs.existsSync(suggestionsDir)) {
            fs.mkdirSync(suggestionsDir, { recursive: true });
        }

        // Save to a temporary file that will be used by suggestion_generator.py
        const tempFilePath = path.join(suggestionsDir, `${baseName}__manual.txt`);
        console.log('Saving to file:', tempFilePath);
        fs.writeFileSync(tempFilePath, suggestions, 'utf-8');

        console.log('Suggestions saved successfully');
        res.json({
            success: true,
            message: 'Suggestions saved successfully',
            filePath: tempFilePath
        });
    } catch (error) {
        console.error('Error saving suggestions:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});


app.post('/execute', (req, res) => {
    const { script, input, processId } = req.body;

    const scriptPath = path.join(__dirname, 'backend', `${script}.py`);
    const pythonPath = path.join(__dirname, 'venv', 'bin', 'python3');

    // Build arguments for the script
    let args;
    if (script === 'profile_generator' && input) {
        args = ['-u', scriptPath, input];
    } else if (input) {
        const inputArgs = input.split('\n').filter(arg => arg !== '');
        args = ['-u', scriptPath, ...inputArgs];
    } else {
        args = ['-u', scriptPath];
    }

    // Spawn python process with -u for unbuffered output
    const pythonProcess = spawn(pythonPath, args);

    // Store process if processId is provided
    if (processId) {
        activeProcesses.set(processId, pythonProcess);
    }

    // Respond immediately to the frontend
    res.json({ success: true, message: 'Script started', processId });

    pythonProcess.stdout.on('data', (data) => {
        const text = data.toString();
        console.log('Python output:', text);
        broadcast({ type: 'stdout', output: text, processId });
    });

    pythonProcess.stderr.on('data', (data) => {
        const errText = data.toString();
        console.error('Python error:', errText);
        broadcast({ type: 'stderr', output: errText, processId });
    });

    pythonProcess.on('close', (code) => {
        if (processId) {
            activeProcesses.delete(processId);
        }
        broadcast({ type: 'close', code, processId });
    });
});

app.post('/stop', (req, res) => {
    const { processId } = req.body;

    const process = activeProcesses.get(processId);
    if (!process) {
        return res.json({
            success: false,
            error: 'Process not found'
        });
    }

    try {
        process.kill('SIGTERM'); // Send termination signal
        activeProcesses.delete(processId);
        broadcast({ type: 'info', message: 'Process stopped by user', processId });
        res.json({ success: true });
    } catch (error) {
        res.json({
            success: false,
            error: error.message
        });
    }
});

app.post('/send-input', (req, res) => {
    const { processId, input } = req.body;

    const process = activeProcesses.get(processId);
    if (!process) {
        return res.json({
            success: false,
            error: 'Process not found'
        });
    }

    try {
        process.stdin.write(`${input}\n`);
        res.json({ success: true });
    } catch (error) {
        res.json({
            success: false,
            error: error.message
        });
    }
});

// Endpoint to save script to txt_inbox
app.post('/save-script', (req, res) => {
    const { content, filename } = req.body;
    const inboxDir = path.join(__dirname, 'txt_inbox');

    try {
        if (!fs.existsSync(inboxDir)) {
            fs.mkdirSync(inboxDir, { recursive: true });
        }

        let finalFilename;
        if (filename && filename.trim()) {
            finalFilename = filename.trim();
            if (!finalFilename.endsWith('.txt')) {
                finalFilename += '.txt';
            }
        } else {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            finalFilename = `script_${timestamp}.txt`;
        }

        const filePath = path.join(inboxDir, finalFilename);

        fs.writeFileSync(filePath, content, 'utf8');
        res.json({ success: true, file: finalFilename });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

server.listen(PORT, () => {
    console.log(`Backend server running on http://localhost:${PORT}`);
});
