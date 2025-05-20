// Rootly main.js - Core JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Handle flash message dismissal
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        // Add a close button to each flash message
        const closeButton = document.createElement('button');
        closeButton.className = 'btn-close float-end';
        closeButton.setAttribute('aria-label', 'Close');
        closeButton.addEventListener('click', function() {
            message.style.display = 'none';
        });
        message.appendChild(closeButton);
        
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.style.display = 'none';
            }, 500);
        }, 5000);
    });
    
    // File upload preview for identify page
    const fileInput = document.getElementById('plant_image');
    const previewContainer = document.getElementById('image-preview-container');
    
    if (fileInput && previewContainer) {
        fileInput.addEventListener('change', function() {
            previewContainer.innerHTML = '';
            
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    const preview = document.createElement('div');
                    preview.className = 'mt-3';
                    preview.innerHTML = `
                        <h6>Preview:</h6>
                        <img src="${e.target.result}" class="img-fluid rounded" style="max-height: 300px;" alt="Image preview">
                    `;
                    previewContainer.appendChild(preview);
                }
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
    
    // Tooltips initialization (for Bootstrap tooltips)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Form validation for required fields
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
            
            // Create or update validation message
            let feedbackDiv = field.nextElementSibling;
            if (!feedbackDiv || !feedbackDiv.classList.contains('invalid-feedback')) {
                feedbackDiv = document.createElement('div');
                feedbackDiv.className = 'invalid-feedback';
                field.parentNode.insertBefore(feedbackDiv, field.nextSibling);
            }
            feedbackDiv.textContent = 'This field is required.';
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}
