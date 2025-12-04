import { spawn } from 'child_process';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

// Configuration
const BACKEND_PORT = 3001;
const FRONTEND_PORT = 5173; // Default Vite port
const FRONTEND_URL = `http://localhost:${FRONTEND_PORT}`;

console.log('🚀 Starting AutoFX Services...');

// Helper to spawn processes
const spawnProcess = (command, args, name, color) => {
    const proc = spawn(command, args, {
        shell: true,
        stdio: 'pipe',
        env: { ...process.env, FORCE_COLOR: '1' }
    });

    proc.stdout.on('data', (data) => {
        const lines = data.toString().split('\n');
        lines.forEach(line => {
            if (line.trim()) console.log(`${color}[${name}] ${line}\x1b[0m`);
        });
    });

    proc.stderr.on('data', (data) => {
        const lines = data.toString().split('\n');
        lines.forEach(line => {
            if (line.trim()) console.error(`${color}[${name}] ERROR: ${line}\x1b[0m`);
        });
    });

    return proc;
};

// Start Backend
const backend = spawnProcess('npm', ['run', 'server'], 'Backend', '\x1b[36m'); // Cyan

// Start Frontend
const frontend = spawnProcess('npm', ['run', 'dev'], 'Frontend', '\x1b[32m'); // Green

// Open Browser after a short delay
setTimeout(() => {
    console.log(`🌐 Opening ${FRONTEND_URL}...`);
    const startCommand = process.platform === 'win32' ? 'start' :
        process.platform === 'darwin' ? 'open' : 'xdg-open';
    spawn(startCommand, [FRONTEND_URL], { shell: true });
}, 3000);

// Handle Exit
const cleanup = () => {
    console.log('\n🛑 Stopping services...');
    backend.kill();
    frontend.kill();
    process.exit();
};

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', cleanup);
