function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = "flex";
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
    const modals = document.querySelectorAll(".modal");

    modals.forEach(modal => {
        modal.addEventListener("click", function (e) {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });

    const closeBtns = document.querySelectorAll(".modal-close");

    closeBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const modal = btn.closest(".modal");
            if (modal) closeModal(modal.id);
        });
    });
});


function toggleFields() {
    const platform = document.getElementById('platformSelect').value;

    document.getElementById('vkFields').style.display = 'none';
    document.getElementById('youtubeFields').style.display = 'none';
    document.getElementById('telegramFields').style.display = 'none';

    if (platform === 'vk') {
        document.getElementById('vkFields').style.display = 'block';
    } else if (platform === 'youtube') {
        document.getElementById('youtubeFields').style.display = 'block';
    } else if (platform === 'telegram') {
        document.getElementById('telegramFields').style.display = 'block';
    }
}