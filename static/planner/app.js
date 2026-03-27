document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-target]");
    if (button) {
        const target = document.getElementById(button.dataset.copyTarget);
        if (!target) {
            return;
        }
        const text = Array.from(target.querySelectorAll(".grocery-item span, p"))
            .map((element) => element.innerText.trim())
            .filter(Boolean)
            .join("\n");
        if (!text) {
            return;
        }
        await navigator.clipboard.writeText(text);
        const originalLabel = button.innerText;
        button.innerText = "Copied";
        window.setTimeout(() => {
            button.innerText = originalLabel;
        }, 1500);
        return;
    }

    const removeButton = event.target.closest(".grocery-remove");
    if (removeButton) {
        const row = removeButton.closest(".grocery-item");
        if (row) {
            row.remove();
        }
    }
});
