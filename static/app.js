// Global app JavaScript functionality

// API Helper Functions
class SplitAppAPI {
    constructor() {
        this.baseURL = '/api';
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Expense endpoints
    async getExpenses() {
        return this.request('/expenses');
    }

    async createExpense(expenseData) {
        return this.request('/expenses', {
            method: 'POST',
            body: JSON.stringify(expenseData),
        });
    }

    async updateExpense(id, expenseData) {
        return this.request(`/expenses/${id}`, {
            method: 'PUT',
            body: JSON.stringify(expenseData),
        });
    }

    async deleteExpense(id) {
        return this.request(`/expenses/${id}`, {
            method: 'DELETE',
        });
    }

    // People and settlements
    async getPeople() {
        return this.request('/people');
    }

    async getBalances() {
        return this.request('/balances');
    }

    async getSettlements() {
        return this.request('/settlements');
    }

    async healthCheck() {
        return this.request('/health');
    }
}

// Global instance
const api = new SplitAppAPI();

// Utility Functions
const Utils = {
    // Format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(amount);
    },

    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    },

    // Show toast notification
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    },

    // Validate expense form data
    validateExpenseData(data) {
        const errors = [];

        if (!data.amount || data.amount <= 0) {
            errors.push('Amount must be greater than 0');
        }

        if (!data.description || data.description.trim() === '') {
            errors.push('Description is required');
        }

        if (!data.paid_by || data.paid_by.trim() === '') {
            errors.push('Paid by is required');
        }

        return errors;
    },

    // Debounce function for search/input
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
};

// Form handling
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-dismissible)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 500);
        }, 5000);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                
                // Re-enable button after 3 seconds to prevent permanent disability
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || 'Submit';
                }, 3000);
            }
        });
    });

    // Store original button text
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(btn => {
        btn.setAttribute('data-original-text', btn.innerHTML);
    });

    // Enhanced number input formatting
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !isNaN(this.value)) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });

    // Auto-complete for person names
    const personInputs = document.querySelectorAll('input[list="peopleList"]');
    personInputs.forEach(input => {
        input.addEventListener('input', Utils.debounce(async function() {
            // Could fetch updated people list here
            // For now, we rely on server-side datalist
        }, 300));
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + E for expenses page
    if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        window.location.href = '/expenses';
    }
    
    // Ctrl/Cmd + S for settlements page
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        window.location.href = '/settlements';
    }
    
    // Ctrl/Cmd + H for home/dashboard
    if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
        e.preventDefault();
        window.location.href = '/';
    }
});

// Service Worker for offline functionality (basic)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Register service worker for caching (optional enhancement)
        // navigator.serviceWorker.register('/sw.js');
    });
}

// Export for use in other scripts
window.SplitApp = {
    api,
    Utils,
};

// Add tooltips to all elements with title attribute
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Real-time updates (basic polling for demo purposes)
let updateInterval;

function startRealTimeUpdates() {
    // Only on settlements page, poll for updates every 30 seconds
    if (window.location.pathname === '/settlements') {
        updateInterval = setInterval(async () => {
            try {
                const balances = await api.getBalances();
                const settlements = await api.getSettlements();
                // Could update page content here without full reload
                // For simplicity, we'll just refresh if significant changes detected
            } catch (error) {
                console.log('Update check failed:', error);
            }
        }, 30000);
    }
}

function stopRealTimeUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// Start/stop updates based on page visibility
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        stopRealTimeUpdates();
    } else {
        startRealTimeUpdates();
    }
});

// Initialize real-time updates
document.addEventListener('DOMContentLoaded', startRealTimeUpdates);
