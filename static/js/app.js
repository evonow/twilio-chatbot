// Global state
let uploadedFiles = [];
let statusCheckInterval = null;
let conversationSessionId = 'session_' + Date.now(); // Unique session ID
let conversationHistory = []; // Store conversation history locally
let currentFileFilter = 'all'; // Current file type filter
let allFilesList = []; // Store all files for filtering
let selectedAudiences = []; // Selected audience filters
let fileAudienceMap = {}; // Map of filename -> audience from knowledge base

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadStats();
    loadFiles();
    loadExampleQuestions();
    
    // Setup collapse chevron toggles for all sections
    const collapseSections = [
        'testChatbotCollapse',
        'adminSectionCollapse',
        'uploadFilesCollapse',
        'processingStatusCollapse',
        'uploadedFilesCollapse',
        'knowledgeBaseCollapse',
        'twilioCollapse',
        'gitlabCollapse',
        'adminCollapse'
    ];
    
    collapseSections.forEach(sectionId => {
        const collapse = document.getElementById(sectionId);
        const button = document.querySelector(`[data-bs-target="#${sectionId}"]`);
        if (collapse && button) {
            collapse.addEventListener('show.bs.collapse', function() {
                const chevron = button.querySelector('.bi-chevron-down');
                if (chevron) {
                    chevron.classList.remove('bi-chevron-down');
                    chevron.classList.add('bi-chevron-up');
                }
            });
            collapse.addEventListener('hide.bs.collapse', function() {
                const chevron = button.querySelector('.bi-chevron-up');
                if (chevron) {
                    chevron.classList.remove('bi-chevron-up');
                    chevron.classList.add('bi-chevron-down');
                }
            });
        }
    });
});

function initializeEventListeners() {
    // File upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Buttons
    document.getElementById('processBtn').addEventListener('click', processFiles);
    document.getElementById('clearUploadsBtn').addEventListener('click', clearUploads);
    document.getElementById('queryBtn').addEventListener('click', queryChatbot);
    document.getElementById('refreshFilesBtn').addEventListener('click', loadFiles);
    document.getElementById('clearKbBtn').addEventListener('click', clearKnowledgeBase);
    
    // Process all files button
    const processAllBtn = document.getElementById('processAllBtn');
    if (processAllBtn) {
        processAllBtn.addEventListener('click', processAllFiles);
    }
    
    const clearAllFilesBtn = document.getElementById('clearAllFilesBtn');
    if (clearAllFilesBtn) {
        clearAllFilesBtn.addEventListener('click', clearAllFiles);
    }
    
    // Logout button/form - handle both click and form submission
    const logoutBtn = document.getElementById('logoutBtn');
    const logoutForm = document.getElementById('logoutForm');
    
    if (logoutBtn) {
        // Handle button click
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Logout button clicked');
            logout();
        });
    }
    
    if (logoutForm) {
        // Handle form submission
        logoutForm.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Logout form submitted');
            logout();
            return false;
        });
    }
    
    if (!logoutBtn && !logoutForm) {
        console.warn('Logout button/form not found');
    }
    
    // Admin user management
    const addUserBtn = document.getElementById('addUserBtn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', () => {
            document.getElementById('addUserForm').style.display = 'block';
        });
    }
    
    const cancelAddUserBtn = document.getElementById('cancelAddUserBtn');
    if (cancelAddUserBtn) {
        cancelAddUserBtn.addEventListener('click', () => {
            document.getElementById('addUserForm').style.display = 'none';
            document.getElementById('newUserPin').value = '';
            document.getElementById('newUserName').value = '';
            document.getElementById('newUserRole').value = 'Customer';
        });
    }
    
    const saveUserBtn = document.getElementById('saveUserBtn');
    if (saveUserBtn) {
        saveUserBtn.addEventListener('click', createUser);
    }
    
    const refreshUsersBtn = document.getElementById('refreshUsersBtn');
    if (refreshUsersBtn) {
        refreshUsersBtn.addEventListener('click', loadUsers);
    }
    
    // Load users if admin section exists
    if (document.getElementById('adminCollapse')) {
        loadUsers();
        checkDbStatus();
    }
    
    // Analyze FAQs button
    const analyzeFaqsBtn = document.getElementById('analyzeFaqsBtn');
    if (analyzeFaqsBtn) {
        analyzeFaqsBtn.addEventListener('click', analyzeFAQs);
    }
    
    
    // Google Docs integration
    const ingestGoogleDocBtn = document.getElementById('ingestGoogleDocBtn');
    if (ingestGoogleDocBtn) {
        ingestGoogleDocBtn.addEventListener('click', ingestGoogleDoc);
    }
    
        // GitLab integration
        const ingestGitLabBtn = document.getElementById('ingestGitLabBtn');
        if (ingestGitLabBtn) {
            ingestGitLabBtn.addEventListener('click', ingestGitLab);
        }
        
        // Twilio integration
        const refreshTwilioBtn = document.getElementById('refreshTwilioBtn');
        if (refreshTwilioBtn) {
            refreshTwilioBtn.addEventListener('click', loadTwilioStatus);
        }
        
        // Load Twilio status on page load
        loadTwilioStatus();
    
    // File type filter buttons
    const filterButtons = document.querySelectorAll('[data-filter]');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            // Set current filter
            currentFileFilter = this.getAttribute('data-filter');
            // Apply filter
            applyFileFilter();
        });
    });
    
    // Audience filter checkboxes
    const audienceCheckboxes = document.querySelectorAll('[id^="audienceFilter"]:not(#audienceFilterDropdown)');
    audienceCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectedAudiences();
            applyFileFilter();
        });
    });
    
    // Clear audience filters button
    const clearAudienceFiltersBtn = document.getElementById('clearAudienceFilters');
    if (clearAudienceFiltersBtn) {
        clearAudienceFiltersBtn.addEventListener('click', function() {
            audienceCheckboxes.forEach(cb => cb.checked = false);
            updateSelectedAudiences();
            applyFileFilter();
        });
    }
    
    // Enter key for query - submit on Enter, new line on Shift+Enter
    const queryInput = document.getElementById('queryInput');
    if (queryInput) {
        queryInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault(); // Prevent new line
                e.stopPropagation(); // Stop event propagation
                
                // Get the query value
                const query = queryInput.value.trim();
                if (query) {
                    // Call queryChatbot directly
                    console.log('Enter key pressed, submitting query:', query);
                    queryChatbot();
                }
            }
        });
        console.log('Enter key handler attached to queryInput');
    } else {
        console.warn('queryInput not found when attaching Enter key handler');
    }
    
    // Enter key for query - submit on Enter, new line on Shift+Enter
    const queryInput = document.getElementById('queryInput');
    if (queryInput) {
        queryInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault(); // Prevent new line
                e.stopPropagation(); // Stop event propagation
                
                // Get the query value
                const query = queryInput.value.trim();
                if (query) {
                    // Call queryChatbot directly
                    queryChatbot();
                }
            }
        });
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    handleFiles(files);
}

