document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("addNetworkModal");

    const usernameInput = document.getElementById("username");
    const urlInput = document.getElementById("url");
    const typeSelect = document.getElementById("networkType");

    window.addSocialNetwork = async function () {
        const username = usernameInput.value.trim();
        const url = urlInput.value.trim();
        const network_type = typeSelect.value;

        if (!username || !url) {
            showError("Заполните все поля");
            return;
        }

        try {
            const res = await fetch("/api/social_networks/create", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    username: username,
                    url: url,
                    type: network_type
                })
            });

            const data = await res.json();

            if (data.status === true) {
                showSuccess("Социальная сеть успешно добавлена");

                usernameInput.value = "";
                urlInput.value = "";
                typeSelect.value = "telegram";

                closeModal("addNetworkModal");

                if (window.loadSocialNetworks) {
                    window.loadSocialNetworks();
                }
            } else {
                showError(data.message || "Ошибка при добавлении");
            }

        } catch (err) {
            showError("Ошибка соединения с сервером");
        }
    };
});
