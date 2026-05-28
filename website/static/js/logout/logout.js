document.addEventListener("DOMContentLoaded", () => {
    const logoutLink = document.querySelector('.nav-item[href="/logout"]');

    if (logoutLink) {
        logoutLink.addEventListener("click", (event) => {
            event.preventDefault();
            window.location.href = "/logout";
        });
    }
});
