/* Human-triggered public prompt launcher. No API calls, cookies, extensions or cross-origin scripting. */
(function () {
  "use strict";

  const prompt = document.getElementById("starter-prompt");
  const message = document.getElementById("provider-status");
  const localAddress = document.getElementById("local-webui-url");
  const links = Array.from(document.querySelectorAll("a[data-ai-provider]"));
  if (!prompt || !message || !links.length) return;

  /* A prefill mode is NOT a promise that an external product will honor it.
   * "documented": vendor-published composer URL format.
   * "best-effort": publicly observed but not a stable published integration.
   * "copy": launch only; the user pastes the copied prompt.
   */
  const PROVIDERS = Object.freeze({
    chatgpt: { name: "ChatGPT", base: "https://chatgpt.com/", key: "prompt", mode: "best-effort" },
    claude: { name: "Claude", base: "https://claude.ai/new", key: "q", mode: "best-effort" },
    grok: { name: "Grok", base: "https://grok.com/", key: "q", mode: "best-effort" },
    gemini: { name: "Gemini", base: "https://gemini.google.com/app", mode: "copy" },
    codex: { name: "Codex desktop", base: "codex://new", key: "prompt", mode: "documented" },
    claudeDesktop: { name: "Claude Desktop", base: "claude://claude.ai/new", key: "q", mode: "documented" },
    claudeCode: { name: "Claude Code", base: "https://claude.ai/code/new", key: "q", mode: "documented" },
    copilot: { name: "Copilot", base: "https://copilot.microsoft.com/", mode: "copy" },
    perplexity: { name: "Perplexity", base: "https://www.perplexity.ai/", mode: "copy" },
    deepseek: { name: "DeepSeek", base: "https://chat.deepseek.com/", mode: "copy" },
    mistral: { name: "Le Chat", base: "https://chat.mistral.ai/chat", mode: "copy" },
    poe: { name: "Poe", base: "https://poe.com/", mode: "copy" },
    webui: { name: "Local / Open WebUI", key: "q", mode: "documented" }
  });

  function validatedWebUI(raw) {
    try {
      const url = new URL(raw.trim());
      if (url.username || url.password || url.hash || url.search) return null;
      if (!["http:", "https:"].includes(url.protocol)) return null;
      const loopback = ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
      if (!loopback && url.protocol !== "https:") return null;
      return url.href;
    } catch (_ignored) {
      return null;
    }
  }

  function linkFor(provider, text, local) {
    if (!provider || !text || text.length > 12000) return null;
    const base = provider === PROVIDERS.webui ? validatedWebUI(local || "") : provider.base;
    if (!base) return null;
    try {
      const url = new URL(base);
      if (provider.key) url.searchParams.set(provider.key, text);
      return url.href;
    } catch (_ignored) {
      return null;
    }
  }

  function selectForManualCopy(note) {
    prompt.focus();
    prompt.select();
    message.textContent = note;
  }

  function copyWithFeedback(provider) {
    const text = prompt.value.trim();
    if (!text) {
      message.textContent = "Public prompt unavailable. Open the written guide instead.";
      return;
    }
    if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
      selectForManualCopy("Clipboard unavailable. The prompt is selected for manual copying.");
      return;
    }
    try {
      /* Invoke writeText inside the trusted click, BEFORE opening another site.
       * Do not await here: the native anchor navigation remains user-initiated. */
      const pending = navigator.clipboard.writeText(text);
      message.textContent = "Launching " + provider.name + ". Copy requested; check the other tab and press Send yourself.";
      Promise.resolve(pending).then(function () {
        const instruction = provider.mode === "copy"
          ? "Paste the copied prompt into its composer, then press Send."
          : "If the prompt did not prefill, paste your copied prompt, then press Send.";
        message.textContent = provider.name + " launch requested. " + instruction;
      }).catch(function () {
        selectForManualCopy("Copy was blocked. Return here, copy the selected text and paste it into " + provider.name + ".");
      });
    } catch (_error) {
      selectForManualCopy("Copy was blocked. The public prompt is selected; paste it into " + provider.name + ".");
    }
  }

  function refresh() {
    const text = prompt.value.trim();
    links.forEach(function (link) {
      const provider = PROVIDERS[link.dataset.aiProvider];
      const url = linkFor(provider, text, localAddress && localAddress.value);
      if (!url) {
        link.removeAttribute("href");
        link.setAttribute("aria-disabled", "true");
      } else {
        link.href = url;
        link.removeAttribute("aria-disabled");
      }
    });
    if (localAddress) {
      const valid = !!validatedWebUI(localAddress.value);
      localAddress.setAttribute("aria-invalid", valid ? "false" : "true");
    }
  }

  links.forEach(function (link) {
    link.addEventListener("click", function (event) {
      const provider = PROVIDERS[link.dataset.aiProvider];
      if (!provider || !link.hasAttribute("href") || !prompt.value.trim()) {
        event.preventDefault();
        message.textContent = "Choose a valid assistant or local Open WebUI address first.";
        if (link.dataset.aiProvider === "webui" && localAddress) localAddress.focus();
        return;
      }
      copyWithFeedback(provider);
      /* No preventDefault: native <a target="_blank"> opens a separate tab/app.
       * A plain browser cannot write into an unrelated vendor's page. */
    });
  });

  if (localAddress) localAddress.addEventListener("input", refresh);
  refresh();
}());