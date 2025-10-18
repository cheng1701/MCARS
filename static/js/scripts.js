// Main JavaScript for Membership Portal

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })

    // Handle membership type selection on registration form
    var membershipTypeSelect = document.getElementById('id_membership_type');
    if (membershipTypeSelect) {
        membershipTypeSelect.addEventListener('change', function() {
            updateMembershipDetails(this.value);
        });
        // Initialize with current value
        if (membershipTypeSelect.value) {
            updateMembershipDetails(membershipTypeSelect.value);
        }
    }

    // Handle family membership check on dashboard
    checkFamilyMembership();
});

// Update membership details on registration form
function updateMembershipDetails(membershipTypeId) {
    // This would typically fetch membership details via AJAX
    // For demonstration purposes, we'll simulate it
    console.log('Selected membership type ID:', membershipTypeId);
    // You could update price, duration, and other details based on selection
}

// Check if user has family membership and show/hide family sections
function checkFamilyMembership() {
    var familySection = document.getElementById('familySection');
    var membershipType = document.getElementById('membershipType');

    if (familySection && membershipType) {
        var isFamily = membershipType.dataset.isFamily === 'True';
        familySection.style.display = isFamily ? 'block' : 'none';
    }
}

// Add child form validation
function validateChildForm() {
    var firstName = document.getElementById('id_first_name').value;
    var lastName = document.getElementById('id_last_name').value;

    if (!firstName || !lastName) {
        alert('Please provide both first and last name for the child.');
        return false;
    }
    return true;
}

// Handle approval confirmation
function confirmApproval(memberId, memberName) {
    return confirm('Are you sure you want to approve the membership application for ' + memberName + '?');
}

// Handle rejection confirmation
function confirmRejection(memberId, memberName) {
    return confirm('Are you sure you want to reject the membership application for ' + memberName + '?');
}

// Payment form validation
function validatePaymentForm() {
    var cardNumber = document.getElementById('cardNumber').value;
    var cardName = document.getElementById('cardName').value;
    var expiryDate = document.getElementById('expiryDate').value;
    var cvv = document.getElementById('cvv').value;

    if (!cardNumber || !cardName || !expiryDate || !cvv) {
        alert('Please fill in all payment details.');
        return false;
    }

    // Basic validation - would be more robust in production
    if (cardNumber.replace(/\s/g, '').length !== 16) {
        alert('Please enter a valid 16-digit card number.');
        return false;
    }

    if (cvv.length < 3) {
        alert('Please enter a valid CVV code.');
        return false;
    }

    return true;
}
