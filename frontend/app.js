/**
 * Zava AI Portal - Expense Tracking Frontend
 * Connects to FastAPI backend for AI-powered expense classification
 */

// Detect if running on Azure or locally
const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api/v1'
    : '/api/v1';  // Use relative path on Azure

// DOM Elements
let expenseForm;
let expenseList;
let summaryElements;
let statusMessage;

/**
 * Initialize the application on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements
    expenseForm = document.getElementById('expense-form');
    expenseList = document.getElementById('expense-list');
    summaryElements = {
        needs: document.getElementById('needs-total'),
        wants: document.getElementById('wants-total'),
        goals: document.getElementById('goals-total'),
        needsPercent: document.getElementById('needs-percent'),
        wantsPercent: document.getElementById('wants-percent'),
        goalsPercent: document.getElementById('goals-percent'),
        total: document.getElementById('total-amount')
    };
    statusMessage = document.getElementById('status-message');
    
    // Add form submit listener
    if (expenseForm) {
        expenseForm.addEventListener('submit', addExpense);
    }
    
    // Load initial data
    loadExpenses();
    loadSummary();
});

/**
 * Add a new expense with AI classification
 * @param {Event} event - Form submit event
 */
async function addExpense(event) {
    event.preventDefault();
    
    // Get form data
    const description = document.getElementById('description').value.trim();
    const amount = parseFloat(document.getElementById('amount').value);
    const currency = document.getElementById('currency').value || 'USD';
    const category = document.getElementById('category').value.trim();
    
    // Validate input
    if (!description || !amount || amount <= 0) {
        showMessage('Please enter a valid description and amount', 'error');
        return;
    }
    
    // Disable form during submission
    const submitButton = expenseForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = 'Classifying...';
    
    try {
        showMessage('Analyzing expense with AI...', 'info');
        
        // POST to backend
        const response = await fetch(`${API_BASE}/expenses/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description,
                amount,
                currency,
                category: category || null
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add expense');
        }
        
        const result = await response.json();
        
        // Show success message with AI classification
        showMessage(
            `✓ Expense classified as "${result.classification.toUpperCase()}" with ${Math.round(result.ai_confidence * 100)}% confidence. ${result.ai_reasoning}`,
            'success'
        );
        
        // Reset form
        expenseForm.reset();
        
        // Refresh data
        await Promise.all([loadExpenses(), loadSummary()]);
        
    } catch (error) {
        console.error('Error adding expense:', error);
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        // Re-enable form
        submitButton.disabled = false;
        submitButton.textContent = 'Add Expense';
    }
}

/**
 * Load and display expenses
 * @param {string} filter - Optional classification filter (needs/wants/goals)
 */
async function loadExpenses(filter = null) {
    if (!expenseList) return;

    try {
        // Build URL with optional filter
        let url = `${API_BASE}/expenses/?limit=100`;
        if (filter) {
            url += `&classification=${filter}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Failed to load expenses');
        }

        const data = await response.json();
        const expenses = data.expenses || [];

        // Render expenses
        if (expenses.length === 0) {
            expenseList.innerHTML = '<p class="empty-state">No expenses yet. Add your first expense above!</p>';
            return;
        }

        expenseList.innerHTML = expenses.map(expense => `
            <div class="expense-item" data-id="${expense.id}">
                <div class="expense-info">
                    <h3>${expense.description}</h3>
                    <p class="expense-amount">$${expense.amount.toFixed(2)} ${expense.currency}</p>
                </div>
                <div class="expense-meta">
                    <span class="classification-badge ${expense.classification}">
                        ${getClassificationIcon(expense.classification)} ${expense.classification.toUpperCase()}
                    </span>
                    <span class="confidence-score" title="AI Confidence Score">
                        ${(expense.ai_confidence * 100).toFixed(0)}% confidence
                    </span>
                </div>
                ${expense.ai_reasoning ? `<p class="expense-reasoning">${expense.ai_reasoning}</p>` : ''}
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading expenses:', error);
        expenseList.innerHTML = '<p class="error-state">Failed to load expenses. Please try again.</p>';
    }
}

/**
 * Load and display expense summary
 */
async function loadSummary() {
    if (!summaryElements.needs) return;
    
    try {
        const response = await fetch(`${API_BASE}/expenses/summary`);
        
        if (!response.ok) {
            throw new Error('Failed to load summary');
        }
        
        const summary = await response.json();
        
        // Update totals
        summaryElements.needs.textContent = `$${summary.needs.toFixed(2)}`;
        summaryElements.wants.textContent = `$${summary.wants.toFixed(2)}`;
        summaryElements.goals.textContent = `$${summary.goals.toFixed(2)}`;
        summaryElements.total.textContent = `$${summary.total.toFixed(2)}`;
        
        // Calculate and update percentages
        if (summary.total > 0) {
            const needsPercent = (summary.needs / summary.total) * 100;
            const wantsPercent = (summary.wants / summary.total) * 100;
            const goalsPercent = (summary.goals / summary.total) * 100;
            
            summaryElements.needsPercent.textContent = `${needsPercent.toFixed(1)}%`;
            summaryElements.wantsPercent.textContent = `${wantsPercent.toFixed(1)}%`;
            summaryElements.goalsPercent.textContent = `${goalsPercent.toFixed(1)}%`;
            
            // Update progress bars if they exist
            updateProgressBar('needs-progress', needsPercent);
            updateProgressBar('wants-progress', wantsPercent);
            updateProgressBar('goals-progress', goalsPercent);
        } else {
            summaryElements.needsPercent.textContent = '0%';
            summaryElements.wantsPercent.textContent = '0%';
            summaryElements.goalsPercent.textContent = '0%';
        }
        
    } catch (error) {
        console.error('Error loading summary:', error);
        // Set to zero on error
        if (summaryElements.needs) {
            summaryElements.needs.textContent = '$0.00';
            summaryElements.wants.textContent = '$0.00';
            summaryElements.goals.textContent = '$0.00';
            summaryElements.total.textContent = '$0.00';
        }
    }
}

/**
 * Update progress bar width
 * @param {string} id - Progress bar element ID
 * @param {number} percent - Percentage (0-100)
 */
function updateProgressBar(id, percent) {
    const progressBar = document.getElementById(id);
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
    }
}

/**
 * Show status message to user
 * @param {string} message - Message text
 * @param {string} type - Message type: 'success', 'error', 'info'
 */
function showMessage(message, type = 'info') {
    if (!statusMessage) {
        statusMessage = document.getElementById('status-message');
    }
    
    if (statusMessage) {
        statusMessage.textContent = message;
        statusMessage.className = `message ${type}`;
        statusMessage.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 5000);
    }
}

/**
 * Get icon for classification type
 * @param {string} classification - Classification type
 * @returns {string} - Icon emoji
 */
function getClassificationIcon(classification) {
    const icons = {
        needs: '🏠',
        wants: '🎉',
        goals: '🎯'
    };
    return icons[classification] || '📝';
}

/**
 * Format date string
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Filter expenses by classification
 * @param {string} classification - Classification to filter by
 */
function filterExpenses(classification) {
    loadExpenses(classification);
}

/**
 * Clear filter and show all expenses
 */
function clearFilter() {
    loadExpenses();
}
