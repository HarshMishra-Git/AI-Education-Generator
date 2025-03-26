// Main JavaScript for TAPBuddy AI Video Generator

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Phone number formatting
    const phoneInput = document.getElementById('phone_number');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            // Keep + and numbers only
            let input = e.target.value.replace(/[^\d+]/g, '');
            
            // Ensure it starts with +
            if (!input.startsWith('+') && input.length > 0) {
                input = '+' + input;
            }
            
            e.target.value = input;
        });
    }
    
    // Subject selection effects
    const subjectSelect = document.getElementById('subject');
    if (subjectSelect) {
        subjectSelect.addEventListener('change', function() {
            // Could add dynamic topic suggestions based on subject
            const topicInput = document.getElementById('topic');
            const selectedSubject = this.value;
            
            if (selectedSubject === 'Visual Arts') {
                topicInput.placeholder = 'e.g., Watercolor Painting, Color Theory';
            } else if (selectedSubject === 'Performing Arts') {
                topicInput.placeholder = 'e.g., Piano Basics, Dance Choreography';
            } else if (selectedSubject === 'Coding') {
                topicInput.placeholder = 'e.g., Python Functions, HTML Basics';
            } else if (selectedSubject === 'Financial Literacy') {
                topicInput.placeholder = 'e.g., Budgeting, Investing Basics';
            } else if (selectedSubject === 'Science') {
                topicInput.placeholder = 'e.g., Photosynthesis, States of Matter';
            } else {
                topicInput.placeholder = 'e.g., Your specific topic';
            }
        });
    }
    
    // Video request status updates
    function updateRequestStatuses() {
        const statusElements = document.querySelectorAll('.status-pending, .status-processing');
        
        if (statusElements.length > 0) {
            // In a real implementation, this would make AJAX calls to check statuses
            console.log('Checking status updates for', statusElements.length, 'requests');
        }
    }
    
    // Check for updates every 10 seconds if there are pending requests
    const hasPendingRequests = document.querySelectorAll('.status-pending, .status-processing').length > 0;
    if (hasPendingRequests) {
        setInterval(updateRequestStatuses, 10000);
    }
});
