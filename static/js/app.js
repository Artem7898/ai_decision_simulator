console.log('AI Decision Simulator frontend loaded');

// Функция для обновления иконок
function updateIcons() {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Функция для показа уведомлений
function showNotification(message, type = 'info') {
    const colors = {
        success: 'green',
        error: 'red',
        warning: 'yellow',
        info: 'blue'
    };

    const color = colors[type] || 'blue';

    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 bg-${color}-100 border border-${color}-400 text-${color}-700 px-4 py-3 rounded-lg shadow-lg z-50 transition-all duration-300`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info'}"
               class="w-5 h-5 mr-2"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);
    updateIcons();

    // Автоматическое скрытие
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Экспорт функций для использования в HTML
window.appHelpers = {
    updateIcons,
    showNotification
};