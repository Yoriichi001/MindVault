/**
 * MINDVAULT[E-BOOK]
 * Core Interactive Logic & Security Hardening Scripts
 */

// Safe XSS mitigation utility for dynamic DOM insertion
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', function () {
    // 1. Heritage 3D Book Cover Open Animation
    const openBookBtn = document.getElementById('openBookBtn');
    const closeBookBtn = document.getElementById('closeBookBtn');
    const browseLibraryBtn = document.getElementById('browseLibraryBtn');
    const mainBook = document.getElementById('mainBook');
    const libraryCollection = document.getElementById('libraryCollection');

    if (openBookBtn && mainBook) {
        openBookBtn.addEventListener('click', function (e) {
            e.preventDefault();
            mainBook.classList.add('book-opened');
        });
    }

    if (closeBookBtn && mainBook) {
        closeBookBtn.addEventListener('click', function (e) {
            e.preventDefault();
            mainBook.classList.remove('book-opened');
        });
    }

    if (browseLibraryBtn && libraryCollection) {
        browseLibraryBtn.addEventListener('click', function (e) {
            e.preventDefault();
            libraryCollection.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // 2. Dropdown Menus Management
    const userMenuDropdown = document.getElementById('userMenuDropdown');
    if (userMenuDropdown) {
        document.addEventListener('click', function (e) {
            if (!userMenuDropdown.contains(e.target)) {
                userMenuDropdown.classList.remove('open');
            }
        });
    }

    // 3. Auto-Dismiss Flash Toasts
    const toastItems = document.querySelectorAll('.mv-toast');
    if (toastItems.length > 0) {
        setTimeout(() => {
            toastItems.forEach(toast => {
                toast.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(60px)';
                setTimeout(() => toast.remove(), 600);
            });
        }, 6500);
    }
});

// 4. Google OAuth Response Receiver
window.handleGoogleCredentialResponse = function (response) {
    if (!response || !response.credential) {
        console.warn("Google authentication token empty.");
        return;
    }

    fetch('/auth/google', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({ credential: response.credential })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success && data.redirect) {
            window.location.href = data.redirect;
        } else {
            alert(data.message || 'Authentication could not be verified.');
        }
    })
    .catch(err => {
        console.error('Google Auth Error:', err);
    });
};
