// Konfigurasi Routing
const routes = {
    '/': 'home',
    '/youtube': 'youtube',
    '/tiktok': 'tiktok',
    '/instagram': 'instagram'
};

// Fungsi Navigasi SPA
function navigateTo(url) {
    window.history.pushState(null, null, url);
    renderPage();
}

// Fungsi Render Halaman
function renderPage() {
    const path = window.location.pathname;
    const targetSection = routes[path] || 'home';

    // Sembunyikan semua section
    document.querySelectorAll('.page-section').forEach(sec => sec.classList.remove('active'));
    
    // Tampilkan section yang sesuai
    const activeSection = document.getElementById(targetSection);
    if(activeSection) activeSection.classList.add('active');

    // Update highlight di sidebar
    document.querySelectorAll('.nav-item').forEach(nav => {
        nav.classList.remove('active');
        if(nav.getAttribute('href') === path) nav.classList.add('active');
    });
}

// Intercept klik pada link agar tidak me-reload halaman
document.querySelectorAll('.nav-item').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        navigateTo(e.currentTarget.getAttribute('href'));
    });
});

// Event Listener Tombol Back & Home
window.addEventListener('popstate', renderPage); // Menangani tombol back browser

document.getElementById('btn-back').addEventListener('click', () => {
    window.history.back();
});

document.getElementById('logo').addEventListener('click', () => {
    navigateTo('/');
});

// Sidebar Toggle
document.getElementById('toggle-sidebar').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('minimized');
});

// Theme Toggle
document.getElementById('toggle-theme').addEventListener('click', () => {
    const body = document.body;
    body.classList.toggle('dark-mode');
    const isDark = body.classList.contains('dark-mode');
    document.getElementById('toggle-theme').innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
});

// Fungsi Fetch API yt-dlp
async function fetchDownload(inputId, resultId) {
    const url = document.getElementById(inputId).value;
    const resultDiv = document.getElementById(resultId);
    
    if (!url) return alert("Masukkan URL terlebih dahulu!");
    
    resultDiv.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Memproses link... Mohon tunggu.</p>';

    try {
        const response = await fetch(`/api/extract?url=${encodeURIComponent(url)}`);
        const data = await response.json();

        if (!response.ok) throw new Error(data.detail || "Gagal memproses video");

        let formatsHtml = data.formats.map(f => `
            <a href="${f.url}" target="_blank" class="format-item">
                <span><i class="fas fa-download"></i> ${f.ext.toUpperCase()}</span>
                <span>${f.resolution}</span>
            </a>
        `).join('');

        resultDiv.innerHTML = `
            <div class="result-card">
                <img src="${data.thumbnail}" alt="Thumbnail">
                <h3>${data.title}</h3>
                <br>
                <h4>Link Tersedia (Klik untuk Unduh/Lihat):</h4>
                <div class="format-list">${formatsHtml}</div>
            </div>
        `;
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// Inisialisasi saat load pertama kali
window.addEventListener('DOMContentLoaded', renderPage);
