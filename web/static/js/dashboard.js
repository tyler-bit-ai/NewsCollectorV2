/**
 * News Collector Dashboard JavaScript
 */

// Global state
let currentTaskId = null;
let progressInterval = null;
let activities = [];

const RECIPIENT_GROUPS = {
    report: {
        label: '일반 리포트',
        inputId: 'report-new-email',
        addButtonId: 'report-add-recipient',
        listId: 'report-recipients',
        countId: 'report-recipient-count',
        emptyId: 'report-no-recipients',
    },
    safety_alert: {
        label: '해외 안전 공지',
        inputId: 'safety-new-email',
        addButtonId: 'safety-add-recipient',
        listId: 'safety-recipients',
        countId: 'safety-recipient-count',
        emptyId: 'safety-no-recipients',
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRecipients('report');
    loadRecipients('safety_alert');
    loadActivities();
    setupEventListeners();
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    document.getElementById('start-analysis').addEventListener('click', startAnalysis);
    document.getElementById('view-results').addEventListener('click', viewResults);
    document.getElementById('send-email').addEventListener('click', sendEmail);

    setupRecipientGroupEvents('report');
    setupRecipientGroupEvents('safety_alert');
}

function setupRecipientGroupEvents(group) {
    const config = RECIPIENT_GROUPS[group];
    const addButton = document.getElementById(config.addButtonId);
    const input = document.getElementById(config.inputId);

    addButton.addEventListener('click', () => addRecipient(group));
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addRecipient(group);
        }
    });
}

/**
 * Start news analysis
 */
