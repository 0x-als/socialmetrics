let isNotificationsInitialized = false;

function initNotifications() {
    if (isNotificationsInitialized) return;
    isNotificationsInitialized = true;

    function createToast(message, type) {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${message}</span>`;
        document.body.appendChild(toast);

        // Показываем с небольшой задержкой
        setTimeout(() => {
            toast.classList.add("show");
        }, 10);

        // Удаляем через 4 секунды
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 400);
        }, 4000);
    }

    window.showSuccess = function(message) {
        createToast(message, "success");
    };

    window.showError = function(message) {
        createToast(message, "error");
    };

    // Для удобства
    window.showNotification = function(message, type = "success") {
        createToast(message, type);
    };
}

// Инициализируем сразу при загрузке скрипта
initNotifications();