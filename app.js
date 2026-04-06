const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// DOM Elements
const body = document.body;
const greetingEl = document.getElementById('greeting');
const userStatusEl = document.getElementById('userStatus');
const pointsEl = document.getElementById('userPoints');
const loader = document.getElementById('loader');

// URL Params
const urlParams = new URLSearchParams(window.location.search);
const isAdmin = urlParams.get('admin') === 'true';
const points = urlParams.get('points') || '0';
const refLink = urlParams.get('ref_link') || 'Loading...';

// Initialization
if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
    greetingEl.innerText = `Salom, ${tg.initDataUnsafe.user.first_name}!`;
    
    // Sync points & Referral link
    pointsEl.innerText = points;
    document.getElementById('refLink').innerText = refLink;

    if (isAdmin) {
        userStatusEl.innerText = "👑 VIP ADMIN";
        document.getElementById('upgradeBtn').innerText = "Admin Paneli (VIP)";
        document.getElementById('upgradeBtn').style.background = 'var(--secondary)';
    }
}

// Navigation System
function navTo(screenId) {
    // Hide all screens
    document.querySelectorAll('.screen').forEach(s => {
        s.classList.remove('active');
        s.style.display = 'none';
    });
    
    // Show target screen
    const target = document.getElementById(screenId);
    target.style.display = 'block';
    setTimeout(() => target.classList.add('active'), 10);

    // Update Bottom Nav Active State
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        // Simple mapping based on icon or text
        if (screenId === 'homeScreen' && link.innerText.includes('Asosiy')) link.classList.add('active');
        if (screenId === 'inviteScreen' && link.innerText.includes('Taklif')) link.classList.add('active');
        if (screenId === 'marketScreen' && link.innerText.includes('Market')) link.classList.add('active');
        if (screenId === 'apiReferatScreen' && link.innerText.includes('AI')) link.classList.add('active');
    });

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// AI Generation Logic
const generateAI = document.getElementById('generateAI');
generateAI.addEventListener('click', () => {
    if (!isAdmin && userStatusEl.innerText !== "👑 PRO") {
        tg.showAlert("Ushbu funksiya faqat PRO foydalanuvchilar uchun! Iltimos, tarifni faollashtiring.");
        return;
    }
    
    const topic = document.getElementById('aiTopic').value;
    if (!topic) {
        tg.showAlert("Mavzuni kiriting!");
        return;
    }

    loader.classList.remove('hidden');
    // Real generation via Bot
    tg.sendData(JSON.stringify({
        action: "generate_ai",
        topic: topic
    }));
    
    setTimeout(() => {
        loader.classList.add('hidden');
        tg.close();
    }, 1500);
});

// Copy & Share logic
document.getElementById('copyRefBtn')?.addEventListener('click', () => {
    const link = document.getElementById('refLink').innerText;
    navigator.clipboard.writeText(link);
    tg.showAlert("Taklif havolasi nusxalandi!");
});

document.getElementById('shareBtn')?.addEventListener('click', () => {
    const link = document.getElementById('refLink').innerText;
    const shareText = "🎓 Talabalar uchun eng foydali bot! Referatlar, materiallar va AI yordami:";
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(shareText)}`;
    tg.openTelegramLink(shareUrl);
});

// Payment logic
document.getElementById('confirmPayBtn').addEventListener('click', () => {
    tg.showConfirm("To'lov qildingizmi? Tasdiqlash uchun adminga yuboramiz.", (val) => {
        if (val) {
            loader.classList.remove('hidden');
            tg.sendData(JSON.stringify({ action: "payment_sent", plan: "PREMIUM (LIFE)" }));
            setTimeout(() => {
                loader.classList.add('hidden');
                tg.close();
            }, 1000);
        }
    });
});

// Initial View
window.onload = () => {
    navTo('homeScreen');
    tg.setHeaderColor('#0a0f1d');
};
