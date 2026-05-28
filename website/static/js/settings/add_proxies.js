window.downloadProxiesExcel = function () {
    const csv =
"\uFEFFlogin;password;host;port\r\n" +
"example_user;StrongPass123;123.45.67.89;8080\r\n" +
"user2;MySecretPass;98.76.54.32;3128\r\n" +
"user3;Password123;45.67.89.123;9050";

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "proxies_template.csv";
    link.click();
};

window.uploadProxiesExcel = async function () {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".csv,.xlsx,.xls";

    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("/api/settings/proxies/create", {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if (data.status) {
            showSuccess(`Успешно добавлено ${data.added}`);
            if (typeof loadProxies === "function") loadProxies();
        } else {
            showError(data.message);
        }
    };

    input.click();
};

window.addProxy = async function () {
    const address = document.getElementById("proxyAddress").value.trim();
    const login = document.getElementById("proxyLogin").value.trim();
    const password = document.getElementById("proxyPassword").value.trim();

    if (!address) {
        showError("Введите адрес прокси (host:port)");
        return;
    }

    const [host, port] = address.split(":");
    if (!host || !port) {
        showError("Неверный формат. Используйте host:port");
        return;
    }

    const res = await fetch("/api/settings/proxies/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            proxies: [{
                host: host.trim(),
                port: port.trim(),
                login: login || null,
                password: password || null
            }]
        })
    });

    const data = await res.json();

    if (data.status) {
        showSuccess("Прокси успешно добавлен");
        closeModal("proxyModal");
        loadProxies();
    } else {
        showError(data.message);
    }
};
