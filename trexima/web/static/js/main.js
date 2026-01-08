/**
 * TREXIMA Web Application - Main JavaScript
 */

// Progress Overlay Functions
function showProgress(message) {
    const overlay = document.getElementById('progress-overlay');
    const messageEl = document.getElementById('progress-message');
    const fillEl = document.getElementById('progress-fill');

    if (overlay && messageEl && fillEl) {
        overlay.classList.remove('hidden');
        messageEl.textContent = message || 'Processing...';
        fillEl.style.width = '0%';

        // Start progress polling
        startProgressPolling();
    }
}

function hideProgress() {
    const overlay = document.getElementById('progress-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
    stopProgressPolling();
}

let progressInterval = null;

function startProgressPolling() {
    stopProgressPolling();
    progressInterval = setInterval(updateProgressFromServer, 500);
}

function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

function updateProgressFromServer() {
    fetch('/api/progress')
        .then(response => response.json())
        .then(data => {
            const messageEl = document.getElementById('progress-message');
            const fillEl = document.getElementById('progress-fill');

            if (messageEl && data.message) {
                messageEl.textContent = data.message;
            }
            if (fillEl && typeof data.percent === 'number') {
                fillEl.style.width = data.percent + '%';
            }
        })
        .catch(err => console.error('Progress update failed:', err));
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // Add to body
    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// API Helper Functions
async function apiGet(endpoint) {
    try {
        const response = await fetch(endpoint);
        return await response.json();
    } catch (error) {
        console.error(`API GET ${endpoint} failed:`, error);
        throw error;
    }
}

async function apiPost(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    } catch (error) {
        console.error(`API POST ${endpoint} failed:`, error);
        throw error;
    }
}

async function apiPostForm(endpoint, formData) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        return await response.json();
    } catch (error) {
        console.error(`API POST ${endpoint} failed:`, error);
        throw error;
    }
}

// Drag and Drop Support
function setupDragDrop(dropZone, fileInput) {
    if (!dropZone || !fileInput) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('highlight');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('highlight');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;

        // Create a new FileList-like object for the input
        const dataTransfer = new DataTransfer();
        for (let file of files) {
            dataTransfer.items.add(file);
        }
        fileInput.files = dataTransfer.files;

        // Trigger change event
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
    }, false);
}

// Initialize drag-drop for file uploads on page load
document.addEventListener('DOMContentLoaded', function() {
    // Setup drag-drop for any file labels
    document.querySelectorAll('.file-label').forEach(label => {
        const input = label.previousElementSibling;
        if (input && input.type === 'file') {
            setupDragDrop(label, input);
        }
    });
});

// Export functions for global use
window.TREXIMA = {
    showProgress,
    hideProgress,
    formatFileSize,
    showNotification,
    apiGet,
    apiPost,
    apiPostForm
};
