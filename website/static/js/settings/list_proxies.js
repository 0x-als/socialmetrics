document.addEventListener("DOMContentLoaded", () => {

    function formatDate(dateString) {
        if (!dateString) return "—";
        return dateString.split(".")[0].replace("T", " ");
    }

    window.loadProxies = function () {
        fetch("/api/settings/proxies/list", {
            method: "GET",
            headers: {"Content-Type": "application/json"}
        })
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById("proxyTableBody");
                tbody.innerHTML = "";

                if (!data.status) {
                    showError(data.message || "Ошибка загрузки прокси");
                    return;
                }

                if (!data.proxies || data.proxies.length === 0) {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td colspan="6" style="padding: 40px 20px; color: #8a94a6; font-style: italic; text-align: center;">
                            Прокси не найдены
                        </td>
                    `;
                    tbody.appendChild(tr);
                    return;
                }

                data.proxies.forEach(proxy => {
                    const tr = document.createElement("tr");

                    const tdHost = document.createElement("td");
                    tdHost.textContent = `${proxy.host}:${proxy.port}`;

                    const tdType = document.createElement("td");
                    tdType.textContent = "SOCKS5";

                    const tdLogin = document.createElement("td");
                    tdLogin.textContent = proxy.login || "—";

                    const tdStatus = document.createElement("td");
                    tdStatus.textContent = proxy.status ? "Активен" : "Неактивен";
                    tdStatus.className = proxy.status ? "status-active" : "status-inactive";

                    const tdCreatedAt = document.createElement("td");
                    tdCreatedAt.textContent = formatDate(proxy.created_at);

                    const tdDelete = document.createElement("td");
                    const btnDelete = document.createElement("button");
                    btnDelete.className = "btn-delete";
                    btnDelete.textContent = "Удалить";
                    btnDelete.onclick = () => window.deleteProxy(proxy.id)
                    tdDelete.appendChild(btnDelete);

                    tr.appendChild(tdHost);
                    tr.appendChild(tdType);
                    tr.appendChild(tdLogin);
                    tr.appendChild(tdStatus);
                    tr.appendChild(tdCreatedAt);
                    tr.appendChild(tdDelete);

                    tbody.appendChild(tr);
                });
            })
            .catch(() => {
                showError("Ошибка соединения с сервером");
            });
    };

    loadProxies();
});