// Mobile menu toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navbarLinks = document.querySelector('.navbar-links');
    
    if (mobileMenuToggle && navbarLinks) {
        mobileMenuToggle.addEventListener('click', function() {
            navbarLinks.classList.toggle('active');
        });
    }
    
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const requiredInputs = form.querySelectorAll('[required]');
        
        form.addEventListener('submit', function(e) {
            let valid = true;
            
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    
                    // Add error styling
                    input.classList.add('is-invalid');
                    
                    // Create error message if it doesn't exist
                    let errorMsg = input.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                        errorMsg = document.createElement('div');
                        errorMsg.classList.add('error-message');
                        errorMsg.style.color = 'var(--color-error)';
                        errorMsg.style.fontSize = '0.875rem';
                        errorMsg.style.marginTop = '4px';
                        input.parentNode.insertBefore(errorMsg, input.nextSibling);
                    }
                    
                    errorMsg.textContent = 'This field is required';
                }
            });
            
            if (!valid) {
                e.preventDefault();
            }
        });
        
        // Clear error styling on input
        requiredInputs.forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');
                const errorMsg = this.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('error-message')) {
                    errorMsg.textContent = '';
                }
            });
        });
    });
    
    // Dynamic form fields for alternatives page
    const alternativeForm = document.getElementById('alternative-form');
    if (alternativeForm) {
        // Format numeric inputs to maintain decimal precision
        const numericInputs = document.querySelectorAll('input[type="number"]');
        numericInputs.forEach(input => {
            input.addEventListener('change', function() {
                const value = parseFloat(this.value);
                if (!isNaN(value)) {
                    this.value = value.toFixed(2);
                }
            });
        });
    }
    
    // Analysis page enhancements
    const analysisForm = document.getElementById('analysis-form');
    if (analysisForm) {
        // Validate that total weights sum to 100%
        const weightInputs = document.querySelectorAll('input[name^="weight_"]');
        const totalWeightDisplay = document.getElementById('total-weight');
        
        function updateTotalWeight() {
            let total = 0;
            weightInputs.forEach(input => {
                const value = parseFloat(input.value) || 0;
                total += value;
            });
            
            if (totalWeightDisplay) {
                totalWeightDisplay.textContent = total.toFixed(2);
                
                // Visual feedback on weight total
                if (Math.abs(total - 1) < 0.01) { // Allow small rounding errors
                    totalWeightDisplay.style.color = 'var(--color-success)';
                } else {
                    totalWeightDisplay.style.color = 'var(--color-error)';
                }
            }
        }
        
        if (weightInputs.length > 0) {
            weightInputs.forEach(input => {
                input.addEventListener('input', updateTotalWeight);
            });
            
            // Initialize
            updateTotalWeight();
        }
    }
    
    // Result visualization enhancements
    const resultCharts = document.querySelectorAll('.result-chart');
    if (resultCharts.length > 0) {
        resultCharts.forEach(chart => {
            // Add hover effects to chart bars
            const bars = chart.querySelectorAll('.chart-bar');
            bars.forEach(bar => {
                bar.addEventListener('mouseenter', function() {
                    this.style.opacity = '0.8';
                    this.style.transform = 'scaleY(1.05)';
                });
                
                bar.addEventListener('mouseleave', function() {
                    this.style.opacity = '1';
                    this.style.transform = 'scaleY(1)';
                });
            });
        });
    }
});

// Function to toggle between different views in the analysis details
function toggleAnalysisView(viewId) {
    const views = document.querySelectorAll('.analysis-view');
    views.forEach(view => {
        view.style.display = 'none';
    });
    
    const selectedView = document.getElementById(viewId);
    if (selectedView) {
        selectedView.style.display = 'block';
    }
    
    // Update active tab
    const tabs = document.querySelectorAll('.view-tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });
    
    const activeTab = document.querySelector(`[data-view="${viewId}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
}