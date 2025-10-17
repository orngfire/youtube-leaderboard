/**
 * YouTube Leaderboard Script
 * Loads and displays leaderboard data from leaderboard.json
 */

// Global variables
let leaderboardData = null;
let expandedRows = new Set();
let currentTab = 'top-creators';
let subscriberData = {};  // Store subscriber data with timestamps

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    loadLeaderboard();
});

/**
 * Load leaderboard data from JSON file
 */
async function loadLeaderboard() {
    try {
        showLoading();

        // Fetch leaderboard data
        // Try GitHub Pages data first (most up-to-date)
        const timestamp = new Date().getTime();
        let response = await fetch(`https://orngfire.github.io/youtube-leaderboard/leaderboard.json?t=${timestamp}`);

        // If GitHub data doesn't work, try local data
        if (!response.ok) {
            response = await fetch('leaderboard.json');
        }

        // If local data doesn't work, try test data
        if (!response.ok) {
            response = await fetch('leaderboard_test.json');
        }

        if (!response.ok) {
            throw new Error('Failed to load leaderboard data');
        }

        leaderboardData = await response.json();

        // Debug: Check if average_views exists in data
        if (leaderboardData && leaderboardData.length > 0) {
            console.log('Data loaded. First channel metrics:', leaderboardData[0].metrics);
            console.log('Has average_views?', 'average_views' in leaderboardData[0].metrics);
        }

        // Display data
        displayLeaderboard();

        // Update last updated time
        updateLastUpdated();

        // Hide loading, show main content
        hideLoading();
        showMainContent();

    } catch (error) {
        console.error('Error loading leaderboard:', error);
        showError();
    }
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    currentTab = tabName;

    // Update active tab button
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Display appropriate data
    displayLeaderboard();
}

/**
 * Display leaderboard data in table
 */
function displayLeaderboard() {
    // Support both old and new data structures
    const channels = leaderboardData.channels || leaderboardData.leaderboard;

    if (!leaderboardData || !channels || channels.length === 0) {
        showEmpty();
        return;
    }

    const tableBody = document.getElementById('table-body');
    const mobileCards = document.getElementById('mobile-cards');

    // Clear existing content
    tableBody.innerHTML = '';
    mobileCards.innerHTML = '';

    // Update table headers based on current tab
    updateTableHeaders();

    // Display data based on current tab
    switch(currentTab) {
        case 'most-active':
            displayMostActive(channels);
            break;
        case 'viral-hit':
            displayViralHit(channels);
            break;
        case 'most-subscribed':
            displayMostSubscribed(channels);
            break;
        case 'top-creators':
        default:
            displayTopCreators(channels);
            break;
    }
}

/**
 * Create table row for desktop view
 */
function createTableRow(channel) {
    const row = document.createElement('tr');
    row.className = `rank-${channel.rank}`;
    row.dataset.rank = channel.rank;

    // Create main row content
    const mainRow = `
        <td class="rank-cell">
            ${getRankDisplay(channel.rank)}
        </td>
        <td class="name-cell">
            <div class="name-wrapper">
                <div class="name-line">
                    <span class="name-text">${channel.name}</span>
                    <div class="badges">
                        ${createBadges(channel.badges, channel.badge_descriptions)}
                    </div>
                </div>
                <div class="channel-name">${channel.channel_handle ? '@' + channel.channel_handle : (channel.channel_name || '')}</div>
            </div>
        </td>
        <td class="total-score-cell">
            <div class="total-score-wrapper">
                <div class="total-score">
                    <span class="total-score-star">★</span>
                    <span class="score-number" data-target="${channel.total_score}">${formatNumber(channel.total_score)}</span>
                </div>
            </div>
        </td>
        <td class="score-cell">${formatNumber(channel.score_breakdown?.basic || channel.basic_score || 0)}</td>
        <td class="score-cell">${formatNumber(channel.score_breakdown?.engagement || channel.engagement_score || 0)}</td>
        <td class="score-cell viral-cell">${formatNumber(channel.score_breakdown?.viral || channel.viral_score || 0)}</td>
        <td class="score-cell growth-cell">${formatNumber(channel.score_breakdown?.growth || channel.growth_score || 0)}</td>
    `;

    row.innerHTML = mainRow;

    // Add expanded details row
    const detailsRow = document.createElement('tr');
    detailsRow.className = 'details-row';
    detailsRow.style.display = 'none';

    const detailsCell = document.createElement('td');
    detailsCell.colSpan = 7;
    detailsCell.innerHTML = createExpandedDetails(channel);
    detailsRow.appendChild(detailsCell);

    // Add click event to toggle details
    row.addEventListener('click', () => toggleDetails(row, detailsRow));

    // Create fragment to return both rows
    const fragment = document.createDocumentFragment();
    fragment.appendChild(row);
    fragment.appendChild(detailsRow);

    return fragment;
}

