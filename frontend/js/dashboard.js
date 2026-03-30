/**
 * Dashboard Logic
 *
 * Loads and displays dashboard statistics, grade distribution chart,
 * and recent evaluations for the teacher view.
 */

async function loadDashboard() {
    try {
        const stats = await api.getDashboardStats();

        // Update stat cards
        const statEvals = $('#stat-evaluations');
        const statStudents = $('#stat-students');
        const statAvgScore = $('#stat-avg-score');
        const statSubjects = $('#stat-subjects');

        if (statEvals) statEvals.textContent = stats.total_evaluations;
        if (statStudents) statStudents.textContent = stats.total_students;
        if (statAvgScore) statAvgScore.textContent = `${Math.round(stats.average_score || 0)}%`;
        if (statSubjects) statSubjects.textContent = stats.subjects.length;

        // Render grade distribution chart
        renderGradeChart(stats.grade_distribution);

        // Render recent evaluations
        renderRecentEvaluations(stats.recent_evaluations);

    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

/**
 * Render grade distribution bar chart using Canvas API.
 */
function renderGradeChart(gradeDistribution) {
    const canvas = $('#grade-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    // High-DPI canvas
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.scale(dpr, dpr);

    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    const grades = ['A+', 'A', 'B+', 'B', 'C', 'D', 'F'];
    const colors = ['#10b981', '#34d399', '#06b6d4', '#3b82f6', '#f59e0b', '#f97316', '#ef4444'];
    const values = grades.map(g => gradeDistribution[g] || 0);
    const maxVal = Math.max(...values, 1);

    const padding = { top: 20, right: 20, bottom: 40, left: 40 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const barWidth = chartWidth / grades.length * 0.6;
    const barGap = chartWidth / grades.length * 0.4;

    // Draw bars
    grades.forEach((grade, i) => {
        const barHeight = (values[i] / maxVal) * chartHeight;
        const x = padding.left + i * (barWidth + barGap) + barGap / 2;
        const y = padding.top + chartHeight - barHeight;

        // Bar with gradient
        const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
        gradient.addColorStop(0, colors[i]);
        gradient.addColorStop(1, colors[i] + '60');
        ctx.fillStyle = gradient;

        // Rounded top corners
        const radius = 4;
        ctx.beginPath();
        ctx.moveTo(x, y + barHeight);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.lineTo(x + barWidth - radius, y);
        ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + radius);
        ctx.lineTo(x + barWidth, y + barHeight);
        ctx.fill();

        // Value on top
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'center';
        if (values[i] > 0) {
            ctx.fillText(values[i], x + barWidth / 2, y - 6);
        }

        // Grade label
        ctx.fillStyle = '#64748b';
        ctx.font = '12px Inter, sans-serif';
        ctx.fillText(grade, x + barWidth / 2, height - 12);
    });
}

/**
 * Render recent evaluations list.
 */
function renderRecentEvaluations(evaluations) {
    const container = $('#recent-evaluations');
    if (!container) return;

    if (!evaluations || evaluations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <h3>No evaluations yet</h3>
                <p>Upload and evaluate answer sheets to see results here.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = evaluations.map(ev => `
        <div class="flex items-center gap-4" style="padding: var(--space-3) 0; border-bottom: 1px solid var(--border-primary);">
            <div class="grade-badge ${getGradeClass(ev.grade)}" style="width: 36px; height: 36px; font-size: 0.875rem;">
                ${ev.grade || '—'}
            </div>
            <div style="flex: 1; min-width: 0;">
                <div style="font-weight: 500; font-size: var(--font-size-sm);">${ev.student_name || 'Unknown'}</div>
                <div style="font-size: var(--font-size-xs); color: var(--text-tertiary);">${ev.subject || '—'}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-weight: 600; font-size: var(--font-size-sm);">${ev.percentage ? Math.round(ev.percentage) + '%' : '—'}</div>
                <div style="font-size: var(--font-size-xs); color: var(--text-tertiary);">${timeAgo(ev.evaluated_at)}</div>
            </div>
        </div>
    `).join('');
}
