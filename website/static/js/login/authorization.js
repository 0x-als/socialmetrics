document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("loginForm");
    const loginInput = document.getElementById("login");
    const passwordInput = document.getElementById("password");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const login = loginInput.value.trim();
        const password = passwordInput.value.trim();

        if (!login || !password) {
            showError("Введите логин и пароль");
            return;
        }

        try {
            const response = await fetch("/api/login/authorization", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ login, password })
            });

            const data = await response.json();

            if (data.status) {
                window.location.href = "/dashboard";
            } else {
                showError(data.error || "Ошибка авторизации");
            }

        } catch (err) {
            showError("Ошибка соединения с сервером");
        }
    });

    function showError(message) {
        let box = document.getElementById("error-box");

        if (!box) {
            box = document.createElement("div");
            box.id = "error-box";
            box.className = "error-box";
            document.querySelector(".login-card").prepend(box);
        }

        box.textContent = message;
        box.style.opacity = "1";

        setTimeout(() => {
            box.style.opacity = "0";
        }, 3000);
    }
});
