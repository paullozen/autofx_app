import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';

const PIDS_FILE = path.join(process.cwd(), '.pids.json');

const killProcess = (pid) => {
    if (!pid) return;
    try {
        if (process.platform === 'win32') {
            exec(`taskkill /pid ${pid} /T /F`, (err) => {
                // ignore errors if process already dead
            });
        } else {
            process.kill(pid, 'SIGTERM');
            // Optional: check and force kill if needed, but SIGTERM is usually enough for child processes
        }
        console.log(`Killed process ${pid}`);
    } catch (e) {
        // ignore
    }
};

if (fs.existsSync(PIDS_FILE)) {
    try {
        const pids = JSON.parse(fs.readFileSync(PIDS_FILE, 'utf-8'));
        console.log('Stopping AutoFX services...');

        // Kill main process first? Or children?
        // If we kill main, it might trigger cleanup.
        // Let's try killing main first.
        if (pids.main) killProcess(pids.main);
        if (pids.backend) killProcess(pids.backend);
        if (pids.frontend) killProcess(pids.frontend);

        // Clean up file
        try {
            fs.unlinkSync(PIDS_FILE);
        } catch (e) { }

        console.log('Services stopped.');
    } catch (e) {
        console.error('Error reading .pids.json:', e);
    }
} else {
    console.log('No running services found (.pids.json missing).');

    // Fallback cleanup just in case
    if (process.platform !== 'win32') {
        exec('pkill -f "node server.js"', () => { });
        exec('pkill -f "vite"', () => { });
    }
}
