// Main JavaScript file for Admission Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize file upload handling
    initializeFileUpload();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form submission handling
    initializeFormSubmission();
});

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateEmail(this);
        });
    });
    
    // Phone validation
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validatePhone(this);
        });
    });
    
    // Date validation (must be in the past for DOB)
    const dobInput = document.getElementById('dob');
    if (dobInput) {
        dobInput.addEventListener('change', function() {
            validateDateOfBirth(this);
        });
    }
}

// File upload handling
function initializeFileUpload() {
    const fileInput = document.getElementById('documents');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            validateFileUpload(this);
        });
    }
}

// Tooltips initialization
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Form submission with loading
function initializeFormSubmission() {
    const applicationForm = document.getElementById('applicationForm');
    if (applicationForm) {
        applicationForm.addEventListener('submit', function() {
            showLoadingModal();
        });
    }
}

// Validation functions
function validateEmail(input) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(input.value);
    
    if (!isValid && input.value !== '') {
        input.setCustomValidity('Please enter a valid email address');
        showValidationError(input, 'Please enter a valid email address');
    } else {
        input.setCustomValidity('');
        clearValidationError(input);
    }
}

function validatePhone(input) {
    const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
    const isValid = phoneRegex.test(input.value);
    
    if (!isValid && input.value !== '') {
        input.setCustomValidity('Please enter a valid phone number');
        showValidationError(input, 'Please enter a valid phone number (minimum 10 digits)');
    } else {
        input.setCustomValidity('');
        clearValidationError(input);
    }
}

function validateDateOfBirth(input) {
    const selectedDate = new Date(input.value);
    const today = new Date();
    const age = today.getFullYear() - selectedDate.getFullYear();
    
    if (selectedDate >= today) {
        input.setCustomValidity('Date of birth must be in the past');
        showValidationError(input, 'Date of birth must be in the past');
    } else if (age < 15) {
        input.setCustomValidity('Minimum age requirement is 15 years');
        showValidationError(input, 'Minimum age requirement is 15 years');
    } else if (age > 100) {
        input.setCustomValidity('Please enter a valid date of birth');
        showValidationError(input, 'Please enter a valid date of birth');
    } else {
        input.setCustomValidity('');
        clearValidationError(input);
    }
}

function validateFileUpload(input) {
    const file = input.files[0];
    const maxSize = 5 * 1024 * 1024; // 5MB
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    
    if (file) {
        if (file.size > maxSize) {
            input.setCustomValidity('File size must be less than 5MB');
            showValidationError(input, 'File size must be less than 5MB');
            input.value = '';
        } else if (!allowedTypes.includes(file.type)) {
            input.setCustomValidity('Only PDF, JPG, PNG, and GIF files are allowed');
            showValidationError(input, 'Only PDF, JPG, PNG, and GIF files are allowed');
            input.value = '';
        } else {
            input.setCustomValidity('');
            clearValidationError(input);
            showFileInfo(input, file);
        }
    }
}

