async function deleteTelegramBot(id) {
    if (!confirm("Вы действительно хотите удалить данного бота?")) {
        return;
    }

    try {
        const response = await fetch("/api/settings/telegram_bot/delete", {
            method: "DELETE",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({id: id})
        })

        const result = await response.json();

        if (result.status) {
            showSuccess("Телеграм бота успешно удален!");
            loadTelegramBots();
        } else {
            showError(result.message || "Не удалось удалить телеграм бота");
        }

    } catch (e) {
        console.error(e)
        showError("Ошибка соединения с сервером!")
    }
}