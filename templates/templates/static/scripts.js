document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggleTheme');
  const body = document.body;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const savedTheme = localStorage.getItem('theme');

  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    body.classList.add('dark-mode');
    if (toggleBtn) {
      toggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i> Modo claro';
    }
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      body.classList.toggle('dark-mode');
      const isDark = body.classList.contains('dark-mode');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      toggleBtn.innerHTML = isDark
        ? '<i class="fa-solid fa-sun"></i> Modo claro'
        : '<i class="fa-solid fa-moon"></i> Modo oscuro';
    });
  }
});

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    document.querySelectorAll('.auto-dismiss').forEach(alert => {
      alert.classList.add('animate__fadeOutUp');
      setTimeout(() => alert.remove(), 1000);
    });
  }, 4000);
});

document.addEventListener('DOMContentLoaded', () => {
  const toasts = document.querySelectorAll('.toast');
  toasts.forEach(toast => {
    setTimeout(() => {
      toast.classList.add('animate__fadeOutUp');
      setTimeout(() => toast.remove(), 1000);
    }, 4000);
  });
});