function handleFiles(files) {
    const formData = new FormData();
    files.forEach(file => {
        if (isValidFile(file)) {
            formData.append('files[]', file);
        }
    });
    
    if (formData.getAll('files[]').length === 0) {
        showToast('No valid files selected', 'warning');
        return;
    }
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            uploadedFiles = uploadedFiles.concat(data.files);
            displayUploadedFiles();
            showToast(data.message, 'success');
        } else {
            showToast(data.error || 'Upload failed', 'danger');
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showToast('Upload failed: ' + error.message, 'danger');
    });
}

function isValidFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    return ['eml', 'mbox', 'txt', 'json', 'csv', 'xml', 'docx', 'pdf'].includes(ext);
}

function displayUploadedFiles() {
    const container = document.getElementById('uploadedFiles');
    
    if (uploadedFiles.length === 0) {
        container.innerHTML = '';
        document.getElementById('processBtn').disabled = true;
        return;
    }
    
    document.getElementById('processBtn').disabled = false;
    
    container.innerHTML = '<h6>Uploaded Files:</h6>' +
        uploadedFiles.map((file, index) => `
            <div class="file-item">
                <div class="file-info">
                    <div class="file-name">${file.original_name}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="removeFile(${index})">
                    <i class="bi bi-x"></i>
                </button>
            </div>
        `).join('');
}

function removeFile(index) {
    uploadedFiles.splice(index, 1);
    displayUploadedFiles();
}

function clearUploads() {
    uploadedFiles = [];
    displayUploadedFiles();
    showToast('Uploads cleared', 'info');
}

function processFiles() {
    if (uploadedFiles.length === 0) {
        showToast('No files to process', 'warning');
        return;
    }
    
    // Get selected audiences from checkboxes
    const selectedAudiences = [];
    const audienceCheckboxes = ['audienceSalesReps', 'audienceCustomers', 'audienceInternal'];
    audienceCheckboxes.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox && checkbox.checked) {
            selectedAudiences.push(checkbox.value);
        }
    });
    const audience = selectedAudiences.length > 0 ? selectedAudiences.join(',') : '';
    
    fetch('/api/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            files: uploadedFiles,
            audience: audience || undefined
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Processing started', 'success');
            document.getElementById('processingCard').style.display = 'block';
            startStatusCheck();
            clearUploads();
        } else {
            showToast(data.error || 'Failed to start processing', 'danger');
        }
    })
    .catch(error => {
        console.error('Process error:', error);
        showToast('Failed to start processing: ' + error.message, 'danger');
    });
}

function processAllFiles() {
    if (!confirm('Process all files in the uploads directory? This may take a while.')) {
        return;
    }
    
    // Get selected audiences from checkboxes (reuse the same checkboxes)
    const selectedAudiences = [];
    const audienceCheckboxes = ['audienceSalesReps', 'audienceCustomers', 'audienceInternal'];
    audienceCheckboxes.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox && checkbox.checked) {
            selectedAudiences.push(checkbox.value);
        }
    });
    const audience = selectedAudiences.length > 0 ? selectedAudiences.join(',') : '';
    
    const btn = document.getElementById('processAllBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Starting...';
    
    fetch('/api/process/all', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            audience: audience || undefined
        })
    })
    .then(response => response.json())
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-play-fill"></i> Process All Files';
        
        if (data.success) {
            showToast(`Processing started for ${data.total_files} file(s)`, 'success');
            document.getElementById('processingCard').style.display = 'block';
            startStatusCheck();
            // Refresh file list after a short delay to show updated status
            setTimeout(() => {
                loadFiles();
            }, 2000);
        } else {
            showToast(data.error || 'Failed to start processing', 'danger');
        }
    })
    .catch(error => {
        console.error('Process all error:', error);
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-play-fill"></i> Process All Files';
        showToast('Failed to start processing: ' + error.message, 'danger');
    });
}

function startStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    // Check status every 500ms for more responsive updates
    statusCheckInterval = setInterval(checkStatus, 500);
    checkStatus(); // Check immediately
}

function checkStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(status => {
            updateProcessingStatus(status);
            
            if (!status.is_processing && status.files_processed > 0) {
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
                loadStats();
                loadFiles();
                showToast(`Processing complete! Added ${status.documents_added} documents.`, 'success');
            }
        })
        .catch(error => {
            console.error('Status check error:', error);
        });
}

function updateProcessingStatus(status) {
    const statusDiv = document.getElementById('processingStatus');
    const progressBar = document.getElementById('progressBar');
    const errorsDiv = document.getElementById('processingErrors');
    
    const progress = status.total_files > 0 
        ? (status.files_processed / status.total_files) * 100 
        : 0;
    
    progressBar.style.width = progress + '%';
    progressBar.textContent = Math.round(progress) + '%';
    
    let statusHTML = `
        <div class="processing-status">
            <p><strong>Files:</strong> ${status.files_processed} / ${status.total_files}</p>
            <p><strong>Documents Added:</strong> ${status.documents_added}</p>
    `;
    
    if (status.current_file) {
        statusHTML += `<p><strong>Current File:</strong> ${status.current_file}</p>`;
    }
    
    statusHTML += '</div>';
    statusDiv.innerHTML = statusHTML;
    
    // Disable/enable process all button based on processing status
    const processAllBtn = document.getElementById('processAllBtn');
    if (processAllBtn) {
        processAllBtn.disabled = status.is_processing;
    }
    
    if (status.errors && status.errors.length > 0) {
        errorsDiv.innerHTML = '<h6 class="text-danger">Errors:</h6>' +
            '<div class="error-list">' +
            status.errors.map(error => `<div class="error-item">${error}</div>`).join('') +
            '</div>';
    } else {
        errorsDiv.innerHTML = '';
    }
}

