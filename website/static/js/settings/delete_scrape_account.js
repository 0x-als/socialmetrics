async function deleteScrapeAccount(id) {
    if (!confirm("Вы действительно хотите удалить данный scrape-аккаунт?")) {
        return;
    }

    try {
        const response = await fetch("/api/settings/scrape_account/delete", {
            method: "DELETE",
            headers: {"Content-type": "application/json"},
            body: JSON.stringify({id: id})
        })

        const result = await response.json();

        if (result.status) {
            showSuccess("Scrape-аккаунт успешно удален!");
            loadScrapeAccounts();
        } else {
            showError(result.message || "Не удалось удалить scrape-аккаунт");
        }

    } catch (e) {
        console.error(e)
        showError("Ошибка соединения с сервером!")
    }
}