async function startAnalysis() {
    try {
        const button = document.getElementById('start-analysis');
        button.disabled = true;

        const response = await fetch('/api/analysis/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();

        if (data.success) {
            currentTaskId = data.task_id;
            showToast('분석 시작', data.message, 'info');
            addActivity('🚀', '뉴스 분석 시작', data.message);

            document.getElementById('progress-container').style.display = 'block';
            updateSystemStatus('running');
            monitorProgress(data.task_id);
        } else {
            showToast('오류', data.message, 'error');
            button.disabled = false;
        }
    } catch (error) {
        console.error('Error starting analysis:', error);
        showToast('오류', '분석 시작 실패', 'error');
        document.getElementById('start-analysis').disabled = false;
    }
}

/**
 * Monitor analysis progress
 */
function monitorProgress(taskId) {
    if (progressInterval) {
        clearInterval(progressInterval);
    }

    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/analysis/status/${taskId}`);
            const data = await response.json();

            if (data.success) {
                updateProgress(data);
                if (data.status === 'completed') {
                    clearInterval(progressInterval);
                    handleAnalysisComplete(data);
                } else if (data.status === 'failed') {
                    clearInterval(progressInterval);
                    handleAnalysisFailed(data.error);
                }
            }
        } catch (error) {
            console.error('Error monitoring progress:', error);
        }
    }, 2000);
}

/**
 * Update progress display
 */
function updateProgress(data) {
    const progressPercent = data.progress;
    const progressText = document.getElementById('progress-text');
    const progressBar = document.getElementById('analysis-progress');
    const progressStatus = document.getElementById('progress-status');
    const progressDetails = document.getElementById('progress-details');
    const newsCollected = document.getElementById('news-collected');
    const newsAnalyzed = document.getElementById('news-analyzed');

    progressText.textContent = `${progressPercent}%`;
    progressBar.style.width = `${progressPercent}%`;

    if (progressPercent < 30) {
        progressStatus.textContent = '뉴스 수집 중...';
    } else if (progressPercent < 60) {
        progressStatus.textContent = '뉴스 분석 중...';
    } else if (progressPercent < 90) {
        progressStatus.textContent = '결과 저장 중...';
    } else {
        progressStatus.textContent = '완료!';
    }

    if (data.news_collected > 0 || data.news_analyzed > 0) {
        progressDetails.style.display = 'flex';
        newsCollected.textContent = `수집: ${data.news_collected}건`;
        newsAnalyzed.textContent = `분석: ${data.news_analyzed}건`;
    }
}

/**
 * Handle analysis completion
 */
function handleAnalysisComplete(data) {
    const button = document.getElementById('start-analysis');
    button.disabled = false;

    const viewResultsBtn = document.getElementById('view-results');
    viewResultsBtn.style.display = 'inline-flex';

    updateSystemStatus('normal');

    const result = data.result;
    const message = `분석 완료! 총 ${result.total}건의 뉴스를 수집하고 분석했습니다.`;
    showToast('분석 완료', message, 'success');
    addActivity('✅', '분석 완료', message);

    setTimeout(() => {
        document.getElementById('progress-container').style.display = 'none';
    }, 3000);
}

/**
 * Handle analysis failure
 */
function handleAnalysisFailed(error) {
    const button = document.getElementById('start-analysis');
    button.disabled = false;
    updateSystemStatus('error');

    const message = `분석 실패: ${error || '알 수 없는 오류'}`;
    showToast('오류', message, 'error');
    addActivity('❌', '분석 실패', message);
}

/**
 * Load recipients for a group
 */
async function loadRecipients(group) {
    try {
        const response = await fetch(`/api/recipients?group=${encodeURIComponent(group)}`);
        const data = await response.json();

        if (data.success) {
            displayRecipients(group, data.recipients || []);
        }
    } catch (error) {
        console.error(`Error loading recipients (${group}):`, error);
    }
}

/**
 * Display recipients list for a group
 */
function displayRecipients(group, recipients) {
    const config = RECIPIENT_GROUPS[group];
    const recipientsList = document.getElementById(config.listId);
    const recipientCount = document.getElementById(config.countId);
    const noRecipients = document.getElementById(config.emptyId);

    recipientsList.innerHTML = '';
    recipientCount.textContent = recipients.length;

    if (recipients.length === 0) {
        noRecipients.style.display = 'block';
        return;
    }

    noRecipients.style.display = 'none';
    recipients.forEach((email) => {
        const li = document.createElement('li');
        li.className = 'recipient-item';

        const emailSpan = document.createElement('span');
        emailSpan.className = 'recipient-email';
        emailSpan.textContent = email;

        const actions = document.createElement('div');
        actions.className = 'recipient-actions';

        const badge = document.createElement('span');
        badge.className = 'recipient-badge recipient-badge-custom';
        badge.textContent = '저장됨';

        const removeButton = document.createElement('button');
        removeButton.className = 'btn btn-danger btn-sm';
        removeButton.textContent = '삭제';
        removeButton.addEventListener('click', () => removeRecipient(group, email));

        actions.appendChild(badge);
        actions.appendChild(removeButton);
        li.appendChild(emailSpan);
        li.appendChild(actions);
        recipientsList.appendChild(li);
    });
}

/**
 * Add new recipient to group
 */
async function addRecipient(group) {
    const config = RECIPIENT_GROUPS[group];
    const emailInput = document.getElementById(config.inputId);
    const email = emailInput.value.trim().toLowerCase();

    if (!email) {
        showToast('입력 오류', '이메일 주소를 입력해주세요', 'warning');
        return;
    }
    if (!isValidEmail(email)) {
        showToast('형식 오류', '올바른 이메일 형식이 아닙니다', 'warning');
        return;
    }

    try {
        const response = await fetch(`/api/recipients?group=${encodeURIComponent(group)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });
        const data = await response.json();

        if (data.success) {
            showToast('성공', data.message, 'success');
            addActivity('➕', `${config.label} 수신자 추가`, `${email} 추가됨`);
            emailInput.value = '';
            loadRecipients(group);
        } else {
            showToast('실패', data.message, 'error');
        }
    } catch (error) {
        console.error(`Error adding recipient (${group}):`, error);
        showToast('오류', '수신자 추가 실패', 'error');
    }
}

/**
 * Remove recipient from group
 */
