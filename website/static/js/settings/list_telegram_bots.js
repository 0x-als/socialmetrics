document.addEventListener("DOMContentLoaded", () => {

    function formatDate(dateString) {
        if (!dateString) return "—";
        return dateString.split(".")[0];
    }

    window.loadTelegramBots = function () {
        fetch("/api/settings/telegram_bots/list", {
            method: "POST",
            headers: {"Content-Type": "application/json"}
        })
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById("telegramBotsBody");
                tbody.innerHTML = "";

                if (!data.status) {
                    showError(data.message || "Ошибка загрузки ботов");
                    return;
                }

                data.bots.forEach(bot => {
                    const tr = document.createElement("tr");

                    const tdName = document.createElement("td");
                    tdName.textContent = bot.bot_name;

                    const tdUrl = document.createElement("td");
                    const link = document.createElement("a");
                    link.href = bot.url;
                    link.target = "_blank";
                    link.className = "btn-link";
                    link.textContent = "перейти";
                    tdUrl.appendChild(link);

                    const tdStatus = document.createElement("td");
                    tdStatus.textContent = bot.status ? "Активен" : "Неактивен";

                    const tdCreated = document.createElement("td");
                    tdCreated.textContent = formatDate(bot.created_at);

                    const tdUpdated = document.createElement("td");
                    tdUpdated.textContent = formatDate(bot.updated_at);

                    const tdDelete = document.createElement("td");
                    const btnDelete = document.createElement("button");
                    btnDelete.className = "btn-delete";
                    btnDelete.textContent = "Удалить";
                    btnDelete.onclick = () => window.deleteTelegramBot(bot.id);
                    tdDelete.appendChild(btnDelete);

                    tr.appendChild(tdName);
                    tr.appendChild(tdUrl);
                    tr.appendChild(tdStatus);
                    tr.appendChild(tdCreated);
                    tr.appendChild(tdUpdated);
                    tr.appendChild(tdDelete);

                    tbody.appendChild(tr);
                });
            })
            .catch(() => {
                showError("Ошибка соединения с сервером");
            });
    };

    loadTelegramBots();
});