function queryChatbot() {
    const query = document.getElementById('queryInput').value.trim();
    
    if (!query) {
        showToast('Please enter a query', 'warning');
        return;
    }
    
    const queryBtn = document.getElementById('queryBtn');
    queryBtn.disabled = true;
        queryBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Asking...';
    
    const audience = document.getElementById('queryAudience')?.value || '';
    
    fetch('/api/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            query: query,
            session_id: conversationSessionId,
            audience: audience || undefined
        })
    })
    .then(response => response.json())
    .then(data => {
        queryBtn.disabled = false;
        queryBtn.innerHTML = '<i class="bi bi-send"></i> Ask';
        
        if (data.success) {
            // Add both user query and assistant response to history after successful response
            conversationHistory.push({ 
                role: 'user', 
                content: query,
                timestamp: new Date().toISOString()
            });
            conversationHistory.push({ 
                role: 'assistant', 
                content: data.response,
                timestamp: new Date().toISOString()
            });
            
            displayQueryResult(data.response, data.sources);
            document.getElementById('queryInput').value = '';
        } else {
            showToast(data.error || 'Query failed', 'danger');
        }
    })
    .catch(error => {
        console.error('Query error:', error);
        queryBtn.disabled = false;
        queryBtn.innerHTML = '<i class="bi bi-send"></i> Ask';
        showToast('Query failed: ' + error.message, 'danger');
    });
}

function displayQueryResult(response, sources = []) {
    const resultDiv = document.getElementById('queryResult');
    
    // Build conversation history display in iMessage style
    let conversationHTML = '';
    conversationHistory.forEach((msg, index) => {
        const isLastMessage = index === conversationHistory.length - 1;
        const isLastResponse = isLastMessage && msg.role === 'assistant';
        
        // Format timestamp
        const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '';
        
        if (msg.role === 'user') {
            conversationHTML += `
                <div class="message-bubble user">
                    <div class="message-content">
                        <div class="message-text">${escapeHtml(msg.content)}</div>
                        ${timestamp ? `<div class="message-timestamp">${timestamp}</div>` : ''}
                    </div>
                </div>
            `;
        } else {
            conversationHTML += `
                <div class="message-bubble assistant">
                    <div class="message-content">
                        <div class="message-text">${escapeHtml(msg.content)}</div>
                        ${sources && sources.length > 0 && isLastResponse ? `
                            <div class="message-sources">
                                <i class="bi bi-info-circle"></i> Based on ${sources.length} source${sources.length > 1 ? 's' : ''}:
                                ${sources.slice(0, 2).map(s => 
                                    `${s.subject !== 'N/A' ? escapeHtml(s.subject) : escapeHtml(s.file)}`
                                ).join(', ')}
                                ${sources.length > 2 ? ` and ${sources.length - 2} more` : ''}
                            </div>
                        ` : ''}
                        ${timestamp ? `<div class="message-timestamp">${timestamp}</div>` : ''}
                    </div>
                </div>
            `;
        }
    });
    
    resultDiv.innerHTML = `
        <div class="conversation-history" id="conversationHistory">
            ${conversationHTML || '<div class="text-muted text-center py-4">Start a conversation by asking a question!</div>'}
        </div>
        ${conversationHistory.length > 0 ? `
            <div class="clear-conversation-btn">
                <button class="btn btn-sm btn-outline-secondary" onclick="clearConversation()">
                    <i class="bi bi-x-circle"></i> Clear Conversation
                </button>
            </div>
        ` : ''}
    `;
    
    // Auto-scroll to bottom
    const historyDiv = document.getElementById('conversationHistory');
    if (historyDiv) {
        historyDiv.scrollTop = historyDiv.scrollHeight;
    }
}

function clearConversation() {
    if (confirm('Clear conversation history? This will start a new conversation.')) {
        conversationHistory = [];
        conversationSessionId = 'session_' + Date.now();
        
        fetch('/api/conversation/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: conversationSessionId })
        })
        .then(response => response.json())
        .then(data => {
            displayQueryResult(); // Refresh display with empty state
            showToast('Conversation cleared', 'success');
        })
        .catch(error => {
            console.error('Clear conversation error:', error);
            // Still clear locally even if API call fails
            displayQueryResult(); // Refresh display with empty state
        });
    }
}

function loadFiles() {
    fetch('/api/files')
        .then(response => response.json())
        .then(data => {
            allFilesList = data.files || [];
            // Build audience map
            fileAudienceMap = {};
            allFilesList.forEach(file => {
                if (file.audience) {
                    fileAudienceMap[file.filename] = file.audience;
                }
            });
            updateFileTypeCounts();
            applyFileFilter();
        })
        .catch(error => {
            console.error('Load files error:', error);
        });
}

function updateFileTypeCounts() {
    const counts = {
        all: allFilesList.length,
        eml: 0,
        docx: 0,
        pdf: 0,
        txt: 0,
        other: 0
    };
    
    allFilesList.forEach(file => {
        const filename = file.filename.toLowerCase();
        const extension = filename.split('.').pop();
        
        if (extension === 'eml') {
            counts.eml++;
        } else if (extension === 'docx') {
            counts.docx++;
        } else if (extension === 'pdf') {
            counts.pdf++;
        } else if (extension === 'txt') {
            counts.txt++;
        } else if (!['mbox', 'json', 'csv', 'xml'].includes(extension)) {
            counts.other++;
        }
    });
    
    // Update count badges
    document.getElementById('countAll').textContent = counts.all;
    document.getElementById('countEml').textContent = counts.eml;
    document.getElementById('countDocx').textContent = counts.docx;
    document.getElementById('countPdf').textContent = counts.pdf;
    document.getElementById('countTxt').textContent = counts.txt;
    document.getElementById('countOther').textContent = counts.other;
    
    // Show/hide buttons based on count
    document.getElementById('filterEml').style.display = counts.eml > 0 ? '' : 'none';
    document.getElementById('filterDocx').style.display = counts.docx > 0 ? '' : 'none';
    document.getElementById('filterPdf').style.display = counts.pdf > 0 ? '' : 'none';
    document.getElementById('filterTxt').style.display = counts.txt > 0 ? '' : 'none';
    document.getElementById('filterOther').style.display = counts.other > 0 ? '' : 'none';
}