/**
 * Create mobile card view
 */
function createMobileCard(channel) {
    const card = document.createElement('div');
    card.className = 'mobile-card';

    card.innerHTML = `
        <div class="mobile-card-header">
            <div class="mobile-rank mobile-rank-${channel.rank}">
                ${getRankDisplay(channel.rank, true)}
            </div>
            <div class="mobile-total-score">
                ★ ${formatNumber(channel.total_score)}
            </div>
        </div>
        <div class="mobile-name">
            ${channel.name}
            ${channel.badges && channel.badges.length > 0 ?
                `<span class="mobile-badges-inline">${channel.badges.join('')}</span>` : ''}
        </div>
        <div class="mobile-channel">${channel.channel_handle ? '@' + channel.channel_handle : (channel.channel_name || '')}</div>
        <div class="mobile-scores">
            <div class="mobile-score-item">
                <div class="mobile-score-label">채널</div>
                <div class="mobile-score-value">${formatNumber(channel.score_breakdown?.basic || channel.basic_score || 0)}</div>
            </div>
            <div class="mobile-score-item">
                <div class="mobile-score-label">인게이지먼트</div>
                <div class="mobile-score-value">${formatNumber(channel.score_breakdown?.engagement || channel.engagement_score || 0)}</div>
            </div>
            <div class="mobile-score-item">
                <div class="mobile-score-label">바이럴</div>
                <div class="mobile-score-value">${formatNumber(channel.score_breakdown?.viral || channel.viral_score || 0)}</div>
            </div>
            <div class="mobile-score-item">
                <div class="mobile-score-label">성장</div>
                <div class="mobile-score-value">${formatNumber(channel.score_breakdown?.growth || channel.growth_score || 0)}</div>
            </div>
        </div>
        ${channel.badges && channel.badges.length > 0 && channel.badge_descriptions ? `
            <div class="mobile-badges">
                ${channel.badges.map(badge => {
                    const desc = channel.badge_descriptions[badge];
                    if (!desc) return '';
                    return `
                        <div class="mobile-badge-item">
                            <span class="mobile-badge-icon">${badge}</span>
                            <div class="mobile-badge-info">
                                <div class="mobile-badge-title">${desc.name}</div>
                                <div class="mobile-badge-message">${desc.message}</div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        ` : ''}
        <a href="${channel.channel_url}" target="_blank" class="mobile-channel-link">
            🔗 채널 바로가기
        </a>
    `;

    return card;
}

/**
 * Get rank display (medal or number)
 */
function getRankDisplay(rank, mobile = false) {
    const medals = {
        1: '🥇',
        2: '🥈',
        3: '🥉'
    };

    if (medals[rank]) {
        if (mobile) {
            return medals[rank];
        }
        return `<span class="rank-medal">${medals[rank]}</span>`;
    }

    return `<span class="rank-number">${rank}</span>`;
}

/**
 * Create badges with tooltips
 */
function createBadges(badges, descriptions) {
    if (!badges || badges.length === 0) return '';

    return badges.map(badge => {
        const desc = descriptions && descriptions[badge];
        const tooltipContent = desc ?
            `<div class="badge-tooltip">
                <div class="tooltip-header">
                    <span class="tooltip-emoji">${badge}</span>
                    <span class="tooltip-title">${desc.name}</span>
                </div>
                <div class="tooltip-message">${desc.message}</div>
            </div>` : '';

        return `
            <span class="badge" data-badge="${badge}">
                ${badge}
                ${tooltipContent}
            </span>
        `;
    }).join('');
}

/**
 * Create expanded details content
 */
function createExpandedDetails(channel) {
    const totalScore = channel.total_score || 0;
    const basicScore = channel.score_breakdown?.basic || channel.basic_score || 0;
    const engagementScore = channel.score_breakdown?.engagement || channel.engagement_score || 0;
    const viralScore = channel.score_breakdown?.viral || channel.viral_score || 0;
    const growthScore = channel.score_breakdown?.growth || channel.growth_score || 0;

    const basicPercent = totalScore > 0 ? Math.round((basicScore / totalScore) * 100) : 0;
    const engagementPercent = totalScore > 0 ? Math.round((engagementScore / totalScore) * 100) : 0;
    const viralPercent = totalScore > 0 ? Math.round((viralScore / totalScore) * 100) : 0;
    const growthPercent = totalScore > 0 ? Math.round((growthScore / totalScore) * 100) : 0;

    let badgeHtml = '';
    if (channel.badges && channel.badges.length > 0 && channel.badge_descriptions) {
        const badgeDetails = channel.badges.map(badge => {
            const desc = channel.badge_descriptions[badge];
            if (!desc) return '';

            // Handle object format with name and message
            let badgeName = '';
            let badgeMessage = '';

            if (typeof desc === 'object' && desc !== null) {
                badgeName = desc.name || '';
                badgeMessage = desc.message || '';
            } else if (typeof desc === 'string') {
                badgeMessage = desc;
            }

            return `
                <div class="badge-detail">
                    <span class="badge-detail-icon">${badge}</span>
                    <div class="badge-detail-info">
                        ${badgeName ? `<div class="badge-name">${badgeName}</div>` : ''}
                        ${badgeMessage ? `<div class="badge-message">${badgeMessage}</div>` : ''}
                    </div>
                </div>
            `;
        }).join('');

        if (badgeDetails) {
            badgeHtml = `
                <div class="detail-section">
                    <div class="detail-title">🏅 획득 뱃지</div>
                    <div class="badge-list">
                        ${badgeDetails}
                    </div>
                </div>
            `;
        }
    }

    return `
        <div class="expanded-content">
            <div class="detail-section">
                <div class="detail-title">📊 상세 점수 분석</div>
                <div class="score-breakdown">
                    <div class="score-item">
                        <span class="score-label">채널 점수</span>
                        <span class="score-value">${formatNumber(basicScore)}점 (${basicPercent}%)</span>
                    </div>
                    <div class="score-item">
                        <span class="score-label">인게이지먼트 점수</span>
                        <span class="score-value">${formatNumber(engagementScore)}점 (${engagementPercent}%)</span>
                    </div>
                    <div class="score-item">
                        <span class="score-label">바이럴 보너스</span>
                        <span class="score-value">${formatNumber(viralScore)}점 (${viralPercent}%)</span>
                    </div>
                    <div class="score-item">
                        <span class="score-label">성장 점수</span>
                        <span class="score-value">${formatNumber(growthScore)}점 (${growthPercent}%)</span>
                    </div>
                </div>
            </div>
            ${badgeHtml}
            <a href="${channel.channel_url}" target="_blank" class="channel-link-btn">
                🔗 채널 바로가기
            </a>
        </div>
    `;
}

/**
 * Toggle expanded details
 */
function toggleDetails(row, detailsRow) {
    const expandedContent = detailsRow.querySelector('.expanded-content');
    const isExpanded = detailsRow.style.display === 'table-row';

    // Close all other expanded rows
    document.querySelectorAll('.details-row').forEach(dr => {
        if (dr !== detailsRow) {
            dr.style.display = 'none';
            dr.querySelector('.expanded-content').classList.remove('show');
        }
    });

    document.querySelectorAll('tr.expanded').forEach(r => {
        if (r !== row) {
            r.classList.remove('expanded');
        }
    });

    // Toggle current row
    if (isExpanded) {
        detailsRow.style.display = 'none';
        expandedContent.classList.remove('show');
        row.classList.remove('expanded');
    } else {
        detailsRow.style.display = 'table-row';
        setTimeout(() => {
            expandedContent.classList.add('show');
        }, 10);
        row.classList.add('expanded');
    }
}

/**
 * Animate score numbers with count-up effect
 */
function animateScores() {
    const scoreElements = document.querySelectorAll('.score-number');

    scoreElements.forEach(element => {
        const target = parseInt(element.dataset.target);
        const duration = 1000; // 1 second
        const steps = 30;
        const stepDuration = duration / steps;
        const increment = target / steps;

        let current = 0;
        element.textContent = '0';
        element.classList.add('count-up');

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = formatNumber(Math.floor(current));
        }, stepDuration);
    });
}

/**
 * Format number with thousand separators
 */
function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return num.toLocaleString('ko-KR');
}

/**
 * Update last updated time
 */
function updateLastUpdated() {
    if (!leaderboardData || !leaderboardData.last_updated) return;

    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement) {
        // Parse ISO date string and convert to Korean timezone
        const date = new Date(leaderboardData.last_updated);

        // Format as Korean date/time
        const options = {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        };

        const formatter = new Intl.DateTimeFormat('ko-KR', options);
        const formattedDate = formatter.format(date);

        // Replace format to be more readable: "2024.10.14 15:30"
        const cleanDate = formattedDate
            .replace(/\. /g, '.')
            .replace(/\.$/, '')
            .replace(' ', ' ');

        lastUpdatedElement.innerHTML = `<span style="color: #666;">마지막 업데이트:</span> <span style="color: #333;">${cleanDate} (KST)</span>`;
    }
}

/**
 * Refresh data - DISABLED
 * Manual refresh is no longer allowed
 * Updates happen automatically at 00:00, 08:00, 16:00 KST
 */
// function refreshData() {
//     const refreshBtn = document.getElementById('refresh-btn');
//     refreshBtn.classList.add('loading');
//
//     // Reload the page to fetch fresh data
//     setTimeout(() => {
//         location.reload();
//     }, 500);
// }

/**
 * Show loading state
 */
function showLoading() {
    document.getElementById('loading-state').style.display = 'flex';
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('main-container').style.display = 'none';
    document.getElementById('mobile-container').style.display = 'none';
}

/**
 * Hide loading state
 */
function hideLoading() {
    document.getElementById('loading-state').style.display = 'none';
}

/**
 * Show main content
 */
function showMainContent() {
    // Check screen size and show appropriate container
    if (window.innerWidth <= 768) {
        document.getElementById('mobile-container').style.display = 'block';
        document.getElementById('main-container').style.display = 'none';
    } else {
        document.getElementById('main-container').style.display = 'block';
        document.getElementById('mobile-container').style.display = 'none';
    }
}

/**
 * Show error state
 */
function showError() {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('error-state').style.display = 'flex';
    document.getElementById('main-container').style.display = 'none';
    document.getElementById('mobile-container').style.display = 'none';
}

/**
 * Show empty state
 */
function showEmpty() {
    document.getElementById('empty-state').style.display = 'block';
    document.getElementById('table-body').innerHTML = '';
    document.getElementById('mobile-cards').innerHTML = '';
}

// Handle window resize to switch between desktop and mobile views
window.addEventListener('resize', () => {
    if (leaderboardData) {
        showMainContent();
    }
});

// Add smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

/**
 * Update table headers based on current tab
 */
function updateTableHeaders() {
    const thead = document.querySelector('.leaderboard-table thead tr');

    switch(currentTab) {
        case 'most-active':
            thead.innerHTML = `
                <th class="th-rank">순위</th>
                <th class="th-name">이름</th>
                <th class="th-total">게재 영상 수</th>
                <th class="th-basic">평균 조회수</th>
                <th class="th-engagement">평균 좋아요</th>
            `;
            break;
        case 'viral-hit':
            thead.innerHTML = `
                <th class="th-rank">순위</th>
                <th class="th-name">이름</th>
                <th class="th-total">최고 조회수</th>
                <th class="th-basic">좋아요</th>
                <th class="th-engagement">댓글</th>
                <th class="th-viral">인게이지먼트</th>
            `;
            break;
        case 'most-subscribed':
            thead.innerHTML = `
                <th class="th-rank">순위</th>
                <th class="th-name">이름</th>
                <th class="th-total">구독자 수</th>
                <th class="th-basic">평가 기간 증가</th>
                <th class="th-engagement">총 게재 영상 수</th>
            `;
            break;
        case 'top-creators':
        default:
            thead.innerHTML = `
                <th class="th-rank">순위</th>
                <th class="th-name">이름</th>
                <th class="th-total">총 점수</th>
                <th class="th-basic">채널</th>
                <th class="th-engagement">인게이지먼트</th>
                <th class="th-viral">바이럴</th>
                <th class="th-growth">성장</th>
            `;
            break;
    }

    // Force rank column width after DOM update
    setTimeout(() => {
        const rankHeaders = document.querySelectorAll('.th-rank');
        const rankCells = document.querySelectorAll('.rank-cell');

        rankHeaders.forEach(th => {
            th.style.width = '100px';
            th.style.minWidth = '100px';
            th.style.maxWidth = '100px';
        });

        rankCells.forEach(td => {
            td.style.width = '100px';
            td.style.minWidth = '100px';
            td.style.maxWidth = '100px';
        });
    }, 0);
}

/**
 * Display Top Creators (existing leaderboard)
 */
function displayTopCreators(channels) {
    const tableBody = document.getElementById('table-body');
    const mobileCards = document.getElementById('mobile-cards');

    channels.forEach((channel) => {
        // Desktop table row
        const row = createTableRow(channel);
        tableBody.appendChild(row);

        // Mobile card
        const card = createMobileCard(channel);
        mobileCards.appendChild(card);
    });

    // Add count-up animation to total scores
    animateScores();
}

/**
 * Display Most Active tab (by video count)
 * Based on videos published during evaluation period (2025.10.02 - 2025.12.14)
 */
function displayMostActive(channels) {
    const tableBody = document.getElementById('table-body');

    // Sort by video count (videos from evaluation period)
    const sortedChannels = [...channels].sort((a, b) => {
        const aCount = a.metrics?.video_count || 0;
        const bCount = b.metrics?.video_count || 0;
        return bCount - aCount;
    });

    sortedChannels.forEach((channel, index) => {
        const row = document.createElement('tr');
        const videoCount = channel.metrics?.video_count || 0;
        const avgViews = Math.round(channel.metrics?.average_views || 0);
        // Debug logging
        if (index === 0) {
            console.log('Most Active Tab Debug:', {
                channel: channel.name,
                metrics: channel.metrics,
                average_views: channel.metrics?.average_views,
                median_score: channel.metrics?.median_score,
                avgViews_calculated: avgViews
            });
        }
        // Use average_likes for the average likes count
        const avgLikes = Math.round(channel.metrics?.average_likes || 0);

        row.innerHTML = `
            <td class="rank-cell">
                ${index < 3 ? `<span class="rank-medal">${['🥇', '🥈', '🥉'][index]}</span>` : `<span class="rank-number">${index + 1}</span>`}
            </td>
            <td class="name-cell">
                <div class="name-wrapper">
                    <div class="name-line">
                        <span class="name-text">${channel.name}</span>
                    </div>
                    <div class="channel-name">@${channel.channel_handle}</div>
                </div>
            </td>
            <td class="score-cell">
                <span class="score-badge">🎬 ${videoCount}개</span>
            </td>
            <td class="score-cell">${avgViews.toLocaleString()}</td>
            <td class="score-cell">${avgLikes.toLocaleString()}</td>
        `;

        row.className = `rank-${index + 1}`;
        tableBody.appendChild(row);
    });
}

/**
 * Display Most Subscribed tab
 * Based on current subscriber count (not limited to evaluation period)
 */
function displayMostSubscribed(channels) {
    const tableBody = document.getElementById('table-body');

    // Sort by actual subscriber count from metrics
    const sortedChannels = [...channels].sort((a, b) => {
        const aSubs = a.metrics?.subscriber_count || 0;
        const bSubs = b.metrics?.subscriber_count || 0;
        return bSubs - aSubs;
    });

    sortedChannels.forEach((channel, index) => {
        // Use actual subscriber count from metrics
        const currentSubs = channel.metrics?.subscriber_count || 0;
        const subsChange = channel.metrics?.subscriber_change || 0;
        const subsChangePercent = channel.metrics?.subscriber_change_percent || 0;

        // Use total_video_count for all videos, regardless of evaluation period
        const totalVideoCount = channel.metrics?.total_video_count || 0;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="rank-cell">
                ${index < 3 ? `<span class="rank-medal">${['🥇', '🥈', '🥉'][index]}</span>` : `<span class="rank-number">${index + 1}</span>`}
            </td>
            <td class="name-cell">
                <div class="name-wrapper">
                    <div class="name-line">
                        <span class="name-text">${channel.name}</span>
                    </div>
                    <div class="channel-name">@${channel.channel_handle}</div>
                </div>
            </td>
            <td class="score-cell">
                <span class="score-badge">👥 ${currentSubs >= 1000 ? (currentSubs / 1000).toFixed(1) + 'K' : currentSubs.toLocaleString()}</span>
            </td>
            <td class="score-cell">
                <span style="color: ${subsChange >= 0 ? '#22c55e' : '#ef4444'}">
                    ${subsChange >= 0 ? '+' : ''}${subsChange}
                    ${subsChangePercent !== 0 ? ` (${subsChangePercent > 0 ? '+' : ''}${subsChangePercent.toFixed(1)}%)` : ''}
                </span>
            </td>
            <td class="score-cell">${totalVideoCount}개</td>
        `;

        row.className = `rank-${index + 1}`;
        tableBody.appendChild(row);
    });
}

