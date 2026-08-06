/**
 * ExpenseFlow - Enhanced UI/UX JavaScript
 * Handles form validation, loading states, and interactive features
 */

// ==========================================
// FORM VALIDATION
// ==========================================

/**
 * Validate form inputs with real-time feedback
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            // Real-time validation on blur
            input.addEventListener('blur', function() {
                validateInput(this);
            });
            
            // Clear errors on input
            input.addEventListener('input', function() {
                clearInputError(this);
            });
        });
        
        // Form submission validation
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            inputs.forEach(input => {
                if (!validateInput(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showFormError('Please fill in all required fields correctly.');
            } else {
                // Show loading state
                showLoadingState(form);
            }
        });
    });
}

/**
 * Validate a single input field
 */
function validateInput(input) {
    const formGroup = input.closest('.form-group');
    const value = input.value.trim();
    
    // Clear previous errors
    clearInputError(input);
    
    // Check if empty
    if (input.hasAttribute('required') && !value) {
        showInputError(input, 'This field is required');
        return false;
    }
    
    // Email validation
    if (input.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showInputError(input, 'Please enter a valid email address');
            return false;
        }
    }
    
    // Number validation
    if (input.type === 'number' && value) {
        if (isNaN(value) || parseFloat(value) <= 0) {
            showInputError(input, 'Please enter a valid positive number');
            return false;
        }
    }
    
    // Password strength
    if (input.type === 'password' && input.name === 'password' && value) {
        if (value.length < 6) {
            showInputError(input, 'Password must be at least 6 characters');
            return false;
        }
    }
    
    // Success state
    showInputSuccess(input);
    return true;
}

/**
 * Show input error
 */
function showInputError(input, message) {
    const formGroup = input.closest('.form-group');
    input.classList.add('error');
    input.classList.remove('success');
    formGroup.classList.add('has-error');
    
    // Add error message if not exists
    let errorMsg = formGroup.querySelector('.error-message');
    if (!errorMsg) {
        errorMsg = document.createElement('div');
        errorMsg.className = 'error-message';
        errorMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        input.parentNode.appendChild(errorMsg);
    } else {
        errorMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    }
}

/**
 * Show input success
 */
function showInputSuccess(input) {
    input.classList.remove('error');
    input.classList.add('success');
    const formGroup = input.closest('.form-group');
    formGroup.classList.remove('has-error');
}

/**
 * Clear input error
 */
function clearInputError(input) {
    input.classList.remove('error', 'success');
    const formGroup = input.closest('.form-group');
    formGroup.classList.remove('has-error');
    
    const errorMsg = formGroup.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.remove();
    }
}

/**
 * Show form-level error
 */
function showFormError(message) {
    const flashContainer = document.querySelector('.flash-container') || createFlashContainer();
    const flash = document.createElement('div');
    flash.className = 'flash-message danger fade-in';
    flash.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        ${message}
        <button class="flash-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    flashContainer.insertBefore(flash, flashContainer.firstChild);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        flash.style.opacity = '0';
        setTimeout(() => flash.remove(), 300);
    }, 5000);
}

/**
 * Create flash container if not exists
 */
function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-container';
    container.setAttribute('role', 'alert');
    container.setAttribute('aria-live', 'polite');
    const content = document.querySelector('.dashboard-content') || document.querySelector('.form-container');
    if (content) {
        content.insertBefore(container, content.firstChild);
    }
    return container;
}

// ==========================================
// LOADING STATES
// ==========================================

/**
 * Show loading state for forms
 */
function showLoadingState(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        
        // Store original text
        if (!submitBtn.dataset.originalText) {
            submitBtn.dataset.originalText = submitBtn.innerHTML;
        }
        
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    }
}

/**
 * Hide loading state
 */
function hideLoadingState(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn && submitBtn.dataset.originalText) {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        submitBtn.innerHTML = submitBtn.dataset.originalText;
    }
}

/**
 * Show page loading overlay
 */
function showLoadingOverlay(message = 'Loading...') {
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div style="text-align: center; color: white;">
                <div class="loading-spinner"></div>
                <p style="margin-top: 20px; font-size: 16px;">${message}</p>
            </div>
        `;
        document.body.appendChild(overlay);
    }
}

/**
 * Hide page loading overlay
 */
function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// ==========================================
// MOBILE NAVIGATION
// ==========================================

/**
 * Initialize mobile navigation
 */
function initMobileNav() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobileOverlay');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    // Mobile menu button
    if (mobileMenuBtn && sidebar && overlay) {
        mobileMenuBtn.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.toggle('mobile-open');
            overlay.classList.toggle('active');
            this.setAttribute('aria-expanded', sidebar.classList.contains('mobile-open'));
        });
    }
    
    // Sidebar toggle for desktop
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            this.setAttribute('aria-expanded', !sidebar.classList.contains('collapsed'));
        });
    }
    
    // Close on overlay click
    if (overlay && sidebar) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
            if (mobileMenuBtn) {
                mobileMenuBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }
    
    // Auto-hide mobile menu when clicking links
    if (sidebar) {
        const menuLinks = sidebar.querySelectorAll('.menu-link');
        menuLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('mobile-open');
                    if (overlay) overlay.classList.remove('active');
                    if (mobileMenuBtn) mobileMenuBtn.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }
}

// ==========================================
// FLASH MESSAGES
// ==========================================

/**
 * Initialize flash message auto-hide
 */
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(flash => {
        // Add close button functionality
        const closeBtn = flash.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                flash.style.opacity = '0';
                setTimeout(() => flash.remove(), 300);
            });
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });
}

// ==========================================
// ANIMATIONS
// ==========================================

/**
 * Initialize scroll animations
 */
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    // Observe cards and stat elements
    document.querySelectorAll('.stat-card-modern, .content-card, .approval-item').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Show success toast
 */
function showSuccessToast(message) {
    showToast(message, 'success');
}

/**
 * Show error toast
 */
function showErrorToast(message) {
    showToast(message, 'danger');
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const container = document.querySelector('.flash-container') || createFlashContainer();
    const toast = document.createElement('div');
    toast.className = `flash-message ${type} fade-in`;
    
    const icon = type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        ${message}
        <button class="flash-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// ==========================================
// INITIALIZE ON DOM LOAD
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all features
    initFormValidation();
    initMobileNav();
    initFlashMessages();
    initScrollAnimations();
    
    console.log('ExpenseFlow UI initialized successfully');
});

// ==========================================
// KEYBOARD NAVIGATION
// ==========================================

// ESC key to close modals and mobile menu
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        // Close mobile menu
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('mobileOverlay');
        if (sidebar && sidebar.classList.contains('mobile-open')) {
            sidebar.classList.remove('mobile-open');
            if (overlay) overlay.classList.remove('active');
        }
        
        // Close modals
        const modals = document.querySelectorAll('.modal.active');
        modals.forEach(modal => modal.classList.remove('active'));
    }
});
