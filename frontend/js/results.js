/**
 * Results Page Logic
 *
 * Handles results display for both teacher and student views:
 * - Teacher: Table of all student results with detail modal
 * - Student: Personal results list with detailed feedback view
 */

// ---- Teacher Results ----
async function loadTeacherResults() {
    const tbody = $('#results-body');
    const emptyState = $('#results-empty');
    if (!tbody) return;

    try {
        const results = await api.getResults();

        if (!results || results.length === 0) {
            tbody.innerHTML = '';
            if (emptyState) emptyState.style.display = 'flex';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';

        tbody.innerHTML = results.map(ev => `
            <tr>
                <td style="font-weight: 500; color: var(--text-primary);">${ev.student_name || '—'}</td>
                <td>${ev.subject || '—'}</td>
                <td style="font-weight: 600;">${ev.total_marks ?? '—'} / ${ev.max_marks ?? '—'}</td>
                <td>
                    <div class="flex items-center gap-2">
                        <div class="progress-bar-container" style="width: 80px;">
                            <div class="progress-bar-fill" style="width: ${ev.percentage || 0}%;"></div>
                        </div>
                        <span style="font-weight: 500; font-size: var(--font-size-sm);">${ev.percentage ? Math.round(ev.percentage) : 0}%</span>
                    </div>
                </td>
                <td>
                    <span class="grade-badge ${getGradeClass(ev.grade)}" style="width: 36px; height: 36px; font-size: 0.8rem;">
                        ${ev.grade || '—'}
                    </span>
                </td>
                <td>${getStatusBadge(ev.status)}</td>
                <td style="font-size: var(--font-size-xs); color: var(--text-tertiary);">${formatDate(ev.evaluated_at)}</td>
                <td>
                    <button class="btn btn-ghost btn-sm" onclick="viewEvaluationDetail('${ev.id}')">
                        View →
                    </button>
                </td>
            </tr>
        `).join('');

    } catch (error) {
        showToast('Failed to load results', 'error');
        console.error(error);
    }
}

/**
 * View detailed evaluation in modal (teacher view).
 */
async function viewEvaluationDetail(evaluationId) {
    const modal = $('#eval-modal');
    const modalContent = $('#modal-content');
    if (!modal || !modalContent) return;

    modal.classList.add('active');
    modalContent.innerHTML = '<div class="flex justify-center" style="padding: var(--space-8);"><div class="spinner spinner-lg"></div></div>';

    try {
        const detail = await api.getEvaluationDetail(evaluationId);
        renderEvaluationDetail(modalContent, detail);
    } catch (error) {
        modalContent.innerHTML = `<p style="color: var(--accent-danger);">Failed to load details: ${error.message}</p>`;
    }
}

function renderEvaluationDetail(container, detail) {
    const questionsHtml = (detail.questions || []).map(q => `
        <div class="feedback-card">
            <div class="question-header">
                <span class="question-id">${q.question_id}</span>
                <span class="question-score" style="color: ${(q.marks_awarded / q.max_marks) >= 0.6 ? 'var(--accent-success)' : 'var(--accent-danger)'};">
                    ${q.marks_awarded ?? 0} / ${q.max_marks ?? 10}
                </span>
            </div>
            ${q.extracted_answer ? `<div class="answer-text"><strong>Answer:</strong> ${q.extracted_answer}</div>` : ''}
            ${q.feedback ? `<div class="feedback-text"><strong>Feedback:</strong> ${q.feedback}</div>` : ''}
            ${q.contradictions && q.contradictions.length > 0 ? `
                <div class="contradiction-list">
                    <h5>⚠️ Contradictions</h5>
                    <ul>${q.contradictions.map(c => `<li>${c}</li>`).join('')}</ul>
                </div>
            ` : ''}
        </div>
    `).join('');

    container.innerHTML = `
        <div class="flex justify-between items-center flex-wrap gap-4" style="margin-bottom: var(--space-6);">
            <div>
                <h4>${detail.student_name || 'Student'}</h4>
                <p style="font-size: var(--font-size-sm); color: var(--text-tertiary);">${detail.subject || '—'} · ${formatDate(detail.evaluated_at)}</p>
            </div>
            <div class="flex items-center gap-4">
                <div style="text-align: right;">
                    <div style="font-size: var(--font-size-2xl); font-weight: 800;">${detail.percentage ? Math.round(detail.percentage) : 0}%</div>
                    <div style="font-size: var(--font-size-xs); color: var(--text-tertiary);">${detail.total_marks} / ${detail.max_marks}</div>
                </div>
                <span class="grade-badge ${getGradeClass(detail.grade)}">${detail.grade || '—'}</span>
            </div>
        </div>
        <div style="max-height: 400px; overflow-y: auto;">
            ${questionsHtml || '<p style="color: var(--text-tertiary);">No question details available.</p>'}
        </div>
    `;
}

// ---- Student Results ----
async function loadStudentResults() {
    const container = $('#student-results-list');
    const emptyState = $('#student-empty-state');
    if (!container) return;

    try {
        const results = await api.getMyResults();

        if (!results || results.length === 0) {
            if (emptyState) emptyState.style.display = 'flex';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';

        container.innerHTML = results.map(ev => `
            <div class="card" style="margin-bottom: var(--space-4); cursor: pointer;" onclick="viewStudentResult('${ev.id}')">
                <div class="flex justify-between items-center">
                    <div>
                        <h4 style="margin-bottom: var(--space-1);">${ev.subject || 'Unknown Subject'}</h4>
                        <p style="font-size: var(--font-size-sm);">${formatDate(ev.evaluated_at)}</p>
                    </div>
                    <div class="flex items-center gap-4">
                        <div style="text-align: right;">
                            <div style="font-size: var(--font-size-xl); font-weight: 700;">${ev.percentage ? Math.round(ev.percentage) : 0}%</div>
                            <div style="font-size: var(--font-size-xs); color: var(--text-tertiary);">${ev.total_marks} / ${ev.max_marks}</div>
                        </div>
                        <span class="grade-badge ${getGradeClass(ev.grade)}">${ev.grade || '—'}</span>
                    </div>
                </div>
                <div style="margin-top: var(--space-3);">
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: ${ev.percentage || 0}%;"></div>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        showToast('Failed to load results', 'error');
        console.error(error);
    }
}

/**
 * View detailed result for a student (student view).
 */
async function viewStudentResult(evaluationId) {
    const listSection = $('#student-results-list');
    const detailSection = $('#result-detail');
    if (!listSection || !detailSection) return;

    listSection.style.display = 'none';
    detailSection.style.display = 'block';

    try {
        const detail = await api.getEvaluationDetail(evaluationId);

        // Update summary
        const detailSubject = $('#detail-subject');
        const detailDate = $('#detail-date');
        const detailPercentage = $('#detail-percentage');
        const detailGrade = $('#detail-grade');
        const detailGradeBadge = $('#detail-grade-badge');
        const detailTotalMarks = $('#detail-total-marks');
        const detailMaxMarks = $('#detail-max-marks');
        const detailQuestionsCount = $('#detail-questions-count');

        if (detailSubject) detailSubject.textContent = detail.subject || 'Subject';
        if (detailDate) detailDate.textContent = formatDateTime(detail.evaluated_at);
        if (detailPercentage) detailPercentage.textContent = `${Math.round(detail.percentage || 0)}%`;
        if (detailGrade) detailGrade.textContent = detail.grade || '—';
        if (detailGradeBadge) detailGradeBadge.className = `grade-badge ${getGradeClass(detail.grade)}`;
        if (detailTotalMarks) detailTotalMarks.textContent = detail.total_marks ?? 0;
        if (detailMaxMarks) detailMaxMarks.textContent = detail.max_marks ?? 0;
        if (detailQuestionsCount) detailQuestionsCount.textContent = (detail.questions || []).length;

        // Render question feedback
        const feedbackContainer = $('#questions-feedback');
        if (feedbackContainer) {
            feedbackContainer.innerHTML = (detail.questions || []).map(q => `
                <div class="feedback-card">
                    <div class="question-header">
                        <span class="question-id">${q.question_id}</span>
                        <span class="question-score" style="color: ${(q.marks_awarded / q.max_marks) >= 0.6 ? 'var(--accent-success)' : 'var(--accent-danger)'};">
                            ${q.marks_awarded ?? 0} / ${q.max_marks ?? 10}
                        </span>
                    </div>
                    ${q.extracted_answer ? `
                        <div class="answer-text">
                            <strong>Your Answer:</strong><br>${q.extracted_answer}
                        </div>
                    ` : ''}
                    ${q.feedback ? `
                        <div class="feedback-text">
                            <strong>💡 Feedback:</strong><br>${q.feedback}
                        </div>
                    ` : ''}
                    ${q.contradictions && q.contradictions.length > 0 ? `
                        <div class="contradiction-list">
                            <h5>⚠️ Points to Review</h5>
                            <ul>${q.contradictions.map(c => `<li>${c}</li>`).join('')}</ul>
                        </div>
                    ` : ''}
                    ${q.confidence_score ? `
                        <div style="margin-top: var(--space-3); font-size: var(--font-size-xs); color: var(--text-tertiary);">
                            AI Confidence: ${Math.round(q.confidence_score * 100)}%
                        </div>
                    ` : ''}
                </div>
            `).join('');
        }

    } catch (error) {
        showToast('Failed to load result details', 'error');
        console.error(error);
    }

    // Back to list button
    const backBtn = $('#back-to-list');
    if (backBtn) {
        backBtn.onclick = () => {
            detailSection.style.display = 'none';
            listSection.style.display = 'block';
        };
    }
}
