async function loadUsers() {
    try {
        const res = await fetch("/api/users/list");
        const data = await res.json();

        if (!data.status || !data.users) return;

        const select = document.getElementById("userFilter");
        select.innerHTML = '<option value="">Все пользователи</option>';

        data.users.forEach(user => {
            const option = document.createElement("option");
            option.value = user.id;
            option.textContent = user.login + (user.email ? ` (${user.email})` : "");
            select.appendChild(option);
        });
    } catch (e) {
        console.error("Ошибка загрузки пользователей:", e);
    }
}