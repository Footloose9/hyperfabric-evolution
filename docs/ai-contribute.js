/* Public-only, user-initiated clipboard helper; no model calls or network access. */
(function () {
  "use strict";
  const button = document.getElementById("copy-prompt");
  const prompt = document.getElementById("starter-prompt");
  const status = document.getElementById("copy-status");
  if (!button || !prompt || !status) return;

  button.addEventListener("click", async function () {
    const text = prompt.value.trim();
    if (!text) {
      status.textContent = "Prompt unavailable. Use the public written guide.";
      return;
    }
    try {
      if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
        throw new Error("Clipboard API unavailable");
      }
      await navigator.clipboard.writeText(text);
      status.textContent = "Prompt copied. Paste it into the AI assistant you choose.";
      button.textContent = "Copied — paste into your AI";
    } catch (_error) {
      prompt.focus();
      prompt.select();
      status.textContent = "Clipboard blocked. The prompt is selected; copy it using your device's copy command.";
      button.textContent = "Prompt selected";
    }
  });
}());
