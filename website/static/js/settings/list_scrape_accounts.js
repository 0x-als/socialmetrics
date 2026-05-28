document.addEventListener("DOMContentLoaded", () => {

    window.loadScrapeAccounts = async function () {
        try {
            const res = await fetch('/api/list/scrape_accounts');
            const accounts = await res.json();

            const tbody = document.getElementById('scrapeTableBody');
            tbody.innerHTML = '';

            accounts.forEach(acc => {
                const tr = document.createElement('tr');

                tr.innerHTML = `
                    <td>${acc.path || "Не требуется"}</td>
                    <td>${acc.type}</td>
                    <td class="status-active">${acc.status ? 'Активен' : 'Неактивен'}</td>
                    <td>
                        <button class="btn-delete" onclick="deleteScrapeAccount(${acc.id})">
                            Удалить
                        </button>
                    </td>
                `;

                tbody.appendChild(tr);
            });

        } catch (e) {
            console.error("Ошибка загрузки scrape аккаунтов:", e);
            showError("Ошибка загрузки scrape аккаунтов");
        }
    };

    loadScrapeAccounts();
});
