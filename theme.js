// theme.js

// ==========================================
// ۱. ذرات پس‌زمینه (برای همه صفحات)
// ==========================================
function createParticles() {
    if (document.querySelector('.bg-particles')) return; 

    const bgContainer = document.createElement('div');
    bgContainer.className = 'bg-particles';
    bgContainer.id = 'particles';
    document.body.prepend(bgContainer);

    const particleCount = 30;
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        const size = Math.random() * 5 + 2 + 'px';
        particle.style.width = size;
        particle.style.height = size;
        particle.style.left = Math.random() * 100 + 'vw';
        particle.style.animationDuration = Math.random() * 10 + 5 + 's';
        particle.style.animationDelay = Math.random() * 5 + 's';
        bgContainer.appendChild(particle);
    }
}

// ==========================================
// ۲. سیستم Toast (پاپ‌آپ)
// ==========================================
function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        container.id = 'toastContainer';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-message">${message}</div>
        <button class="toast-btn" onclick="this.parentElement.remove()">فهمیدم</button>
    `;
    container.appendChild(toast);
}

// ==========================================
// ۳. مدیریت تم (روشن/تیره)
// ==========================================
function initTheme() {
    const currentTheme = localStorage.getItem('ojGam_theme');
    if (currentTheme === 'light') {
        document.body.classList.add('light-mode');
    }
}

function toggleTheme() {
    document.body.classList.toggle('light-mode');
    const isLight = document.body.classList.contains('light-mode');
    localStorage.setItem('ojGam_theme', isLight ? 'light' : 'dark');
    
    const themeBtn = document.getElementById('themeBtn');
    if (themeBtn) { themeBtn.textContent = isLight ? '🌙' : '☀️'; }
}

// ==========================================
// ۴. دکمه اسکرول هوشمند (Scroll to Top)
// ==========================================
function initScrollToggle() {
    let isAtBottom = false;

    // ساخت دکمه اگه وجود نداشت
    if (!document.getElementById('scrollBtn')) {
        const btn = document.createElement('button');
        btn.className = 'scroll-toggle-btn';
        btn.id = 'scrollBtn';
        btn.innerHTML = `<span id="scrollIcon">⬇️</span>`;
        btn.onclick = handleScrollToggle;
        document.body.appendChild(btn);
    }

    window.addEventListener('scroll', () => {
        const btn = document.getElementById('scrollBtn');
        const icon = document.getElementById('scrollIcon');
        if (!btn) return;

        const scrollTop = window.scrollY;
        const scrollHeight = document.documentElement.scrollHeight;
        const clientHeight = document.documentElement.clientHeight;

        if (scrollHeight > clientHeight + 100) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }

        if (scrollTop + clientHeight >= scrollHeight - 50) {
            if (!isAtBottom) {
                isAtBottom = true;
                btn.classList.add('at-top');
                icon.textContent = '⬆️';
            }
        } else if (scrollTop < 100) {
            if (isAtBottom) {
                isAtBottom = false;
                btn.classList.remove('at-top');
                icon.textContent = '⬇️';
            }
        }
    });
}

function handleScrollToggle() {
    const scrollBtn = document.getElementById('scrollBtn');
    if (scrollBtn.classList.contains('at-top')) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }
}

// ==========================================
// ۵. اجرای خودکار موقع لود شدن
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    createParticles();
    initScrollToggle();
});