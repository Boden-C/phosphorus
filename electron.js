// Disable security warnings in development environment only
process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = 'true';

import { app, BrowserWindow, session, WebContents, Certificate } from 'electron';
import path from 'path';

/**
 * Creates and configures the main application window
 * @returns {BrowserWindow} The created browser window instance
 */
function createWindow() {
    // Create the browser window with secure defaults
    const mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true,
            webSecurity: true,
            enableRemoteModule: false,
            preload: path.join(__dirname, 'preload.js'),
        },
    });

    // In production, use loadURL for deployed app
    if (app.isPackaged) {
        mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'))
            .catch((err) => console.error('Failed to load app:', err));
    } else {
        // In development, you might want to load from a dev server
        mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'))
            .catch((err) => console.error('Failed to load app:', err));
    }

    // Open DevTools in development mode
    if (!app.isPackaged) {
        mainWindow.webContents.openDevTools();
    }

    return mainWindow;
}

/**
 * Configure content security policy for the application
 */
function setupSecurityPolicies() {
    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
        callback({
            responseHeaders: {
                ...details.responseHeaders,
                'Content-Security-Policy': [
                    "default-src 'self'; script-src 'self'; connect-src 'self';"
                ]
            }
        });
    });
}

// App initialization
app.whenReady()
    .then(() => {
        setupSecurityPolicies();
        createWindow();

        // Only use this in development, remove in production
        if (!app.isPackaged) {
            app.commandLine.appendSwitch('ignore-certificate-errors');
        }
    })
    .catch((err) => {
        console.error('Failed to initialize app:', err);
        app.quit();
    });

// Handle window activation
app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// WARNING: Only in development environments
if (!app.isPackaged) {
    app.on('certificate-error', (
        event,
        webContents,
        url,
        error,
        certificate,
        callback
    ) => {
        console.warn('Certificate error:', error, 'URL:', url);
        event.preventDefault();
        callback(true); // Accept the certificate anyway
    });
}