// Enhanced Schedule Chat with Intelligent Automatic Actions
let isWaitingForResponse = false;

function initScheduleChat() {
    console.log('🚀 Initializing Intelligent Schedule Chat');
    
    const chatInput = document.getElementById('schedule-chat-input');
    const sendButton = document.getElementById('schedule-chat-send');
    
    if (chatInput && sendButton) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendScheduleMessage();
            }
        });
        
        sendButton.addEventListener('click', sendScheduleMessage);
        
        // Add welcome message
        addScheduleMessage('🤖 Assistant intelligent activé ! Je peux automatiquement reprogrammer vos rendez-vous selon vos préférences et les directives du cabinet. Dites-moi simplement ce dont vous avez besoin.', 'ai');
    }
}

async function sendScheduleMessage() {
    const input = document.getElementById('schedule-chat-input');
    const message = input.value.trim();
    
    if (!message || isWaitingForResponse) return;
    
    // Add user message
    addScheduleMessage(message, 'user');
    input.value = '';
    
    // Set waiting state
    isWaitingForResponse = true;
    const loadingMessage = addScheduleMessage('🧠 Analyse intelligente en cours...', 'ai', true);
    
    try {
        // Send message to AI for analysis
        const response = await fetch('/api/schedule-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                context: 'schedule_management'
            })
        });
        
        const data = await response.json();
        
        // Remove loading message
        if (loadingMessage) {
            loadingMessage.remove();
        }
        
        if (data.success) {
            // Add AI response
            addScheduleMessage(data.response, 'ai');
            
            // Check if actions were detected
            if (data.actions && data.actions.length > 0) {
                // Show detected actions
                const actionsHtml = formatDetectedActions(data.actions);
                addScheduleMessage(actionsHtml, 'ai');
                
                // Execute actions automatically for high-confidence actions
                await executeIntelligentActions(data.actions);
            }
        } else {
            addScheduleMessage('❌ Erreur lors de l\'analyse: ' + (data.error || 'Erreur inconnue'), 'ai');
        }
        
    } catch (error) {
        console.error('Error sending schedule message:', error);
        if (loadingMessage) {
            loadingMessage.remove();
        }
        addScheduleMessage('❌ Erreur de communication avec l\'assistant', 'ai');
    } finally {
        isWaitingForResponse = false;
    }
}

function formatDetectedActions(actions) {
    let html = '<div class="detected-actions">';
    html += '<h4>🎯 Actions détectées :</h4>';
    
    actions.forEach((action, index) => {
        const priorityColor = getPriorityColor(action.priority);
        const confidencePercent = (action.confidence * 100).toFixed(0);
        
        html += `
            <div class="action-item" style="border-left: 4px solid ${priorityColor};">
                <div class="action-header">
                    <span class="action-type">${getActionIcon(action.action)} ${action.action}</span>
                    <span class="action-confidence" style="color: ${priorityColor};">
                        ${confidencePercent}% confiance
                    </span>
                </div>
                <div class="action-details">
                    <strong>Date:</strong> ${action.date || 'Non spécifiée'}<br>
                    <strong>Priorité:</strong> ${action.priority}<br>
                    <strong>Détails:</strong> ${action.details || 'Aucun détail'}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

async function executeIntelligentActions(actions) {
    console.log('🚀 Executing intelligent actions automatically');
    
    for (const action of actions) {
        // Only execute high-confidence actions automatically
        if (action.confidence >= 0.7) {
            await executeAutomaticAction(action);
        } else {
            // For lower confidence actions, show manual confirmation
            showManualConfirmation(action);
        }
    }
}

async function executeAutomaticAction(action) {
    try {
        addScheduleMessage(`🤖 Exécution automatique : ${action.action} (${action.date})`, 'ai');
        
        if (action.action === 'reschedule') {
            // Find appointments for the date
            const appointments = await findAppointmentsForDate(action.date);
            
            if (appointments && appointments.length > 0) {
                // Execute intelligent rescheduling
                const response = await fetch('/api/schedule-execute-action', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        action: 'reschedule',
                        appointments: appointments,
                        context: action
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Show success message with details
                    addScheduleMessage(result.message, 'ai');
                    
                    // Show execution statistics
                    if (result.stats) {
                        const statsHtml = formatExecutionStats(result.stats);
                        addScheduleMessage(statsHtml, 'ai');
                    }
                    
                    // Refresh the schedule view
                    if (typeof loadScheduleData === 'function') {
                        loadScheduleData();
                    }
                } else {
                    addScheduleMessage(`❌ Erreur lors de l'exécution : ${result.message || result.error}`, 'ai');
                }
            } else {
                addScheduleMessage(`ℹ️ Aucun rendez-vous trouvé pour le ${action.date}`, 'ai');
            }
        }
        
    } catch (error) {
        console.error('Error executing automatic action:', error);
        addScheduleMessage(`❌ Erreur lors de l'exécution automatique : ${error.message}`, 'ai');
    }
}