function updateSelectedAudiences() {
    selectedAudiences = [];
    const audienceCheckboxes = document.querySelectorAll('[id^="audienceFilter"]:not(#audienceFilterDropdown)');
    audienceCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            selectedAudiences.push(checkbox.value);
        }
    });
    
    // Update dropdown button text
    const dropdownBtn = document.getElementById('audienceFilterDropdown');
    if (selectedAudiences.length === 0) {
        dropdownBtn.innerHTML = '<i class="bi bi-funnel"></i> Filter by Audience';
    } else {
        const labels = {
            'sales_reps': 'Sales Reps',
            'customers': 'Customers',
            'internal': 'Internal'
        };
        const selectedLabels = selectedAudiences.map(a => labels[a] || a).join(', ');
        dropdownBtn.innerHTML = `<i class="bi bi-funnel-fill"></i> ${selectedLabels}`;
    }
}

function applyFileFilter() {
    let filteredFiles = allFilesList;
    
    // Apply file type filter
    if (currentFileFilter !== 'all') {
        filteredFiles = filteredFiles.filter(file => {
            const filename = file.filename.toLowerCase();
            const extension = filename.split('.').pop();
            
            if (currentFileFilter === 'other') {
                // Show files that are not eml, docx, pdf, or txt
                return !['eml', 'docx', 'pdf', 'txt', 'mbox', 'json', 'csv', 'xml'].includes(extension);
            } else {
                return extension === currentFileFilter;
            }
        });
    }
    
    // Apply audience filter if any are selected
    if (selectedAudiences.length > 0) {
        filteredFiles = filteredFiles.filter(file => {
            // Check if file has audience metadata
            const fileAudience = fileAudienceMap[file.filename] || file.audience;
            // If file has no audience label, include it (means it's for all audiences)
            if (!fileAudience) {
                return true;
            }
            // Include if file's audience matches any selected audience
            return selectedAudiences.includes(fileAudience);
        });
    }
    
    displayFilesList(filteredFiles);
}

function displayFilesList(files) {
    const container = document.getElementById('filesList');
    
    if (files.length === 0) {
        container.innerHTML = '<p class="text-muted">No files uploaded yet</p>';
        return;
    }
    
    const processedCount = files.filter(f => f.processed).length;
    const totalCount = files.length;
    
    container.innerHTML = `
        <div class="mb-2">
            <span class="badge bg-success">${processedCount} Processed</span>
            <span class="badge bg-secondary">${totalCount - processedCount} Not Processed</span>
            <span class="badge bg-info">${totalCount} Total</span>
        </div>
        <table class="table table-sm files-table">
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Filename</th>
                    <th>Size</th>
                    <th>Modified</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${files.map(file => `
                    <tr>
                        <td>
                            ${file.processed 
                                ? '<span class="badge bg-success"><i class="bi bi-check-circle"></i> In KB</span>' 
                                : '<span class="badge bg-warning"><i class="bi bi-exclamation-circle"></i> Not Processed</span>'}
                        </td>
                        <td>${escapeHtml(file.filename)}</td>
                        <td>${formatFileSize(file.size)}</td>
                        <td>${new Date(file.modified).toLocaleString()}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-info me-1" onclick="verifyFile('${file.filename}')" title="Verify in knowledge base">
                                <i class="bi bi-search"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteFile('${file.filename}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function verifyFile(filename) {
    // Extract the base filename (remove timestamp prefix if present)
    let searchFilename = filename;
    if (filename.includes('_') && filename.match(/^\d{8}_\d{6}_/)) {
        // Remove timestamp prefix: YYYYMMDD_HHMMSS_
        searchFilename = filename.replace(/^\d{8}_\d{6}_/, '');
    }
    
    // Search for this file in the knowledge base
    fetch('/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: 'metadata',
            filename: searchFilename,
            max_results: 50
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.count > 0) {
            // Show results in a modal or alert
            const resultText = `Found ${data.count} document(s) from this file in the knowledge base.\n\n` +
                `Documents:\n${data.results.map((r, i) => 
                    `${i+1}. ${r.metadata?.subject || 'No subject'} (Chunk ${r.metadata?.chunk_index || 0})`
                ).join('\n')}`;
            
            alert(resultText);
            
            // Also display in search results area
            displaySearchResults(data.results, data.count);
            // Scroll to search results
            document.getElementById('searchResults').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert(`File "${filename}" was NOT found in the knowledge base.\n\n` +
                  `This means it hasn't been processed yet. Click "Process Files" to add it to the knowledge base.`);
        }
    })
    .catch(error => {
        console.error('Verify error:', error);
        showToast('Failed to verify file: ' + error.message, 'danger');
    });
}

function deleteFile(filename) {
    if (!confirm('Are you sure you want to delete this file?')) {
        return;
    }
    
    fetch(`/api/files/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('File deleted', 'success');
            loadFiles();
        } else {
            showToast(data.error || 'Failed to delete file', 'danger');
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        showToast('Failed to delete file: ' + error.message, 'danger');
    });
}

function clearAllFiles() {
    // Get current file count for confirmation message
    const fileCount = allFilesList ? allFilesList.length : 0;
    
    if (fileCount === 0) {
        showToast('No files to delete', 'info');
        return;
    }
    
    if (!confirm(`Are you sure you want to delete all ${fileCount} uploaded file(s)?\n\nThis action cannot be undone!`)) {
        return;
    }
    
    const btn = document.getElementById('clearAllFilesBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Clearing...';
    
    fetch('/api/files/clear-all', {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Successfully deleted ${data.deleted_count} file(s)`, 'success');
            // Clear the files list
            allFilesList = [];
            fileAudienceMap = {};
            loadFiles();
            updateFileTypeCounts();
        } else {
            showToast(data.error || 'Failed to clear files', 'danger');
        }
    })
    .catch(error => {
        console.error('Clear all files error:', error);
        showToast('Failed to clear files: ' + error.message, 'danger');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = originalText;
    });
}

