// 상태 관리
let leaderboardData = null;
let previousData = null;

// 뱃지 정보
const BADGE_INFO = {
    '🎯': { name: '안정 러너', desc: '중앙값 5,000점 이상' },
    '💬': { name: '인게이지먼트 킹', desc: '평균 인게이지먼트율 5% 이상' },
    '🔥': { name: '바이럴 메이커', desc: 'Top 3 평균이 중앙값의 10배 이상' },
    '📈': { name: '성장 로켓', desc: '성장 비율 1.5 이상' },
    '⭐': { name: '올라운더', desc: '모든 지표 평균 이상' }
};

// DOM 로드 완료 후 실행
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadLeaderboard();
    setupEventListeners();
});

// 테마 초기화
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

// 테마 아이콘 업데이트
function updateThemeIcon(theme) {
    const themeIcon = document.querySelector('.theme-icon');
    themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 새로고침 버튼
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadLeaderboard(true);
    });

    // 테마 토글
    document.getElementById('themeToggle').addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

// 리더보드 데이터 로드
async function loadLeaderboard(forceReload = false) {
    const refreshBtn = document.getElementById('refreshBtn');
    const leaderboardContainer = document.getElementById('leaderboard');

    if (forceReload) {
        refreshBtn.classList.add('loading');
    }

    try {
        // 캐시 방지를 위한 타임스탬프 추가
        const timestamp = forceReload ? `?t=${Date.now()}` : '';
        const response = await fetch(`leaderboard.json${timestamp}`);

        if (!response.ok) {
            throw new Error('데이터를 불러올 수 없습니다.');
        }

        previousData = leaderboardData;
        leaderboardData = await response.json();

        updateLastUpdateTime(leaderboardData.last_updated);
        renderLeaderboard(leaderboardData.leaderboard);

    } catch (error) {
        console.error('Error loading leaderboard:', error);
        leaderboardContainer.innerHTML = `
            <div class="loading">
                <p style="color: var(--danger);">❌ 데이터를 불러오는데 실패했습니다.</p>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">${error.message}</p>
            </div>
        `;
    } finally {
        refreshBtn.classList.remove('loading');
    }
}

// 마지막 업데이트 시간 표시
function updateLastUpdateTime(isoTime) {
    const date = new Date(isoTime);
    const formatter = new Intl.DateTimeFormat('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Seoul'
    });

    document.getElementById('lastUpdate').textContent = formatter.format(date);
}

// 리더보드 렌더링
function renderLeaderboard(data) {
    const container = document.getElementById('leaderboard');
    container.innerHTML = '';

    data.forEach(item => {
        const card = createLeaderboardCard(item);
        container.appendChild(card);
    });
}

// 리더보드 카드 생성
function createLeaderboardCard(item) {
    const card = document.createElement('div');
    card.className = `leaderboard-card rank-${item.rank}`;

    // 채널을 찾을 수 없거나 데이터가 없는 경우
    if (item.status === 'channel_not_found') {
        card.innerHTML = createChannelNotFoundCard(item);
        return card;
    }

    // 메달 표시
    const medalEmoji = item.rank === 1 ? '🥇' : item.rank === 2 ? '🥈' : item.rank === 3 ? '🥉' : '';
    const rankDisplay = medalEmoji || `${item.rank}위`;

    // 점수 변동 계산
    const scoreChange = calculateScoreChange(item);

    card.innerHTML = `
        <div class="card-header">
            <div class="rank-badge">${rankDisplay}</div>
            <div class="channel-thumbnail">${getInitial(item.name)}</div>
            <div class="channel-info">
                <div class="channel-name">
                    <span>${item.name}</span>
                    ${item.badges.length > 0 ? `<span class="channel-badges">${item.badges.join(' ')}</span>` : ''}
                </div>
                <div class="channel-handle">@${item.channel_handle}</div>
            </div>
            <div class="score-display">
                <div class="total-score">${item.total_score.toLocaleString()}</div>
                <div class="score-label">점</div>
                ${scoreChange}
            </div>
        </div>
        <div class="card-details">
            ${createScoreBreakdown(item)}
            ${createMetrics(item)}
            ${createBadgesEarned(item)}
            <a href="${item.channel_url}" target="_blank" rel="noopener noreferrer" class="channel-link">
                <span>📺</span>
                <span>채널 바로가기</span>
            </a>
        </div>
    `;

    // 클릭 이벤트 (상세 정보 토글)
    card.addEventListener('click', (e) => {
        // 링크 클릭은 제외
        if (e.target.closest('.channel-link')) return;

        card.classList.toggle('expanded');
    });

    return card;
}

