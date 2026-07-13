const platforms = {
    '/youtube': { title: 'YouTube Downloader', icon: 'fab fa-youtube', color: '#ff0000', placeholder: 'Tempel link YouTube di sini...' },
    '/tiktok': { title: 'TikTok Downloader', icon: 'fab fa-tiktok', color: 'var(--text-color)', placeholder: 'Tempel link TikTok di sini...' },
    '/instagram': { title: 'Instagram Downloader', icon: 'fab fa-instagram', color: '#e1306c', placeholder: 'Tempel link Instagram di sini...' },
    '/facebook': { title: 'Facebook Downloader', icon: 'fab fa-facebook', color: '#1877f2', placeholder: 'Tempel link Facebook di sini...' },
    '/twitter': { title: 'X (Twitter) Downloader', icon: 'fab fa-x-twitter', color: 'var(--text-color)', placeholder: 'Tempel link X/Twitter di sini...' },
    '/threads': { title: 'Threads Downloader', icon: 'fas fa-at', color: 'var(--text-color)', placeholder: 'Tempel link Threads di sini...' },
};

function navigateTo(url) {
    window.history.pushState(null, null, url);
    renderPage();
}

function renderPage() {
    const path = window.location.pathname;
    
    // Reset Views
    document.getElementById('page-home').classList.remove('active');
    document.getElementById('page-downloader').classList.remove('active');
    document.getElementById('dl-result').innerHTML = ''; 
    document.getElementById('dl-input').value = '';

    // Update Sidebar Active State
    document.querySelectorAll('.nav-item').forEach(nav => {
        nav.classList.remove('active');
        if(nav.getAttribute('href') === path) nav.classList.add('active');
    });

    if (path === '/' || !platforms[path]) {
        document.getElementById('page-home').classList.add('active');
    } else {
        document.getElementById('page-downloader').classList.add('active');
        const p = platforms[path];
        
        // Update UI dynamically based on platform
        document.getElementById('dl-title').innerText = p.title;
        document.getElementById('dl-icon').className = p.icon;
        document.getElementById('dl-icon').style.color = p.color;
        document.getElementById('dl-input').placeholder = p.placeholder;
    }
}

// Event Listeners Routing
document.querySelectorAll('a[href^="/"]').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        navigateTo(e.currentTarget.getAttribute('href'));
        // Auto close sidebar on mobile
        if(window.innerWidth <= 768) {
            document.getElementById('sidebar').classList.remove('minimized');
        }
    });
});

window.addEventListener('popstate', renderPage);

document.getElementById('btn-back').addEventListener('click', () => { window.history.back(); });
document.getElementById('logo').addEventListener('click', () => { navigateTo('/'); });

document.getElementById('toggle-sidebar').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('minimized');
});

document.getElementById('toggle-theme').addEventListener('click', () => {
    const body = document.body;
    body.classList.toggle('dark-mode');
    document.getElementById('toggle-theme').innerHTML = body.classList.contains('dark-mode') ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
});

async function processDownload() {
    const url = document.getElementById('dl-input').value;
    const resultDiv = document.getElementById('dl-result');
    const btn = document.getElementById('btn-process');
    
    if (!url) return alert("URL tidak boleh kosong!");
    
    resultDiv.innerHTML = '<div style="text-align:center; padding: 20px;"><i class="fas fa-spinner fa-spin fa-2x"></i><p style="margin-top:10px;">Sedang memproses link... (Bisa memakan waktu 10-30 detik)</p></div>';
    btn.disabled = true;

    try {
        const response = await fetch(`/api/extract?url=${encodeURIComponent(url)}`);
        const data = await response.json();

        if (!response.ok) throw new Error(data.detail || "Gagal memproses video");

        if (!data.formats || data.formats.length === 0) {
            throw new Error("Tidak ada format video/audio yang ditemukan dari link ini.");
        }

        let formatsHtml = data.formats.map(f => `
            <a href="${f.url}" target="_blank" class="format-item">
                <span><i class="fas fa-file-download"></i> ${f.label}</span>
                <span style="text-transform: uppercase; font-size: 12px; background: var(--bg-color); padding: 3px 8px; border-radius: 4px;">${f.ext}</span>
            </a>
        `).join('');

        resultDiv.innerHTML = `
            <div class="result-card">
                ${data.thumbnail ? `<img src="${data.thumbnail}" alt="Thumbnail">` : ''}
                <h3>${data.title}</h3>
                <div class="format-list">${formatsHtml}</div>
            </div>
        `;
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="result-card" style="border-color: #dc3545;">
                <i class="fas fa-exclamation-triangle" style="color: #dc3545; font-size: 30px; margin-bottom: 15px;"></i>
                <h3 style="color: #dc3545;">Terjadi Kesalahan</h3>
                <p>${error.message}</p>
                <p style="font-size: 12px; margin-top:10px; color: gray;">*Catatan: YouTube dan Instagram sering memblokir server secara acak. Coba lagi nanti atau gunakan video lain.</p>
            </div>`;
    } finally {
        btn.disabled = false;
    }
}

window.addEventListener('DOMContentLoaded', renderPage);
