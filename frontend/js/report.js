// Check auth but allow both roles
const user = checkAuth();

document.addEventListener('DOMContentLoaded', () => {
    if(user) {
        const urlParams = new URLSearchParams(window.location.search);
        const evalId = urlParams.get('id');
        if(evalId) {
            loadReport(evalId);
        } else {
            document.getElementById('report-container').innerHTML = 
                '<h2 style="text-align:center; color:var(--error);">No Evaluation ID provided</h2>';
        }
    }
});

async function loadReport(id) {
    try {
        const report = await api.get(`/results/${id}`);
        const container = document.getElementById('report-container');

        let html = `
            <div class="report-header">
                <div>
                    <h2 class="card-title" style="border:none; margin:0;">${report.subject || 'Evaluation Report'}</h2>
                    <p style="color:var(--text-muted)">Student: ${report.student_name} (${report.student_email})</p>
                </div>
                <div style="text-align:right">
                    <div style="font-size:0.8rem;color:var(--text-muted)">Evaluated on</div>
                    <div>${new Date(report.evaluated_at).toLocaleString()}</div>
                </div>
            </div>

            <div class="total-score-card">
                <span style="font-weight:600; letter-spacing:2px; text-transform:uppercase;">Final Grade: ${report.grade}</span>
                <h2>${report.percentage.toFixed(1)}%</h2>
                <span>${report.total_marks.toFixed(1)} / ${report.max_marks.toFixed(1)} Total Marks</span>
            </div>
            
            <h3 style="margin-bottom: 1.5rem">Question Breakdown <span style="font-weight:400; font-size:1rem; color:var(--text-muted)">(${report.questions.length} detected)</span></h3>
        `;

        if (report.questions && report.questions.length > 0) {
            report.questions.forEach((q, idx) => {
                
                const hasContradictions = q.contradictions && q.contradictions.length > 0;
                let cHTML = '';
                if(hasContradictions) {
                    cHTML = `
                    <div class="contradiction-alert">
                        <strong style="color:var(--error)">⚠️ Conflict/Contradiction Detected:</strong><br>
                        <ul style="margin-top:0.5rem; padding-left:1.5rem; font-size:0.9rem">
                            ${q.contradictions.map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    </div>`;
                }

                html += `
                <div class="question-card" style="animation-delay: ${idx * 0.1}s">
                    <div class="q-header">
                        <div class="q-title">${q.question_id || `Question ${idx+1}`}</div>
                        <div class="q-marks">${q.marks_awarded || 0} / ${q.max_marks}</div>
                    </div>
                    
                    <span class="feedback-label">Extracted Student Answer:</span>
                    <div class="answer-box">${q.extracted_answer || 'No readable answer found.'}</div>

                    <span class="feedback-label">AI Rationale & Feedback:</span>
                    <div class="feedback-box">
                        ${q.feedback || 'No feedback generated.'}
                        ${cHTML}
                    </div>
                </div>
                `;
            });
        } else {
            html += `<p style="text-align:center; color:var(--text-muted)">No questions could be extracted and mapped.</p>`;
        }

        container.innerHTML = html;
        
    } catch(err) {
        document.getElementById('report-container').innerHTML = 
            `<h2 style="text-align:center; color:var(--error);">Failed to load report: ${err.message}</h2>`;
    }
}
