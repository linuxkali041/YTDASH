/**
 * Admin Theme Manager
 * Handles theme persistence and toggling for admin pages
 */
const AdminTheme = {
    init() {
        this.applySavedTheme();
        this.setupListeners();
    },

    applySavedTheme() {
        try {
            const savedSettings = localStorage.getItem('ytdl_settings');
            if (savedSettings) {
                const settings = JSON.parse(savedSettings);
                if (settings.theme) {
                    this.setTheme(settings.theme);
                }
            }
        } catch (e) {
            console.error('Error loading theme:', e);
        }
    },

    setTheme(theme) {
        // Apply to document
        document.documentElement.setAttribute('data-theme', theme);

        // Update active state of buttons
        document.querySelectorAll('.theme-option').forEach(btn => {
            if (btn.dataset.theme === theme) {
                btn.classList.add('active');
                btn.style.borderColor = 'var(--primary)';
                btn.style.color = 'var(--primary)';
            } else {
                btn.classList.remove('active');
                btn.style.borderColor = 'var(--border-color)';
                btn.style.color = 'var(--text-secondary)';
            }
        });
    },

    saveTheme(theme) {
        try {
            let settings = {};
            const savedSettings = localStorage.getItem('ytdl_settings');
            if (savedSettings) {
                settings = JSON.parse(savedSettings);
            }
            settings.theme = theme;
            localStorage.setItem('ytdl_settings', JSON.stringify(settings));
        } catch (e) {
            console.error('Error saving theme:', e);
        }
    },

    setupListeners() {
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const theme = btn.dataset.theme;
                this.setTheme(theme);
                this.saveTheme(theme);
            });
        });
    }
};

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AdminTheme.init());
} else {
    AdminTheme.init();
}