/**
 * Display Viral Hit tab (highest view video)
 * Based on videos published during evaluation period (2025.10.02 - 2025.12.14)
 */
function displayViralHit(channels) {
    const tableBody = document.getElementById('table-body');

    // Sort by highest view count from actual data
    const sortedChannels = [...channels].sort((a, b) => {
        const aViews = a.metrics?.viral_video?.views || 0;
        const bViews = b.metrics?.viral_video?.views || 0;
        return bViews - aViews;
    });

    sortedChannels.forEach((channel, index) => {
        // Use actual viral_video data from metrics (single highest view video from evaluation period)
        const video = channel.metrics?.viral_video || { views: 0, likes: 0, comments: 0 };
        // Calculate engagement with 2x weight for comments (same as main leaderboard)
        const engagement = video.views > 0 ?
            ((video.likes + video.comments * 2) / video.views * 100).toFixed(2) : 0;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="rank-cell">
                ${index < 3 ? `<span class="rank-medal">${['🥇', '🥈', '🥉'][index]}</span>` : `<span class="rank-number">${index + 1}</span>`}
            </td>
            <td class="name-cell">
                <div class="name-wrapper">
                    <div class="name-line">
                        <span class="name-text">${channel.name}</span>
                    </div>
                    <div class="channel-name">@${channel.channel_handle}</div>
                </div>
            </td>
            <td class="score-cell">
                <span class="score-badge">🔥 ${video.views.toLocaleString()}</span>
            </td>
            <td class="score-cell">${video.likes.toLocaleString()}</td>
            <td class="score-cell">${video.comments.toLocaleString()}</td>
            <td class="score-cell">${engagement}%</td>
        `;

        row.className = `rank-${index + 1}`;
        tableBody.appendChild(row);
    });
}