// Helper functions for validation feedback
function showValidationError(input, message) {
    clearValidationError(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;
    
    input.classList.add('is-invalid');
    input.parentNode.appendChild(errorDiv);
}

function clearValidationError(input) {
    input.classList.remove('is-invalid');
    const existingError = input.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

function showFileInfo(input, file) {
    clearFileInfo(input);
    
    const infoDiv = document.createElement('div');
    infoDiv.className = 'form-text text-success';
    infoDiv.innerHTML = `<i class="fas fa-check-circle me-1"></i>File selected: ${file.name} (${formatFileSize(file.size)})`;
    
    input.parentNode.appendChild(infoDiv);
}

function clearFileInfo(input) {
    const existingInfo = input.parentNode.querySelector('.form-text.text-success');
    if (existingInfo) {
        existingInfo.remove();
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Modal functions
function showLoadingModal() {
    const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
    modal.show();
}

// Admin functions
function viewApplication(id, appId, name, dob, gender, email, phone, address, course, prevEdu, docs, status, notes, docStatus, docNotes) {
    const modalBody = document.getElementById('applicationDetails');
    const modalApplicationId = document.getElementById('modalApplicationId');
    const modalStatus = document.getElementById('modalStatus');
    
    modalApplicationId.value = appId;
    modalStatus.value = status;
    
    const docStatusBadge = docStatus === 'Pending' ? 'warning' : docStatus === 'Verified' ? 'success' : 'danger';
    
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-6 mb-3">
                <strong>Application ID:</strong><br>
                <code>${appId}</code>
            </div>
            <div class="col-md-6 mb-3">
                <strong>Current Status:</strong><br>
                <span class="badge bg-${status === 'Pending' ? 'warning' : status === 'Accepted' ? 'success' : 'danger'}">${status}</span>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6 mb-3">
                <strong>Full Name:</strong><br>
                ${name}
            </div>
            <div class="col-md-6 mb-3">
                <strong>Date of Birth:</strong><br>
                ${dob}
            </div>
        </div>
        <div class="row">
            <div class="col-md-6 mb-3">
                <strong>Gender:</strong><br>
                ${gender}
            </div>
            <div class="col-md-6 mb-3">
                <strong>Course:</strong><br>
                ${course}
            </div>
        </div>
        <div class="row">
            <div class="col-md-6 mb-3">
                <strong>Email:</strong><br>
                ${email}
            </div>
            <div class="col-md-6 mb-3">
                <strong>Phone:</strong><br>
                ${phone}
            </div>
        </div>
        <div class="mb-3">
            <strong>Address:</strong><br>
            ${address}
        </div>
        <div class="mb-3">
            <strong>Previous Education:</strong><br>
            ${prevEdu}
        </div>
        ${docs ? `
        <div class="mb-3">
            <strong>Documents:</strong>
            <span class="badge bg-${docStatusBadge} ms-2">${docStatus || 'Pending'}</span>
            <br>
            <span class="text-success"><i class="fas fa-file me-1"></i>${docs}</span>
            <div class="mt-2">
                <button class="btn btn-sm btn-success me-2" onclick="verifyDocument('${appId}', 'Verified')">
                    <i class="fas fa-check me-1"></i>Verify
                </button>
                <button class="btn btn-sm btn-danger" onclick="verifyDocument('${appId}', 'Rejected')">
                    <i class="fas fa-times me-1"></i>Reject
                </button>
            </div>
        </div>` : '<div class="mb-3"><span class="text-muted">No documents uploaded</span></div>'}
        ${docNotes ? `<div class="mb-3"><strong>Document Notes:</strong><br><div class="alert alert-warning">${docNotes}</div></div>` : ''}
        ${notes ? `<div class="mb-3"><strong>Admin Notes:</strong><br><div class="alert alert-info">${notes}</div></div>` : ''}
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('applicationModal'));
    modal.show();
}

function verifyDocument(appId, status) {
    const notes = prompt(`Enter notes for document ${status.toLowerCase()}:`);
    if (notes !== null) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/admin/verify_document';
        
        const appIdInput = document.createElement('input');
        appIdInput.type = 'hidden';
        appIdInput.name = 'application_id';
        appIdInput.value = appId;
        
        const statusInput = document.createElement('input');
        statusInput.type = 'hidden';
        statusInput.name = 'document_status';
        statusInput.value = status;
        
        const notesInput = document.createElement('input');
        notesInput.type = 'hidden';
        notesInput.name = 'document_notes';
        notesInput.value = notes;
        
        form.appendChild(appIdInput);
        form.appendChild(statusInput);
        form.appendChild(notesInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Search functionality enhancement
function initializeSearch() {
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                // Auto-submit form after 500ms of no typing
                if (this.value.length >= 3 || this.value.length === 0) {
                    this.form.submit();
                }
            }, 500);
        });
    }
}

// Application ID formatter
function formatApplicationId(input) {
    let value = input.value.replace(/[^A-Z0-9]/g, '').toUpperCase();
    input.value = value;
}

// Initialize search on admin pages
if (window.location.pathname.includes('admin')) {
    document.addEventListener('DOMContentLoaded', initializeSearch);
}

// Bulk selection functionality
document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const applicationCheckboxes = document.querySelectorAll('.application-checkbox');
    const bulkApplyBtn = document.getElementById('bulkApplyBtn');
    const bulkActionForm = document.getElementById('bulkActionForm');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            applicationCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkButton();
        });
    }
    
    if (applicationCheckboxes.length > 0) {
        applicationCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const allChecked = Array.from(applicationCheckboxes).every(cb => cb.checked);
                const someChecked = Array.from(applicationCheckboxes).some(cb => cb.checked);
                
                if (selectAllCheckbox) {
                    selectAllCheckbox.checked = allChecked;
                    selectAllCheckbox.indeterminate = someChecked && !allChecked;
                }
                updateBulkButton();
            });
        });
    }
    
    function updateBulkButton() {
        const checkedCount = document.querySelectorAll('.application-checkbox:checked').length;
        if (bulkApplyBtn) {
            bulkApplyBtn.disabled = checkedCount === 0;
            bulkApplyBtn.innerHTML = checkedCount > 0 
                ? `<i class="fas fa-check me-2"></i>Apply (${checkedCount})`
                : `<i class="fas fa-check me-2"></i>Apply`;
        }
    }
    
    if (bulkActionForm) {
        bulkActionForm.addEventListener('submit', function(e) {
            const checkedCount = document.querySelectorAll('.application-checkbox:checked').length;
            if (checkedCount === 0) {
                e.preventDefault();
                alert('Please select at least one application');
                return false;
            }
            
            const bulkStatus = document.getElementById('bulkStatus').value;
            if (!bulkStatus) {
                e.preventDefault();
                alert('Please select an action');
                return false;
            }
            
            if (!confirm(`Are you sure you want to update ${checkedCount} application(s)?`)) {
                e.preventDefault();
                return false;
            }
        });
    }
});

// Auto-dismiss alerts
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Prevent form double submission
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                setTimeout(() => {
                    submitBtn.disabled = false;
                }, 3000);
            }
        });
    });
});
