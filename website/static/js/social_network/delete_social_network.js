async function deleteNetwork(id) {
    if (!confirm("Вы действительно хотите удалить эту социальную сеть?")) {
        return;
    }

    try {
        const res = await fetch("/api/social_networks/delete", {
            method: "DELETE",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({id: id})
        });

        const result = await res.json();

        if (result.status) {
            showSuccess("Социальная сеть успешно удалена");
            loadSocialNetworks(document.getElementById("userFilter").value); // обновляем текущий фильтр
        } else {
            showError(result.message || "Не удалось удалить");
        }
    } catch (e) {
        console.error(e);
        showError("Ошибка соединения с сервером");
    }
}