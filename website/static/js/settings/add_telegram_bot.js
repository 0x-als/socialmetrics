document.addEventListener("DOMContentLoaded", () => {
    const botModal = document.getElementById("botModal");
    const botForm = botModal.querySelector("form");
    const tokenInput = botForm.querySelector("input");

    botForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const token = tokenInput.value.trim();
        if (!token) {
            showError("Введите токен бота");
            return;
        }

        try {
            const res = await fetch("/api/settings/telegram_bots/create", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ token })
            });

            const data = await res.json();

            if (data.status === true) {
                showSuccess(`Бот «${data.name}» успешно добавлен`);

                tokenInput.value = "";
                closeModal("botModal");

                if (window.loadTelegramBots) {
                    window.loadTelegramBots(); // ← работает!
                }
            } else {
                showError(data.message || "Ошибка при добавлении бота");
            }
        } catch (err) {
            showError("Ошибка соединения с сервером");
        }
    });
});
