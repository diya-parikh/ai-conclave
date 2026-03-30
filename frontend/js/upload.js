/**
 * Upload Page Logic
 *
 * Handles file selection, drag & drop, form submission,
 * and pipeline progress tracking.
 */

document.addEventListener('DOMContentLoaded', () => {
    const uploadZone = $('#upload-zone');
    const fileInput = $('#file-input');
    const filePreview = $('#file-preview');
    const uploadForm = $('#upload-form');
    const uploadBtn = $('#upload-submit-btn');
    const processSection = $('#processing-section');
    const pipelineSteps = $('#pipeline-steps');

    // Knowledge upload elements
    const knowledgeUploadZone = $('#knowledge-upload-zone');
    const knowledgeFileInput = $('#knowledge-file-input');
    const knowledgeForm = $('#knowledge-form');
    const knowledgeBtn = $('#knowledge-submit-btn');

    let selectedFile = null;
    let selectedKnowledgeFile = null;

    if (!uploadZone || !fileInput) return;

    // ---- Drag & Drop ----
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    // ---- File Input Change ----
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    function handleFileSelect(file) {
        selectedFile = file;
        uploadBtn.disabled = false;

        // Show file preview
        filePreview.style.display = 'block';
        filePreview.innerHTML = `
            <div class="file-preview">
                <div class="file-icon">📄</div>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
                <button class="btn btn-ghost btn-sm" id="remove-file">✕</button>
            </div>
        `;

        $('#remove-file').addEventListener('click', () => {
            selectedFile = null;
            filePreview.style.display = 'none';
            fileInput.value = '';
            uploadBtn.disabled = true;
        });
    }

    // ---- Upload Form Submission ----
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (!selectedFile) {
                showToast('Please select a file first', 'error');
                return;
            }

            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<div class="spinner"></div> Uploading...';

            try {
                // Step 1: Upload file
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('student_name', $('#student-name').value);
                formData.append('student_email', $('#student-email-input').value);
                formData.append('subject', $('#subject-input').value);
                formData.append('exam_name', $('#exam-name-input').value || '');

                showPipelineProgress('upload', 'running');
                const uploadResult = await api.uploadDocument(formData);
                showPipelineProgress('upload', 'done');
                showToast('File uploaded successfully!', 'success');

                // Step 2: Process document (OCR + NLP)
                showPipelineProgress('process', 'running');
                uploadBtn.innerHTML = '<div class="spinner"></div> Processing OCR...';
                const processResult = await api.processDocument(uploadResult.id);
                showPipelineProgress('process', 'done');
                showToast('Document processed!', 'success');

                // Step 3: Evaluate
                showPipelineProgress('evaluate', 'running');
                uploadBtn.innerHTML = '<div class="spinner"></div> Evaluating...';
                const evalResult = await api.evaluateDocument(uploadResult.id);
                showPipelineProgress('evaluate', 'done');
                showToast('Evaluation complete!', 'success');

                // Reset form
                uploadForm.reset();
                selectedFile = null;
                filePreview.style.display = 'none';
                fileInput.value = '';
                uploadBtn.disabled = true;
                uploadBtn.textContent = '📤 Upload & Process';

                showToast(`Score: ${evalResult.total_marks}/${evalResult.max_marks} (${evalResult.grade})`, 'success', 6000);

            } catch (error) {
                showToast(error.message, 'error');
                uploadBtn.disabled = false;
                uploadBtn.textContent = '📤 Upload & Process';
            }
        });
    }

    function showPipelineProgress(step, status) {
        if (!processSection || !pipelineSteps) return;
        processSection.style.display = 'block';

        const steps = {
            upload: { label: '📤 Uploading File', order: 1 },
            process: { label: '🔍 OCR + NLP Processing', order: 2 },
            evaluate: { label: '🧠 AI Evaluation', order: 3 },
        };

        const stepConfig = steps[step];
        if (!stepConfig) return;

        let stepEl = $(`#step-${step}`);
        if (!stepEl) {
            stepEl = createElement('div', {
                id: `step-${step}`,
                className: 'flex items-center gap-4',
                style: 'padding: var(--space-3) 0; border-bottom: 1px solid var(--border-primary);',
            });
            pipelineSteps.appendChild(stepEl);
        }

        const statusIcon = status === 'running'
            ? '<div class="spinner"></div>'
            : status === 'done'
            ? '✅'
            : '⏳';

        stepEl.innerHTML = `
            ${statusIcon}
            <span style="flex: 1; font-size: var(--font-size-sm);">${stepConfig.label}</span>
            <span class="badge ${status === 'done' ? 'badge-success' : 'badge-warning'}">${status === 'done' ? 'Complete' : 'In Progress'}</span>
        `;
    }

    // ---- Knowledge Base Upload ----
    if (knowledgeFileInput) {
        knowledgeFileInput.addEventListener('change', () => {
            if (knowledgeFileInput.files.length > 0) {
                selectedKnowledgeFile = knowledgeFileInput.files[0];
                knowledgeBtn.disabled = false;
            }
        });
    }

    if (knowledgeForm) {
        knowledgeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!selectedKnowledgeFile) {
                showToast('Please select a file first', 'error');
                return;
            }

            knowledgeBtn.disabled = true;
            knowledgeBtn.innerHTML = '<div class="spinner"></div> Ingesting...';

            try {
                const formData = new FormData();
                formData.append('file', selectedKnowledgeFile);
                formData.append('subject', $('#knowledge-subject').value);
                formData.append('document_type', $('#knowledge-type').value);

                const result = await api.ingestKnowledge(formData);
                showToast(`Ingested ${result.chunks_created} chunks successfully!`, 'success');

                knowledgeForm.reset();
                selectedKnowledgeFile = null;
                knowledgeFileInput.value = '';
                knowledgeBtn.disabled = true;
                knowledgeBtn.textContent = '📚 Ingest Document';

            } catch (error) {
                showToast(error.message, 'error');
                knowledgeBtn.disabled = false;
                knowledgeBtn.textContent = '📚 Ingest Document';
            }
        });
    }
});
