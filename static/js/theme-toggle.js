document.addEventListener('DOMContentLoaded', function() {
    // Check for theme toggle button
    const themeToggleBtn = document.getElementById('theme-toggle');

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            // Send AJAX request to toggle theme
            fetch('/toggle-theme/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the button text and icon based on the new theme
                    if (data.theme === 'dark') {
                        themeToggleBtn.innerHTML = '<i class="fas fa-sun me-1"></i> Light Mode';
                    } else {
                        themeToggleBtn.innerHTML = '<i class="fas fa-moon me-1"></i> Dark Mode';
                    }

                    // Reload page to apply new theme
                    window.location.reload();
                } else {
                    console.error('Theme toggle failed:', data.error);
                }
            })
            .catch(error => {
                console.error('Error toggling theme:', error);
            });
        });
    }
});

// Helper function to get cookies (for CSRF token)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
