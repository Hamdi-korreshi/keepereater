document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-target]");
    if (!button) {
        return;
    }
    const target = document.getElementById(button.dataset.copyTarget);
    if (!target) {
        return;
    }
    const text = Array.from(target.querySelectorAll("div, p"))
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
});
