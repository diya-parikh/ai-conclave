// Ensure teacher role
const user = checkAuth('teacher');

document.addEventListener('DOMContentLoaded', () => {
    if(user) {
        loadDashboard();
        loadRecentEvaluations();
    }
});

// UI helpers
function showAnswerForm() {
    const input = document.getElementById('answerSheetInput');
    if(input.files.length > 0) {
        document.getElementById('upload-answer-form').style.display = 'block';
    }
}

function showKbForm() {
    const input = document.getElementById('kbInput');
    if(input.files.length > 0) {
        document.getElementById('upload-kb-form').style.display = 'block';
    }
}

// Load Dashboard Stats
async function loadDashboard() {
    try {
        const stats = await api.get('/results/dashboard');
        document.getElementById('stat-total').textContent = stats.total_evaluations;
        document.getElementById('stat-students').textContent = stats.total_students;
        document.getElementById('stat-avg').textContent = stats.average_score ? `${stats.average_score.toFixed(1)}%` : 'N/A';
    } catch(e) {
        console.error('Failed to load dashboard stats', e);
    }
}

// Load Recent Evaluations
async function loadRecentEvaluations() {
    try {
        const results = await api.get('/results/');
        const tbody = document.getElementById('eval-table-body');
        
        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted)">No evaluations found</td></tr>';
            return;
        }

        tbody.innerHTML = results.map(row => `
            <tr>
                <td>${new Date(row.evaluated_at || row.uploaded_at || Date.now()).toLocaleDateString()}</td>
                <td>
                    <div style="font-weight:500">${row.student_name || 'Unknown'}</div>
                    <div style="font-size:0.75rem;color:var(--text-muted)">${row.student_email || ''}</div>
                </td>
                <td>${row.subject || '-'}</td>
                <td>${row.percentage !== null ? row.percentage.toFixed(1) + '%' : '-'}</td>
                <td>${row.grade || '-'}</td>
                <td><span class="status-badge status-${row.status}">${row.status}</span></td>
                <td>
                    ${row.status === 'uploaded' ? 
                        `<button class="action-btn" onclick="triggerProcessAndEval('${row.id}')">Start Eval</button>` 
                        : row.status === 'completed' ?
                        `<button class="action-btn action-btn-outline" onclick="window.location.href='report.html?id=${row.id}'">View Report</button>`
                        : `<span style="font-size:0.8rem;color:var(--text-muted)">Processing...</span>`
                    }
                </td>
            </tr>
        `).join('');
    } catch(e) {
        console.error(e);
        document.getElementById('eval-table-body').innerHTML = '<tr><td colspan="7" style="color:var(--error);text-align:center">Error loading data</td></tr>';
    }
}

// Upload Answer Sheet
document.getElementById('upload-answer-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-upload-as');
    btn.disabled = true;
    btn.textContent = 'Uploading...';

    const file = document.getElementById('answerSheetInput').files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('student_name', document.getElementById('as-name').value);
    formData.append('student_email', document.getElementById('as-email').value);
    formData.append('subject', document.getElementById('as-subject').value);

    try {
        const doc = await api.upload('/upload/', formData);
        
        btn.textContent = 'Processing OCR...';
        // Auto trigger pipeline processing
        await api.post('/process/', { document_id: doc.id });
        
        btn.textContent = 'Evaluating (RAG+LLM)...';
        // Auto trigger evaluation
        await api.post('/evaluate/', { document_id: doc.id, max_marks_per_question: 10 });
        
        alert('Evaluation completed successfully!');
        window.location.reload();
    } catch(err) {
        alert('Error: ' + err.message);
        btn.disabled = false;
        btn.textContent = 'Upload & Process';
    }
});

// Manual Trigger for previously uploaded files
async function triggerProcessAndEval(docId) {
    if(!confirm("Start OCR and Evaluation process for this document?")) return;
    try {
        alert("Process started, this may take a few minutes...");
        await api.post('/process/', { document_id: docId });
        await api.post('/evaluate/', { document_id: docId, max_marks_per_question: 10 });
        alert('Evaluation completed!');
        loadDashboard();
        loadRecentEvaluations();
    } catch(err) {
        alert('Pipeline Error: ' + err.message);
    }
}

// Upload Knowledge base
document.getElementById('upload-kb-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-upload-kb');
    btn.disabled = true;
    btn.textContent = 'Ingesting to Vector Database...';

    const file = document.getElementById('kbInput').files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject', document.getElementById('kb-subject').value);
    formData.append('document_type', document.getElementById('kb-type').value);

    try {
        await api.upload('/knowledge/ingest', formData);
        alert('Reference material ingested successfully!');
        document.getElementById('upload-kb-form').reset();
        document.getElementById('upload-kb-form').style.display = 'none';
        btn.disabled = false;
        btn.textContent = 'Ingest to Knowledge Base';
    } catch(err) {
        alert('Ingestion Error: ' + err.message);
        btn.disabled = false;
        btn.textContent = 'Ingest to Knowledge Base';
    }
});