function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update navbar stats
                const totalDocs = data.total_documents || 0;
                document.getElementById('kb-stats-total').textContent = totalDocs.toLocaleString();
                
                // Show document types breakdown in header
                const docTypes = data.document_types || {};
                const typeCounts = Object.entries(docTypes)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3) // Show top 3 types
                    .map(([type, count]) => `.${type}: ${count}`)
                    .join(', ');
                
                const typesElement = document.getElementById('kb-stats-types');
                if (typeCounts) {
                    typesElement.textContent = typeCounts;
                } else {
                    typesElement.textContent = '';
                }
                
                // Update detailed stats in Knowledge Base section
                updateDetailedStats(data);
            } else {
                document.getElementById('kb-stats-total').textContent = '-';
                document.getElementById('kb-stats-types').textContent = '';
            }
        })
        .catch(error => {
            console.error('Stats error:', error);
            document.getElementById('kb-stats-total').textContent = '-';
            document.getElementById('kb-stats-types').textContent = '';
        });
}

function updateDetailedStats(data) {
    const statsContainer = document.getElementById('kbInfo');
    if (!statsContainer) return;
    
    // Document types breakdown
    const docTypes = data.document_types || {};
    const docTypesHtml = Object.keys(docTypes).length > 0 
        ? Object.entries(docTypes)
            .sort((a, b) => b[1] - a[1])
            .map(([type, count]) => `<span class="badge bg-secondary me-1">.${type}: ${count}</span>`)
            .join('')
        : '<span class="text-muted">No documents analyzed</span>';
    
    // Audience breakdown
    const audience = data.audience_breakdown || {};
    const audienceHtml = Object.keys(audience).length > 0
        ? Object.entries(audience)
            .map(([aud, count]) => `<span class="badge bg-info me-1">${aud || 'unlabeled'}: ${count}</span>`)
            .join('')
        : '<span class="text-muted">No audience labels</span>';
    
    // Customer service stats
    const csEmails = data.customer_service?.emails || 0;
    const csTexts = data.customer_service?.text_messages || 0;
    const csTotal = data.customer_service?.total || 0;
    
    // Release notes stats
    const releaseFeatures = data.release_notes?.features_count || 0;
    const releaseDocs = data.release_notes?.documents || 0;
    
    // Other stats
    const gitlabDocs = data.gitlab_documents || 0;
    const uniqueFiles = data.unique_files || 0;
    const uniqueSenders = data.unique_senders || 0;
    
    statsContainer.innerHTML = `
        <div class="row">
            <div class="col-md-6 mb-3">
                <h6><i class="bi bi-file-earmark-text"></i> Document Types</h6>
                <div>${docTypesHtml}</div>
            </div>
            <div class="col-md-6 mb-3">
                <h6><i class="bi bi-people"></i> Audience Breakdown</h6>
                <div>${audienceHtml}</div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-4 mb-3">
                <h6><i class="bi bi-envelope"></i> Customer Service</h6>
                <ul class="list-unstyled mb-0">
                    <li>Emails: <strong>${csEmails}</strong></li>
                    <li>Text Messages: <strong>${csTexts}</strong></li>
                    <li>Total: <strong>${csTotal}</strong></li>
                </ul>
            </div>
            <div class="col-md-4 mb-3">
                <h6><i class="bi bi-star"></i> Release Notes</h6>
                <ul class="list-unstyled mb-0">
                    <li>Documents: <strong>${releaseDocs}</strong></li>
                    <li>Features Count: <strong>${releaseFeatures}</strong></li>
                </ul>
            </div>
            <div class="col-md-4 mb-3">
                <h6><i class="bi bi-info-circle"></i> Additional Stats</h6>
                <ul class="list-unstyled mb-0">
                    <li>Unique Files: <strong>${uniqueFiles}</strong></li>
                    <li>Unique Senders: <strong>${uniqueSenders}</strong></li>
                    <li>GitLab Docs: <strong>${gitlabDocs}</strong></li>
                    <li class="text-muted small">Sampled: ${data.sampled_documents || 0} docs</li>
                </ul>
            </div>
        </div>
        <div class="mt-2">
            <small class="text-muted">
                <i class="bi bi-database"></i> Index: <strong>${data.index_name || 'N/A'}</strong> | 
                Total Documents: <strong>${data.total_documents || 0}</strong>
            </small>
        </div>
    `;
}

function clearKnowledgeBase() {
    if (!confirm('⚠️ WARNING: This will delete ALL documents from the knowledge base!\n\nThis cannot be undone. Are you sure?')) {
        return;
    }
    
    fetch('/api/clear', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Knowledge base cleared', 'success');
            loadStats();
        } else {
            showToast(data.error || 'Failed to clear knowledge base', 'danger');
        }
    })
    .catch(error => {
        console.error('Clear error:', error);
        showToast('Failed to clear knowledge base: ' + error.message, 'danger');
    });
}

function analyzeFAQs() {
    const btn = document.getElementById('analyzeFaqsBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Analyzing...';
    
    fetch('/api/analyze/faqs?max_questions=20&sample_size=200')
        .then(response => response.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-graph-up"></i> Analyze FAQs';
            
            if (data.success) {
                displayFAQs(data.faqs, data.count);
            } else {
                showToast(data.error || 'Failed to analyze FAQs', 'danger');
                document.getElementById('faqsResults').innerHTML = '';
            }
        })
        .catch(error => {
            console.error('Analyze FAQs error:', error);
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-graph-up"></i> Analyze FAQs';
            showToast('Failed to analyze FAQs: ' + error.message, 'danger');
        });
}

