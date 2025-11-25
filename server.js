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

// Helper to parse .env file
const parseEnv = () => {
    const envPath = path.join(__dirname, 'backend', '.env');
    if (!fs.existsSync(envPath)) {
        fs.writeFileSync(envPath, '', 'utf8');
        return {};
    }
    const content = fs.readFileSync(envPath, 'utf8');
    const lines = content.split('\n');
    const env = {};
    lines.forEach(line => {
        const match = line.match(/^([^=]+)=(.*)$/);
        if (match) {
            const key = match[1].trim();
            const value = match[2].trim();
            env[key] = value;
        }
    });
    return env;
};

// Helper to save .env file
const saveEnv = (env) => {
    const envPath = path.join(__dirname, 'backend', '.env');
    const content = Object.entries(env)
        .map(([key, value]) => `${key}=${value}`)
        .join('\n');
    fs.writeFileSync(envPath, content, 'utf8');
};

// Endpoint to get API keys (masked)
app.get('/api/env', (req, res) => {
    try {
        const env = parseEnv();
        const maskedEnv = {};
        Object.keys(env).forEach(key => {
            const val = env[key];
            if (val && val.length > 8) {
                maskedEnv[key] = `${val.substring(0, 4)}...${val.substring(val.length - 4)}`;
            } else if (val) {
                maskedEnv[key] = '********';
            } else {
                maskedEnv[key] = '';
            }
        });
        res.json({ success: true, keys: maskedEnv });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// Endpoint to update an API key
app.post('/api/env', (req, res) => {
    const { key, value } = req.body;
    if (!key) return res.json({ success: false, error: 'Key is required' });

    try {
        const env = parseEnv();
        env[key] = value;
        saveEnv(env);
        res.json({ success: true, message: `Key ${key} updated` });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// Endpoint to delete an API key
app.delete('/api/env/:key', (req, res) => {
    const { key } = req.params;
    try {
        const env = parseEnv();
        if (env[key]) {
            delete env[key];
            saveEnv(env);
        }
        res.json({ success: true, message: `Key ${key} deleted` });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// Endpoint to get prompt file content
app.get('/api/prompts/:filename', (req, res) => {
    const { filename } = req.params;
    const filePath = path.join(__dirname, 'prompts', filename);

    try {
        if (!fs.existsSync(filePath)) {
            // If file doesn't exist, return empty string or create it
            return res.json({ success: true, content: '' });
        }
        const content = fs.readFileSync(filePath, 'utf8');
        res.json({ success: true, content });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// Endpoint to save prompt file content
app.post('/api/prompts/:filename', (req, res) => {
    const { filename } = req.params;
    const { content } = req.body;
    const filePath = path.join(__dirname, 'prompts', filename);

    try {
        // Ensure prompts directory exists
        const promptsDir = path.dirname(filePath);
        if (!fs.existsSync(promptsDir)) {
            fs.mkdirSync(promptsDir, { recursive: true });
        }

        fs.writeFileSync(filePath, content, 'utf8');
        res.json({ success: true, message: 'File saved successfully' });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

server.listen(PORT, () => {
    console.log(`Backend server running on http://localhost:${PORT}`);
});
