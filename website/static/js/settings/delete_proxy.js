async function deleteProxy(id) {
    if (!confirm("Вы действительно хотите удалить данный прокси?")) {
        return;
    }

    try {
        const response = await fetch("/api/settings/proxies/delete", {
            method: "DELETE",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({id: id})
        })

        const result = await response.json();

        if (result.status) {
            showSuccess("Прокси успешно удален!");
            loadProxies();
        } else {
            showError(result.message || "Не удалось удалить прокси");
        }

    } catch (e) {
        console.error(e)
        showError("Ошибка соединения с сервером!")
    }
}