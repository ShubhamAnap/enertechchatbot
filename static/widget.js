(function () {
  "use strict";

  if (window.__EnerTechChatbotLoaded) return;
  window.__EnerTechChatbotLoaded = true;

  var script =
    document.currentScript ||
    document.querySelector('script[src*="widget.js"]');

  var baseUrl = (
    (script && script.getAttribute("data-base-url")) ||
    (script && script.src ? script.src.replace(/\/static\/widget\.js.*$/, "") : "") ||
    ""
  ).replace(/\/$/, "");

  var title = (script && script.getAttribute("data-title")) || "EnerTech Assistant";
  var subtitle =
    (script && script.getAttribute("data-subtitle")) || "Online · Ready to help";
  var welcome =
    (script && script.getAttribute("data-welcome")) ||
    "Hello! I'm your EnerTech assistant. Ask me about UPS, batteries, or power solutions.";
  var primaryColor =
    (script && script.getAttribute("data-primary-color")) || "#0B2388";
  var position =
    (script && script.getAttribute("data-position")) || "right";
  var apiKey = (script && script.getAttribute("data-api-key")) || "";
  var logoUrl =
    (script && script.getAttribute("data-logo")) ||
    "https://enertechups.com/wp-content/uploads/2022/10/Logo1-removebg-preview.png";

  if (!baseUrl) {
    console.error("[EnerTech Chatbot] data-base-url is required on the script tag.");
    return;
  }

  var host = document.createElement("div");
  host.id = "enertech-chatbot-host";
  host.style.cssText =
    "all:initial;position:fixed;z-index:2147483646;bottom:24px;" +
    (position === "left" ? "left:24px;" : "right:24px;");
  document.body.appendChild(host);

  var shadow = host.attachShadow({ mode: "open" });

  var style = document.createElement("style");
  style.textContent =
    '@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap");' +
    ":host{all:initial;font-family:'Plus Jakarta Sans',Segoe UI,sans-serif;}" +
    "*{box-sizing:border-box;}" +
    ".launcher{" +
    "width:64px;height:64px;border-radius:50%;border:3px solid #FFFFFF;cursor:pointer;" +
    "background:" +
    primaryColor +
    ";color:#fff;display:flex;align-items:center;justify-content:center;" +
    "box-shadow:0 12px 32px rgba(11,35,136,.35);transition:transform .2s ease,box-shadow .2s ease;" +
    "}" +
    ".launcher:hover{transform:translateY(-2px) scale(1.04);box-shadow:0 16px 40px rgba(11,35,136,.42);}" +
    ".launcher img{width:36px;height:36px;border-radius:50%;object-fit:contain;background:#FFFFFF;padding:2px;}" +
    ".launcher svg{width:28px;height:28px;fill:#FFFFFF;}" +
    ".panel{" +
    "position:absolute;bottom:84px;" +
    (position === "left" ? "left:0;" : "right:0;") +
    "width:380px;max-width:calc(100vw - 32px);height:560px;max-height:calc(100vh - 120px);" +
    "background:#FFFFFF;border-radius:20px;overflow:hidden;display:none;flex-direction:column;" +
    "box-shadow:0 24px 64px rgba(11,35,136,.22);border:1px solid #E6EAF5;" +
    "}" +
    ".panel.open{display:flex;animation:et-slide-up .24s ease;}" +
    "@keyframes et-slide-up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}" +
    ".header{" +
    "display:flex;align-items:center;gap:12px;padding:16px 18px;" +
    "background:" +
    primaryColor +
    ";color:#FFFFFF;" +
    "}" +
    ".header img{width:44px;height:44px;border-radius:50%;background:#FFFFFF;object-fit:contain;padding:3px;}" +
    ".header .meta{flex:1;min-width:0;}" +
    ".header .meta strong{display:block;font-size:15px;font-weight:700;letter-spacing:.2px;}" +
    ".header .meta span{display:block;font-size:12px;opacity:.9;margin-top:3px;font-weight:500;}" +
    ".status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#4ADE80;margin-right:6px;}" +
    ".close-btn{" +
    "background:rgba(255,255,255,.14);border:none;color:#FFFFFF;width:32px;height:32px;" +
    "border-radius:10px;font-size:20px;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;" +
    "}" +
    ".close-btn:hover{background:rgba(255,255,255,.24);}" +
    ".messages{" +
    "flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:12px;" +
    "background:#F5F7FC;" +
    "}" +
    ".bubble{" +
    "max-width:84%;padding:11px 14px;border-radius:16px;font-size:14px;line-height:1.5;" +
    "white-space:pre-wrap;word-break:break-word;font-weight:500;" +
    "}" +
    ".bot{align-self:flex-start;background:#FFFFFF;color:#1A2140;border:1px solid #E6EAF5;border-bottom-left-radius:6px;" +
    "box-shadow:0 2px 8px rgba(11,35,136,.04);}" +
    ".user{align-self:flex-end;background:" +
    primaryColor +
    ";color:#FFFFFF;border-bottom-right-radius:6px;" +
    "box-shadow:0 4px 14px rgba(11,35,136,.2);}" +
    ".typing{align-self:flex-start;background:#FFFFFF;color:#6B7394;font-size:13px;padding:10px 14px;" +
    "border-radius:16px;border:1px solid #E6EAF5;font-weight:500;}" +
    ".footer{display:flex;gap:10px;padding:14px;background:#FFFFFF;border-top:1px solid #E6EAF5;}" +
    ".footer input{" +
    "flex:1;border:1px solid #D9E0F2;outline:none;border-radius:12px;padding:12px 14px;" +
    "background:#F8F9FD;color:#1A2140;font-size:14px;font-family:inherit;font-weight:500;" +
    "transition:border-color .15s ease,box-shadow .15s ease;" +
    "}" +
    ".footer input:focus{border-color:" +
    primaryColor +
    ";box-shadow:0 0 0 3px rgba(11,35,136,.12);background:#FFFFFF;}" +
    ".footer input::placeholder{color:#8B93B0;}" +
    ".footer button{" +
    "border:none;border-radius:12px;padding:0 18px;cursor:pointer;" +
    "background:" +
    primaryColor +
    ";color:#FFFFFF;font-weight:700;font-size:14px;font-family:inherit;" +
    "transition:opacity .15s ease,transform .15s ease;" +
    "}" +
    ".footer button:hover{opacity:.92;transform:translateY(-1px);}" +
    ".footer button:disabled{opacity:.55;cursor:not-allowed;transform:none;}" +
    "@media (max-width:480px){" +
    ".panel{width:calc(100vw - 20px);height:min(72vh,580px);bottom:80px;}" +
    "}";

  shadow.appendChild(style);

  var panel = document.createElement("div");
  panel.className = "panel";
  panel.innerHTML =
    '<div class="header">' +
    '<img src="' +
    logoUrl +
    '" alt="logo" />' +
    '<div class="meta"><strong>' +
    escapeHtml(title) +
    '</strong><span><i class="status-dot"></i>' +
    escapeHtml(subtitle) +
    "</span></div>" +
    '<button class="close-btn" type="button" aria-label="Close">×</button>' +
    "</div>" +
    '<div class="messages"></div>' +
    '<form class="footer">' +
    '<input type="text" placeholder="Type your message..." autocomplete="off" required />' +
    "<button type=\"submit\">Send</button>" +
    "</form>";

  var launcher = document.createElement("button");
  launcher.className = "launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-label", "Open chat");
  launcher.innerHTML =
    '<img src="' +
    logoUrl +
    '" alt="Open chat" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'block\'" />' +
    '<svg style="display:none" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.2L4 17.2V4h16v12z"/></svg>';

  shadow.appendChild(panel);
  shadow.appendChild(launcher);

  var messagesEl = panel.querySelector(".messages");
  var form = panel.querySelector("form");
  var input = panel.querySelector("input");
  var sendBtn = panel.querySelector("button[type='submit']");
  var closeBtn = panel.querySelector(".close-btn");
  var open = false;
  var busy = false;

  addMessage(welcome, "bot");

  launcher.addEventListener("click", function () {
    open = !open;
    panel.classList.toggle("open", open);
    if (open) input.focus();
  });

  closeBtn.addEventListener("click", function () {
    open = false;
    panel.classList.remove("open");
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var text = (input.value || "").trim();
    if (!text || busy) return;
    input.value = "";
    addMessage(text, "user");
    sendMessage(text);
  });

  function addMessage(text, role) {
    var bubble = document.createElement("div");
    bubble.className = "bubble " + role;
    bubble.textContent = text;
    messagesEl.appendChild(bubble);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
  }

  function setTyping(show) {
    var existing = messagesEl.querySelector(".typing");
    if (existing) existing.remove();
    if (!show) return;
    var el = document.createElement("div");
    el.className = "typing";
    el.textContent = "Typing...";
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function sendMessage(text) {
    busy = true;
    sendBtn.disabled = true;
    setTyping(true);

    var headers = { "Content-Type": "application/json" };
    if (apiKey) headers["X-Widget-Key"] = apiKey;

    fetch(baseUrl + "/api/chat", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ message: text }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) throw new Error((data && data.error) || "Request failed");
          return data;
        });
      })
      .then(function (data) {
        setTyping(false);
        addMessage(data.answer || "No response received.", "bot");
      })
      .catch(function (err) {
        setTyping(false);
        addMessage(
          "Sorry, I couldn't reach the assistant. Please try again later.",
          "bot"
        );
        console.error("[EnerTech Chatbot]", err);
      })
      .finally(function () {
        busy = false;
        sendBtn.disabled = false;
        input.focus();
      });
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
