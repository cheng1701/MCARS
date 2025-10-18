document.addEventListener('DOMContentLoaded', function () {
  const guestBtn = document.getElementById('guest-theme-toggle');
  const themeLink = document.getElementById('theme-css');

  // Only run for anonymous layout where guest toggle exists
  if (!guestBtn || !themeLink) return;

  const LIGHT_HREF = themeLink.getAttribute('href').includes('light-theme.css')
    ? themeLink.getAttribute('href')
    : themeLink.getAttribute('href').replace('dark-theme.css', 'light-theme.css');
  const DARK_HREF = themeLink.getAttribute('href').includes('dark-theme.css')
    ? themeLink.getAttribute('href')
    : themeLink.getAttribute('href').replace('light-theme.css', 'dark-theme.css');

  function applyTheme(theme) {
    if (theme === 'light') {
      if (!themeLink.getAttribute('href').includes('light-theme.css')) {
        themeLink.setAttribute('href', LIGHT_HREF);
      }
      guestBtn.innerHTML = '<i class="fas fa-moon me-1"></i> Dark Mode';
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      if (!themeLink.getAttribute('href').includes('dark-theme.css')) {
        themeLink.setAttribute('href', DARK_HREF);
      }
      guestBtn.innerHTML = '<i class="fas fa-sun me-1"></i> Light Mode';
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }

  // Initialize from localStorage; fallback to server-provided (derived from request.theme)
  const stored = (localStorage.getItem('siteTheme') || '').toLowerCase();
  if (stored === 'light' || stored === 'dark') {
    applyTheme(stored);
  } else {
    // Infer initial from current href
    const initial = themeLink.getAttribute('href').includes('light-theme.css') ? 'light' : 'dark';
    applyTheme(initial);
  }

  guestBtn.addEventListener('click', function () {
    const isLight = themeLink.getAttribute('href').includes('light-theme.css');
    const next = isLight ? 'dark' : 'light';
    localStorage.setItem('siteTheme', next);
    applyTheme(next);
  });
});