function displayFAQs(faqs, count) {
    const container = document.getElementById('faqsResults');
    
    if (!faqs || faqs.length === 0) {
        container.innerHTML = '<div class="alert alert-warning">No frequently asked questions found. Make sure you have processed some emails first.</div>';
        return;
    }
    
    let html = `<div class="alert alert-success"><strong>Found ${count} Frequently Asked Questions</strong></div>`;
    html += '<div class="list-group">';
    
    faqs.forEach((faq, index) => {
        const question = faq.question || 'Unknown question';
        const frequency = faq.frequency || 0;
        const variations = faq.variations || [];
        
        html += `
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">
                            <span class="badge bg-primary me-2">#${index + 1}</span>
                            ${escapeHtml(question)}
                        </h6>
                        <p class="mb-1 text-muted">
                            <strong>Frequency:</strong> ${frequency} time${frequency !== 1 ? 's' : ''}
                        </p>
                        ${variations.length > 0 ? `
                            <p class="mb-1"><strong>Example variations:</strong></p>
                            <ul class="small text-muted mb-0">
                                ${variations.slice(0, 3).map(v => `<li>${escapeHtml(v)}</li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = toast.querySelector('.toast-body');
    const toastHeader = toast.querySelector('.toast-header strong');
    
    toastBody.textContent = message;
    toastHeader.textContent = type.charAt(0).toUpperCase() + type.slice(1);
    
    toast.classList.remove('bg-primary', 'bg-success', 'bg-danger', 'bg-warning', 'bg-info');
    toast.classList.add(`bg-${type}`);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function ingestGoogleDoc() {
    const documentId = document.getElementById('googleDocId').value.trim();
    const credentialsFile = document.getElementById('googleCredentialsFile').value.trim() || 'credentials.json';
    
    if (!documentId) {
        showToast('Please enter a Google Doc URL or Document ID', 'warning');
        return;
    }
    
    const btn = document.getElementById('ingestGoogleDocBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Ingesting...';
    
    const resultDiv = document.getElementById('googleDocsResult');
    resultDiv.innerHTML = '<div class="alert alert-info">Connecting to Google Docs...</div>';
    
    fetch('/api/googledocs/ingest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            document_id: documentId,
            credentials_file: credentialsFile,
            audience: document.getElementById('googleDocAudience')?.value || undefined
        })
    })
    .then(response => response.json())
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Ingest Google Doc';
        
        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <strong>Success!</strong> ${data.message}<br>
                    Added ${data.documents_added} document chunk(s) to knowledge base.
                </div>
            `;
            showToast(`Successfully ingested: ${data.title}`, 'success');
            loadStats();
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> ${data.error || 'Failed to ingest Google Doc'}
                    ${data.traceback ? `<pre class="mt-2 small">${escapeHtml(data.traceback)}</pre>` : ''}
                </div>
            `;
            showToast(data.error || 'Failed to ingest Google Doc', 'danger');
        }
    })
    .catch(error => {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Ingest Google Doc';
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> ${error.message}
            </div>
        `;
        showToast('Failed to ingest Google Doc: ' + error.message, 'danger');
    });
}

function loadTwilioStatus() {
    fetch('/api/twilio/status')
        .then(response => response.json())
        .then(data => {
            const statusDiv = document.getElementById('twilioStatus');
            const webhookUrl = document.getElementById('webhookUrl');
            const conversationsDiv = document.getElementById('twilioConversations');
            
            // Try to get ngrok URL from ngrok API, fallback to current origin
            fetch('http://localhost:4040/api/tunnels')
                .then(response => response.json())
                .then(ngrokData => {
                    const tunnels = ngrokData.tunnels || [];
                    const httpsTunnel = tunnels.find(t => t.public_url && t.public_url.startsWith('https://'));
                    if (httpsTunnel) {
                        webhookUrl.textContent = `${httpsTunnel.public_url}/sms`;
                        webhookUrl.style.color = '#28a745';
                    } else {
                        // Fallback to current origin
                        const currentUrl = window.location.origin;
                        webhookUrl.textContent = `${currentUrl}/sms`;
                        webhookUrl.style.color = '#dc3545';
                        // Add warning
                        if (statusDiv) {
                            const existingWarning = statusDiv.querySelector('.ngrok-warning');
                            if (!existingWarning) {
                                const warning = document.createElement('div');
                                warning.className = 'alert alert-warning mt-2 ngrok-warning';
                                warning.innerHTML = '<strong>⚠️ Note:</strong> This is a localhost URL. For Twilio, you need a public HTTPS URL. Use ngrok: <code>ngrok http 5001</code> and use the HTTPS URL it provides.';
                                statusDiv.appendChild(warning);
                            }
                        }
                    }
                })
                .catch(() => {
                    // ngrok not running or not accessible
                    const currentUrl = window.location.origin;
                    webhookUrl.textContent = `${currentUrl}/sms`;
                    webhookUrl.style.color = '#dc3545';
                    // Add warning
                    if (statusDiv) {
                        const existingWarning = statusDiv.querySelector('.ngrok-warning');
                        if (!existingWarning) {
                            const warning = document.createElement('div');
                            warning.className = 'alert alert-warning mt-2 ngrok-warning';
                            warning.innerHTML = '<strong>⚠️ Note:</strong> This is a localhost URL. For Twilio, you need a public HTTPS URL. Use ngrok: <code>ngrok http 5001</code> and use the HTTPS URL it provides.';
                            statusDiv.appendChild(warning);
                        }
                    }
                });
            
            // Update status (this will be called after webhook URL is set)
            updateTwilioStatus(data, statusDiv);
            
            // Load conversations
            loadTwilioConversations();
        })
        .catch(error => {
            console.error('Error loading Twilio status:', error);
            document.getElementById('twilioStatus').innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-x-circle"></i> Error loading Twilio status
                </div>
            `;
        });
}

function updateTwilioStatus(data, statusDiv) {
    if (data.configured) {
        statusDiv.innerHTML = `
            <div class="alert alert-success">
                <i class="bi bi-check-circle"></i> <strong>Twilio Configured</strong>
                <br>Phone Number: ${data.phone_number || 'Not set'}
                <br>Active Conversations: ${data.active_conversations}
                <br>Total Messages: ${data.total_messages}
            </div>
        `;
    } else {
        statusDiv.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle"></i> <strong>Twilio Not Configured</strong>
                <br>Please set the following environment variables:
                <ul class="mb-0 mt-2">
                    <li><code>TWILIO_ACCOUNT_SID</code></li>
                    <li><code>TWILIO_AUTH_TOKEN</code></li>
                    <li><code>TWILIO_PHONE_NUMBER</code></li>
                </ul>
            </div>
        `;
    }
}

function loadTwilioConversations() {
    fetch('/api/twilio/conversations')
        .then(response => response.json())
        .then(data => {
            const conversationsDiv = document.getElementById('twilioConversations');
            
            if (data.conversations && data.conversations.length > 0) {
                conversationsDiv.innerHTML = `
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Phone Number</th>
                                <th>Messages</th>
                                <th>Last Message</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.conversations.map(conv => `
                                <tr>
                                    <td>${escapeHtml(conv.phone_number)}</td>
                                    <td>${conv.message_count}</td>
                                    <td>${conv.last_message ? new Date(conv.last_message).toLocaleString() : 'N/A'}</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-info" onclick="viewTwilioConversation('${encodeURIComponent(conv.phone_number)}')">
                                            <i class="bi bi-eye"></i> View
                                        </button>
                                        <button class="btn btn-sm btn-outline-danger" onclick="clearTwilioConversation('${encodeURIComponent(conv.phone_number)}')">
                                            <i class="bi bi-trash"></i> Clear
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                conversationsDiv.innerHTML = '<p class="text-muted">No active conversations</p>';
            }
        })
        .catch(error => {
            console.error('Error loading conversations:', error);
        });
}

function viewTwilioConversation(phoneNumber) {
    fetch(`/api/twilio/conversations/${phoneNumber}`)
        .then(response => response.json())
        .then(data => {
            if (data.messages) {
                const messagesHtml = data.messages.map(msg => `
                    <div class="mb-2 p-2 ${msg.role === 'user' ? 'bg-light' : 'bg-info bg-opacity-10'}">
                        <strong>${msg.role === 'user' ? 'User' : 'Assistant'}:</strong> ${escapeHtml(msg.content)}
                        <br><small class="text-muted">${new Date(msg.timestamp).toLocaleString()}</small>
                    </div>
                `).join('');
                
                // Show in modal or alert
                alert(`Conversation with ${data.phone_number}:\n\n${messagesHtml.replace(/<[^>]*>/g, '\n')}`);
            }
        })
        .catch(error => {
            console.error('Error loading conversation:', error);
            showToast('Error loading conversation', 'error');
        });
}

function clearTwilioConversation(phoneNumber) {
    if (!confirm('Are you sure you want to clear this conversation history?')) {
        return;
    }
    
    fetch(`/api/twilio/conversations/${phoneNumber}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            showToast('Conversation cleared', 'success');
            loadTwilioConversations();
        })
        .catch(error => {
            console.error('Error clearing conversation:', error);
            showToast('Error clearing conversation', 'error');
        });
}

function ingestGitLab() {
    const gitlabUrl = document.getElementById('gitlabUrl').value.trim() || 'https://gitlab.com';
    const projectId = document.getElementById('gitlabProjectId').value.trim();
    const accessToken = document.getElementById('gitlabToken').value.trim();
    const ref = document.getElementById('gitlabRef').value.trim() || 'main';
    
    const includeCommits = document.getElementById('includeCommits').checked;
    const includeReadmes = document.getElementById('includeReadmes').checked;
    const includeReleaseNotes = document.getElementById('includeReleaseNotes').checked;
    const maxCommits = parseInt(document.getElementById('maxCommits').value) || 100;
    
    if (!projectId) {
        showToast('Please enter a GitLab Project ID', 'warning');
        return;
    }
    
    if (!includeCommits && !includeReadmes && !includeReleaseNotes) {
        showToast('Please select at least one content type to include', 'warning');
        return;
    }
    
    const btn = document.getElementById('ingestGitLabBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Ingesting...';
    
    const resultDiv = document.getElementById('gitlabResult');
    resultDiv.innerHTML = '<div class="alert alert-info">Connecting to GitLab...</div>';
    
    const audience = document.getElementById('gitlabAudience')?.value || '';
    
    const requestBody = {
        project_id: projectId,
        gitlab_url: gitlabUrl,
        ref: ref,
        include_commits: includeCommits,
        include_readmes: includeReadmes,
        include_release_notes: includeReleaseNotes,
        max_commits: maxCommits
    };
    
    if (accessToken) {
        requestBody.access_token = accessToken;
    }
    
    if (audience) {
        requestBody.audience = audience;
    }
    
    fetch('/api/gitlab/ingest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Ingest GitLab Repository';
        
        if (data.success) {
            const sourcesInfo = data.sources ? `
                <ul class="mb-0">
                    <li>Commits: ${data.sources.commits || 0}</li>
                    <li>READMEs: ${data.sources.readmes || 0}</li>
                    <li>Release Notes: ${data.sources.release_notes || 0}</li>
                </ul>
            ` : '';
            
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <strong>Success!</strong> ${data.message}<br>
                    Added ${data.documents_added} document chunk(s) to knowledge base.
                    ${sourcesInfo}
                </div>
            `;
            showToast(`Successfully ingested: ${data.project_name}`, 'success');
            loadStats();
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> ${data.error || 'Failed to ingest GitLab repository'}
                    ${data.traceback ? `<pre class="mt-2 small">${escapeHtml(data.traceback)}</pre>` : ''}
                </div>
            `;
            showToast(data.error || 'Failed to ingest GitLab repository', 'danger');
        }
    })
    .catch(error => {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Ingest GitLab Repository';
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> ${error.message}
            </div>
        `;
        showToast('Failed to ingest GitLab repository: ' + error.message, 'danger');
    });
}

function logout() {
    console.log('Logout function called');
    
    if (!confirm('Are you sure you want to logout?')) {
        return false;
    }
    
    // Use form submission (most reliable method)
    const logoutForm = document.getElementById('logoutForm');
    if (logoutForm) {
        console.log('Submitting logout form');
        // Let the form submit naturally - backend will redirect
        return true; // Allow form submission
    }
    
    // Fallback: direct redirect if form not found
    console.log('Form not found, redirecting directly');
    window.location.href = '/logout';
    return false;
}

function checkDbStatus() {
    fetch('/api/db-status')
        .then(response => response.json())
        .then(data => {
            const alertDiv = document.getElementById('dbStatusAlert');
            const statusText = document.getElementById('dbStatusText');
            
            if (!alertDiv || !statusText) return;
            
            if (data.using_postgres && data.connection_test === 'success') {
                alertDiv.className = 'alert alert-success mb-3';
                statusText.innerHTML = `✅ PostgreSQL connected | ${data.user_count} user(s) stored | Users will persist across deployments`;
            } else if (data.warning) {
                alertDiv.className = 'alert alert-warning mb-3';
                statusText.innerHTML = `⚠️ ${data.warning} | Users may be lost on next deployment!`;
            } else {
                alertDiv.className = 'alert alert-danger mb-3';
                statusText.innerHTML = `❌ Database connection failed | Users may be lost on next deployment!`;
            }
        })
        .catch(error => {
            console.error('DB status error:', error);
            const alertDiv = document.getElementById('dbStatusAlert');
            const statusText = document.getElementById('dbStatusText');
            if (alertDiv && statusText) {
                alertDiv.className = 'alert alert-danger mb-3';
                statusText.innerHTML = `❌ Error checking database status`;
            }
        });
}

function loadUsers() {
    fetch('/api/users')
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                showToast('Admin access required', 'danger');
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.users) {
                displayUsers(data.users);
            }
        })
        .catch(error => {
            console.error('Load users error:', error);
            showToast('Failed to load users', 'danger');
        });
}

