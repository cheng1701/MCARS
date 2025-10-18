document.addEventListener('DOMContentLoaded', function() {
    // Calculate profile completion percentage
    function calculateCompletion() {
        const form = document.getElementById('profileForm');
        if (!form) return;

        // Required fields
        const requiredFields = [
            'id_first_name',
            'id_last_name',
            'id_email',
            'id_phone_number',
            'id_street',
            'id_city',
            'id_state',
            'id_zip_code'
        ];

        let filledFields = 0;

        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field && field.value && field.value.trim() !== '') {
                filledFields++;
            }
        });

        const percentage = Math.round((filledFields / requiredFields.length) * 100);

        // Update progress bar
        const progressBar = document.getElementById('profileProgress');
        if (progressBar) {
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);

            // Add color based on completion percentage
            progressBar.classList.remove('bg-danger', 'bg-warning', 'bg-info', 'bg-success');

            if (percentage < 25) {
                progressBar.classList.add('bg-danger');
            } else if (percentage < 50) {
                progressBar.classList.add('bg-warning');
            } else if (percentage < 75) {
                progressBar.classList.add('bg-info');
            } else {
                progressBar.classList.add('bg-success');
            }
        }

        return percentage;
    }

    // Initial calculation
    calculateCompletion();

    // Listen for input changes to update progress bar
    const form = document.getElementById('profileForm');
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('change', calculateCompletion);
            input.addEventListener('keyup', calculateCompletion);
        });
    }
});
