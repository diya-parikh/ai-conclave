// Ensure student role
const user = checkAuth('student');

document.addEventListener('DOMContentLoaded', () => {
    if(user) {
        loadMyResults();
    }
});

async function loadMyResults() {
    try {
        const results = await api.get('/results/my-results');
        const tbody = document.getElementById('student-eval-table');
        
        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted)">No evaluations available yet.</td></tr>';
            return;
        }

        tbody.innerHTML = results.map(row => `
            <tr>
                <td>${new Date(row.evaluated_at || row.uploaded_at).toLocaleDateString()}</td>
                <td style="font-weight:600">${row.subject || '-'}</td>
                <td>${row.exam_name || 'Assignment'}</td>
                <td>
                    ${row.percentage !== null ? 
                        `<span style="color:var(--primary);font-weight:700;">${parseFloat(row.percentage).toFixed(1)}%</span> (${parseFloat(row.total_marks || 0).toFixed(1)}/${parseFloat(row.max_marks || 0).toFixed(1)})` 
                        : '-'}
                </td>
                <td>
                    ${row.grade ? `<span class="status-badge status-completed">${row.grade}</span>` : '-'}
                </td>
                <td><span class="status-badge status-${row.status}">${row.status}</span></td>
                <td>
                    ${row.status === 'completed' ?
                        `<button class="action-btn" onclick="window.location.href='report.html?id=${row.id}'">View Full Report</button>`
                        : `<span style="font-size:0.8rem;color:var(--text-muted)">Processing...</span>`
                    }
                </td>
            </tr>
        `).join('');
    } catch(e) {
        console.error(e);
        document.getElementById('student-eval-table').innerHTML = '<tr><td colspan="7" style="color:var(--error);text-align:center">Error loading your results.</td></tr>';
    }
}