function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No users found</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => {
        const createdDate = user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A';
        return `
            <tr>
                <td><code>${escapeHtml(user.pin)}</code></td>
                <td>${escapeHtml(user.name || '')}</td>
                <td><span class="badge bg-${getRoleBadgeColor(user.role)}">${escapeHtml(user.role)}</span></td>
                <td>${createdDate}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteUser('${user.pin}')">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function getRoleBadgeColor(role) {
    switch(role) {
        case 'Admin': return 'danger';
        case 'Internal': return 'dark';
        case 'Sales Rep': return 'info';
        case 'Customer': return 'success';
        default: return 'secondary';
    }
}

function createUser() {
    const pin = document.getElementById('newUserPin').value.trim();
    const name = document.getElementById('newUserName').value.trim();
    const role = document.getElementById('newUserRole').value;
    
    if (!pin || pin.length !== 4 || !/^\d{4}$/.test(pin)) {
        showToast('PIN must be exactly 4 digits', 'danger');
        return;
    }
    
    if (!name) {
        showToast('Name is required', 'danger');
        return;
    }
    
    fetch('/api/users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pin, name, role })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`User ${name} created successfully with PIN ${pin}`, 'success');
            document.getElementById('addUserForm').style.display = 'none';
            document.getElementById('newUserPin').value = '';
            document.getElementById('newUserName').value = '';
            document.getElementById('newUserRole').value = 'Customer';
            loadUsers();
        } else {
            showToast(data.error || 'Failed to create user', 'danger');
        }
    })
    .catch(error => {
        console.error('Create user error:', error);
        showToast('Failed to create user', 'danger');
    });
}

function deleteUser(pin) {
    if (!confirm(`Are you sure you want to delete user with PIN ${pin}?`)) {
        return;
    }
    
    fetch(`/api/users/${pin}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('User deleted successfully', 'success');
            loadUsers();
        } else {
            showToast(data.error || 'Failed to delete user', 'danger');
        }
    })
    .catch(error => {
        console.error('Delete user error:', error);
        showToast('Failed to delete user', 'danger');
    });
}

