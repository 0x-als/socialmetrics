window.loadSocialNetworks = async function (userId = "") {
    try {
        const res = await fetch("/api/social_networks/list", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId })
        });

        const data = await res.json();
        const tbody = document.getElementById("networksBody");
        tbody.innerHTML = "";

        if (!data.networks) return;

        data.networks.forEach(network => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${network.username}</td>
                <td><a href="${network.url}" target="_blank" class="link">${network.url}</a></td>
                <td>${network.type.toUpperCase()}</td>
                <td class="status-active">${network.status ? "Активен" : "Неактивен"}</td>
                <td>
                    <button class="btn-delete" onclick="deleteNetwork(${network.id})">Удалить</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
        showError("Ошибка загрузки данных");
    }
};

// Загрузка списка пользователей в select
async function loadUsers() {
    try {
        const res = await fetch("/api/users/list");
        const data = await res.json();

        const select = document.getElementById("userFilter");
        select.innerHTML = '<option value="">Все пользователи</option>';

        data.users.forEach(user => {
            const option = document.createElement("option");
            option.value = user.id;
            option.textContent = user.login;
            select.appendChild(option);
        });
    } catch (e) {
        console.error(e);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadUsers();
    loadSocialNetworks();   // загрузка всех по умолчанию
});