async function removeRecipient(group, email) {
    const config = RECIPIENT_GROUPS[group];
    if (!confirm(`'${email}' 님을 ${config.label} 수신자 목록에서 삭제하시겠습니까?`)) {
        return;
    }

    try {
        const response = await fetch(
            `/api/recipients/${encodeURIComponent(email)}?group=${encodeURIComponent(group)}`,
            { method: 'DELETE' }
        );
        const data = await response.json();

        if (data.success) {
            showToast('성공', data.message, 'success');
            addActivity('🗑️', `${config.label} 수신자 삭제`, `${email} 삭제됨`);
            loadRecipients(group);
        } else {
            showToast('실패', data.message, 'error');
        }
    } catch (error) {
        console.error(`Error removing recipient (${group}):`, error);
        showToast('오류', '수신자 삭제 실패', 'error');
    }
}

/**
 * Send report email
 */
async function sendEmail() {
    const emailStatus = document.getElementById('email-status');
    emailStatus.className = 'status-message info show';
    emailStatus.textContent = '이메일 발송 중...';

    try {
        const response = await fetch('/api/email/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
        });
        const data = await response.json();

        if (data.success) {
            emailStatus.className = 'status-message success show';
            emailStatus.textContent = data.message;
            showToast('성공', data.message, 'success');
            addActivity('✉️', '이메일 발송', data.message);
        } else {
            emailStatus.className = 'status-message error show';
            emailStatus.textContent = data.message;
            showToast('실패', data.message, 'error');
        }

        setTimeout(() => {
            emailStatus.className = 'status-message';
        }, 5000);
    } catch (error) {
        console.error('Error sending email:', error);
        emailStatus.className = 'status-message error show';
        emailStatus.textContent = '이메일 발송 실패';
        showToast('오류', '이메일 발송 실패', 'error');
    }
}

/**
 * View analysis results
 */
async function viewResults() {
    try {
        const response = await fetch('/api/latest-report');
        const data = await response.json();

        if (data.success) {
            window.open(data.url, '_blank');
        } else {
            showToast('리포트 없음', data.message || '생성된 리포트가 없습니다', 'warning');
        }
    } catch (error) {
        console.error('Error viewing results:', error);
        showToast('오류', '리포트를 불러올 수 없습니다', 'error');
    }
}

/**
 * Update system status
 */
function updateSystemStatus(status) {
    const statusBadge = document.getElementById('status-badge');

    switch (status) {
        case 'running':
            statusBadge.className = 'badge badge-warning';
            statusBadge.textContent = '분석중';
            break;
        case 'error':
            statusBadge.className = 'badge badge-danger';
            statusBadge.textContent = '오류';
            break;
        default:
            statusBadge.className = 'badge badge-success';
            statusBadge.textContent = '정상';
    }
}

/**
 * Add activity to log
 */
function addActivity(icon, title, message) {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });

    activities.unshift({ icon, title, message, time: timeStr });
    if (activities.length > 10) {
        activities = activities.slice(0, 10);
    }

    saveActivities();
    displayActivities();
}

/**
 * Display activities
 */
function displayActivities() {
    const activityLog = document.getElementById('activity-log');

    if (activities.length === 0) {
        activityLog.innerHTML = `
            <div class="empty-state">
                <p>활동 기록이 없습니다</p>
            </div>
        `;
        return;
    }

    activityLog.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <span class="activity-icon">${activity.icon}</span>
            <div class="activity-content">
                <div class="activity-title">${escapeHtml(activity.title)}</div>
                <div class="activity-time">${escapeHtml(activity.message)} • ${activity.time}</div>
            </div>
        </div>
    `).join('');
}

/**
 * Save activities to localStorage
 */
function saveActivities() {
    localStorage.setItem('newsCollectorActivities', JSON.stringify(activities));
}

/**
 * Load activities from localStorage
 */
function loadActivities() {
    const saved = localStorage.getItem('newsCollectorActivities');
    if (saved) {
        try {
            activities = JSON.parse(saved);
            displayActivities();
        } catch (error) {
            console.error('Error loading activities:', error);
            activities = [];
        }
    }
}

/**
 * Show toast notification
 */
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <div class="toast-content">
            <div class="toast-title">${escapeHtml(title)}</div>
            <div class="toast-message">${escapeHtml(message)}</div>
        </div>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
