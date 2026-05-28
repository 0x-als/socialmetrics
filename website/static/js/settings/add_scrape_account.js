function safeShowSuccess(message) {
    if (typeof window.showSuccess === "function") window.showSuccess(message);
    else alert(message);
}

function safeShowError(message) {
    if (typeof window.showError === "function") window.showError(message);
    else alert(message);
}

let currentStep = 1;
let vkInterval = null;

function clearModalFields() {
    document.getElementById("platformSelect").value = "";
    document.querySelectorAll(".platform-fields input").forEach(input => input.value = "");
    document.getElementById("vkQrImage").style.display = "none";
    document.getElementById("vkStatusText").style.display = "none";
    document.getElementById("vkInputFields").style.display = "block";
    document.getElementById("tgCodeBlock").style.display = "none";
    document.getElementById("tgPasswordBlock").style.display = "none";
    if (vkInterval) clearInterval(vkInterval);
    currentStep = 1;
}

function toggleFields() {
    const platform = document.getElementById("platformSelect").value;
    document.querySelectorAll(".platform-fields").forEach(f => f.style.display = "none");
    if (platform === "vk") document.getElementById("vkFields").style.display = "block";
    if (platform === "youtube") document.getElementById("youtubeFields").style.display = "block";
    if (platform === "telegram") document.getElementById("telegramFields").style.display = "block";
}

async function waitVkLogin() {
    const statusText = document.getElementById("vkStatusText");
    const client_id = document.querySelector("#vkFields input[placeholder='Client ID']").value.trim();
    const api_key = document.querySelector("#vkFields input[placeholder='API Key']").value.trim();

    if (!client_id || !api_key) {
        safeShowError("Client ID и API Key обязательны");
        return;
    }

    try {
        const res = await fetch("/api/settings/scrape_account/vk/wait_login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ client_id, api_key })
        });

        const data = await res.json();

        if (data.status === true) {
            statusText.textContent = "Профиль успешно сохранён!";
            statusText.style.color = "#22c55e";

            setTimeout(() => {
                closeModal("scrapeModal");
                safeShowSuccess("VK аккаунт успешно добавлен!");
                if (typeof window.loadScrapeAccounts === "function") window.loadScrapeAccounts();
            }, 1500);
        } else {
            statusText.textContent = data.message || "Ошибка авторизации VK";
            statusText.style.color = "#ef4444";
        }
    } catch (e) {
        console.error(e);
        statusText.textContent = "Ошибка соединения с сервером";
        statusText.style.color = "#ef4444";
    }
}



document.addEventListener("DOMContentLoaded", () => {
    const btn = document.querySelector("#scrapeModal button.btn-primary");
    if (!btn) return;

    btn.addEventListener("click", async function (e) {
        e.preventDefault();

        const platform = document.getElementById("platformSelect").value;
        if (!platform) {
            safeShowError("Выберите платформу");
            return;
        }

        if (platform === "telegram" && currentStep === 2) {
            const code = document.getElementById("tgCode").value.trim();
            if (!code) {
                safeShowError("Введите код подтверждения");
                return;
            }

            try {
                const res = await fetch("/api/settings/scrape_account/telegram/confirm", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({code})
                });

                const data = await res.json();

                if (data.status === true) {
                    safeShowSuccess("Telegram аккаунт добавлен");
                    clearModalFields();
                    closeModal("scrapeModal");
                    if (typeof window.loadScrapeAccounts === "function") loadScrapeAccounts();
                } else if (data.status === "password_required") {
                    currentStep = 3;
                    document.getElementById("tgPasswordBlock").style.display = "block";
                    btn.textContent = "Подтвердить пароль";
                } else safeShowError(data.message || "Ошибка подтверждения");

            } catch {
                safeShowError("Ошибка соединения с сервером");
            }

            return;
        }

        if (platform === "telegram" && currentStep === 3) {
            const password = document.getElementById("tgPassword").value.trim();
            if (!password) {
                safeShowError("Введите пароль");
                return;
            }

            try {
                const res = await fetch("/api/settings/scrape_account/telegram/password", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({password})
                });

                const data = await res.json();

                if (data.status === true) {
                    safeShowSuccess("Telegram аккаунт добавлен");
                    clearModalFields();
                    closeModal("scrapeModal");
                    if (typeof window.loadScrapeAccounts === "function") loadScrapeAccounts();
                } else {
                    safeShowError(data.message || "Ошибка подтверждения пароля");
                }

            } catch {
                safeShowError("Ошибка соединения с сервером");
            }

            return;
        }

        let fields = {};

        if (platform === "vk") {
            fields = {
                client_id: document.querySelector("#vkFields input[placeholder='Client ID']").value.trim(),
                api_key: document.querySelector("#vkFields input[placeholder='API Key']").value.trim()
            };
        }

        if (platform === "youtube") {
            fields = {
                api_key: document.querySelector("#youtubeFields input").value.trim()
            };
        }

        if (platform === "telegram") {
            fields = {
                phone: document.querySelector("#telegramFields input").value.trim(),
                api_id: document.getElementById("tgApiId").value.trim(),
                api_hash: document.getElementById("tgApiHash").value.trim()
            };
        }

        if (Object.values(fields).some(v => !v)) {
            safeShowError("Заполните все обязательные поля");
            return;
        }

        try {
            const response = await fetch("/api/settings/scrape_account", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({platform, fields})
            });

            const result = await response.json();

            if (platform === "vk" && result.status === "quick_response") {
                document.getElementById("vkInputFields").style.display = "none";

                const img = document.getElementById("vkQrImage");
                img.src = result.quick_response;
                img.style.display = "block";

                const statusText = document.getElementById("vkStatusText");
                statusText.style.display = "block";
                statusText.textContent = "Ожидание авторизации в VK...";

                waitVkLogin(fields.client_id, fields.api_key);
                return;
            }

            if (platform === "telegram" && result.status === "code_required") {
                currentStep = 2;
                document.getElementById("tgCodeBlock").style.display = "block";
                btn.textContent = "Подтвердить код";
                return;
            }

            if (result.status === true) {
                clearModalFields();
                closeModal("scrapeModal");
                safeShowSuccess(result.message || "Аккаунт успешно добавлен!");
                if (typeof window.loadScrapeAccounts === "function") loadScrapeAccounts();
            } else {
                safeShowError(result.message || "Ошибка при добавлении аккаунта");
            }

        } catch {
            safeShowError("Ошибка соединения с сервером");
        }
    });
});