// 채널을 찾을 수 없는 경우 카드
function createChannelNotFoundCard(item) {
    const medalEmoji = item.rank === 1 ? '🥇' : item.rank === 2 ? '🥈' : item.rank === 3 ? '🥉' : '';
    const rankDisplay = medalEmoji || `${item.rank}위`;

    return `
        <div class="card-header">
            <div class="rank-badge">${rankDisplay}</div>
            <div class="channel-thumbnail">${getInitial(item.name)}</div>
            <div class="channel-info">
                <div class="channel-name">
                    <span>${item.name}</span>
                </div>
                <div class="channel-handle">@${item.channel_handle}</div>
            </div>
            <div class="score-display">
                <div class="total-score">0</div>
                <div class="score-label">점</div>
            </div>
        </div>
        <div class="insufficient-data">
            <div class="insufficient-data-icon">❌</div>
            <div class="insufficient-data-text">
                ${item.video_count === 0 ? '평가 기간 내 영상이 없습니다.' : `평가 기간 내 영상이 ${item.video_count}개입니다.`}<br>
                0점으로 처리됩니다.
            </div>
        </div>
    `;
}

// 이름의 첫 글자 추출
function getInitial(name) {
    return name.charAt(0);
}

// 점수 변동 계산
function calculateScoreChange(item) {
    if (!previousData) return '';

    const prevItem = previousData.leaderboard.find(p => p.name === item.name);
    if (!prevItem || prevItem.status !== 'success') return '';

    const change = item.total_score - prevItem.total_score;
    if (change === 0) return '';

    const arrow = change > 0 ? '▲' : '▼';
    const color = change > 0 ? 'var(--success)' : 'var(--danger)';

    return `<div style="font-size: 0.75rem; color: ${color}; margin-top: 0.25rem;">${arrow} ${Math.abs(change).toLocaleString()}</div>`;
}

// 점수 분석
function createScoreBreakdown(item) {
    return `
        <div class="score-breakdown">
            <div class="score-item">
                <div class="score-item-label">기본 점수</div>
                <div class="score-item-value">${item.score_breakdown.basic.toLocaleString()}</div>
            </div>
            <div class="score-item">
                <div class="score-item-label">인게이지먼트</div>
                <div class="score-item-value">${item.score_breakdown.engagement.toLocaleString()}</div>
            </div>
            <div class="score-item">
                <div class="score-item-label">바이럴</div>
                <div class="score-item-value">${item.score_breakdown.viral.toLocaleString()}</div>
            </div>
            <div class="score-item">
                <div class="score-item-label">성장</div>
                <div class="score-item-value">${item.score_breakdown.growth.toLocaleString()}</div>
            </div>
        </div>
    `;
}

// 상세 지표
function createMetrics(item) {
    return `
        <div class="metrics-section">
            <h4>상세 지표</h4>
            <div class="metrics-grid">
                <div class="metric-item">
                    <span class="metric-label">영상 수</span>
                    <span class="metric-value">${item.metrics.video_count}개</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">중앙값</span>
                    <span class="metric-value">${item.metrics.median_score.toLocaleString()}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">인게이지먼트율</span>
                    <span class="metric-value">${item.metrics.avg_engagement}%</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Top 3 평균</span>
                    <span class="metric-value">${item.metrics.top3_avg.toLocaleString()}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">성장 비율</span>
                    <span class="metric-value">${item.metrics.growth_ratio}</span>
                </div>
            </div>
        </div>
    `;
}

// 획득 뱃지
function createBadgesEarned(item) {
    if (item.badges.length === 0) {
        return `
            <div class="badges-earned">
                <h4>획득 뱃지</h4>
                <p style="font-size: 0.875rem; color: var(--text-secondary);">획득한 뱃지가 없습니다.</p>
            </div>
        `;
    }

    const badgesHtml = item.badges.map(badge => {
        const info = BADGE_INFO[badge];
        return `
            <div class="earned-badge">
                <span>${badge}</span>
                <span>${info.name}</span>
            </div>
        `;
    }).join('');

    return `
        <div class="badges-earned">
            <h4>획득 뱃지</h4>
            <div class="earned-badges-list">
                ${badgesHtml}
            </div>
        </div>
    `;
}