function loadExampleQuestions() {
    fetch('/api/examples')
        .then(response => response.json())
        .then(data => {
            console.log('Examples data received:', data);
            if (data.success && data.examples && data.examples.length > 0) {
                const queryInput = document.getElementById('queryInput');
                if (queryInput) {
                    // Ensure we have at least 3 examples
                    let allExamples = data.examples;
                    if (allExamples.length < 3) {
                        const fallbacks = [
                            "How do I create a fundraiser?",
                            "How do I track donations?",
                            "How do I share my fundraiser?"
                        ];
                        allExamples = allExamples.concat(fallbacks).slice(0, Math.max(3, allExamples.length));
                    }
                    
                    console.log('All examples:', allExamples);
                    
                    // Rotate through 3 examples at a time
                    let currentIndex = 0;
                    const examplesPerRotation = 3;
                    
                    const updatePlaceholder = () => {
                        // Only update if input is empty
                        if (!queryInput.value || queryInput.value.trim() === '') {
                            // Get next 3 examples (wrapping around)
                            const examplesToShow = [];
                            for (let i = 0; i < examplesPerRotation; i++) {
                                const idx = (currentIndex + i) % allExamples.length;
                                examplesToShow.push(allExamples[idx]);
                            }
                            
                            console.log('Showing examples:', examplesToShow);
                            
                            // Show all 3 examples in placeholder separated by " | "
                            const placeholderText = examplesToShow.map(ex => `e.g., ${ex}`).join(' | ');
                            queryInput.placeholder = placeholderText;
                            queryInput.setAttribute('rows', '2'); // Keep rows at 2
                            
                            // Store current examples for display
                            queryInput.setAttribute('data-examples', JSON.stringify(examplesToShow));
                            
                            // Move to next set of 3 examples
                            currentIndex = (currentIndex + examplesPerRotation) % allExamples.length;
                        }
                    };
                    
                    // Update immediately
                    updatePlaceholder();
                    
                    // Rotate every 7 seconds
                    setInterval(updatePlaceholder, 7000);
                } else {
                    console.warn('queryInput element not found');
                }
            } else {
                console.warn('No examples received or invalid data:', data);
            }
        })
        .catch(error => {
            console.error('Error loading examples:', error);
            // Keep default placeholder
        });
}