function formatExecutionStats(stats) {
    return `
        <div class="execution-stats">
            <h4>📊 Statistiques d'exécution :</h4>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">${stats.total}</span>
                    <span class="stat-label">Total</span>
                </div>
                <div class="stat-item success">
                    <span class="stat-number">${stats.successful}</span>
                    <span class="stat-label">Réussis</span>
                </div>
                <div class="stat-item warning">
                    <span class="stat-number">${stats.failed}</span>
                    <span class="stat-label">Échecs</span>
                </div>
            </div>
        </div>
    `;
}

function showManualConfirmation(action) {
    const confirmationHtml = `
        <div class="manual-confirmation">
            <h4>🤔 Confirmation requise :</h4>
            <p><strong>Action :</strong> ${action.action}</p>
            <p><strong>Date :</strong> ${action.date}</p>
            <p><strong>Confiance :</strong> ${(action.confidence * 100).toFixed(0)}%</p>
            <p><strong>Détails :</strong> ${action.details}</p>
            
            <div class="confirmation-buttons">
                <button class="confirm-btn" onclick="confirmManualAction('${JSON.stringify(action).replace(/'/g, "\\'")}')">
                    ✅ Confirmer
                </button>
                <button class="cancel-btn" onclick="cancelManualAction()">
                    ❌ Annuler
                </button>
            </div>
        </div>
    `;
    
    addScheduleMessage(confirmationHtml, 'ai');
}

async function confirmManualAction(actionJson) {
    try {
        const action = JSON.parse(actionJson);
        await executeAutomaticAction(action);
    } catch (error) {
        console.error('Error confirming manual action:', error);
        addScheduleMessage('❌ Erreur lors de la confirmation', 'ai');
    }
}

function cancelManualAction() {
    addScheduleMessage('❌ Action annulée', 'ai');
}

async function findAppointmentsForDate(dateStr) {
    try {
        const response = await fetch('/api/schedule-find-appointments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                date: dateStr
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            return data.appointments;
        } else {
            console.error('Error finding appointments:', data.error);
            return [];
        }
        
    } catch (error) {
        console.error('Error finding appointments:', error);
        return [];
    }
}

function addScheduleMessage(message, sender, isLoading = false) {
    const chatMessages = document.getElementById('schedule-chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    if (isLoading) {
        messageDiv.classList.add('loading');
    }
    
    // Convert markdown-like formatting to HTML
    const formattedMessage = formatMessage(message);
    messageDiv.innerHTML = formattedMessage;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function formatMessage(message) {
    // Convert markdown-like formatting to HTML
    return message
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/^(#{1,6})\s*(.*?)$/gm, function(match, hashes, text) {
            const level = hashes.length;
            return `<h${level}>${text}</h${level}>`;
        });
}

function getActionIcon(action) {
    const icons = {
        'reschedule': '📅',
        'cancel': '❌',
        'block_time': '🚫',
        'emergency': '🚨',
        'find_slots': '🔍'
    };
    return icons[action] || '⚡';
}

function getPriorityColor(priority) {
    const colors = {
        'urgent': '#ff4444',
        'high': '#ff8800',
        'medium': '#ffaa00',
        'low': '#00aa00'
    };
    return colors[priority] || '#666666';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initScheduleChat); 