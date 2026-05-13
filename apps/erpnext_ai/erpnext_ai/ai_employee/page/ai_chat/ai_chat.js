/**
 * AI Chat Page — ERPNext desk page
 * Mirrors NocoBase's AI Employee chat interface.
 *
 * Features:
 * - Employee selector (Dex / Viz / Avery)
 * - Conversation list sidebar
 * - Message thread with SSE streaming
 * - Tool call display (human-in-the-loop confirmation)
 * - Work context injection (current DocType/record)
 */

frappe.pages["ai-chat"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "AI Chat",
    single_column: true,
  });

  // Mount the chat app
  new AIChatApp(page, wrapper);
};

class AIChatApp {
  constructor(page, wrapper) {
    this.page = page;
    this.wrapper = wrapper;
    this.employees = [];
    this.conversations = [];
    this.currentEmployee = null;
    this.currentConversation = null;
    this.messages = [];
    this.streaming = false;

    this.render();
    this.loadEmployees();
  }

  render() {
    this.wrapper.innerHTML = "";

    const container = document.createElement("div");
    container.className = "ai-chat-container";
    container.style.cssText = `
      display: flex;
      height: calc(100vh - 120px);
      font-family: var(--font-stack);
      background: var(--bg-color);
    `;

    container.innerHTML = `
      <!-- Sidebar -->
      <div class="ai-chat-sidebar" style="
        width: 280px; min-width: 280px;
        border-right: 1px solid var(--border-color);
        display: flex; flex-direction: column;
        background: var(--control-bg);
      ">
        <!-- Employee selector -->
        <div style="padding: 12px; border-bottom: 1px solid var(--border-color);">
          <label style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">AI Employee</label>
          <select id="employee-select" style="
            width: 100%; margin-top: 6px;
            padding: 6px 10px;
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            background: var(--control-bg);
            color: var(--text-color);
            font-size: 13px;
          ">
            <option value="">Loading employees...</option>
          </select>
        </div>

        <!-- New chat button -->
        <div style="padding: 10px 12px; border-bottom: 1px solid var(--border-color);">
          <button id="new-chat-btn" style="
            width: 100%; padding: 8px;
            background: var(--primary); color: white;
            border: none; border-radius: var(--border-radius);
            cursor: pointer; font-size: 13px; font-weight: 500;
          ">+ New Conversation</button>
        </div>

        <!-- Conversation list -->
        <div id="conversation-list" style="
          flex: 1; overflow-y: auto;
          padding: 8px 0;
        "></div>
      </div>

      <!-- Main chat area -->
      <div class="ai-chat-main" style="
        flex: 1; display: flex; flex-direction: column;
        background: var(--bg-color);
      ">
        <!-- Employee header -->
        <div id="chat-header" style="
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
          display: flex; align-items: center; gap: 12px;
          background: var(--card-bg);
        ">
          <div style="
            width: 40px; height: 40px; border-radius: 50%;
            background: var(--primary-light);
            display: flex; align-items: center; justify-content: center;
            font-size: 20px;
          " id="employee-avatar">🤖</div>
          <div>
            <div style="font-weight: 600; font-size: 15px;" id="employee-name">Select an employee</div>
            <div style="font-size: 12px; color: var(--text-muted);" id="employee-position"></div>
          </div>
        </div>

        <!-- Messages -->
        <div id="message-thread" style="
          flex: 1; overflow-y: auto;
          padding: 20px; display: flex; flex-direction: column; gap: 16px;
        "></div>

        <!-- Input area -->
        <div style="
          padding: 16px 20px;
          border-top: 1px solid var(--border-color);
          background: var(--card-bg);
        ">
          <div style="display: flex; gap: 10px; align-items: flex-end;">
            <textarea id="message-input" placeholder="Message the AI employee..." style="
              flex: 1; padding: 10px 14px;
              border: 1px solid var(--border-color);
              border-radius: var(--border-radius);
              background: var(--control-bg);
              color: var(--text-color);
              font-size: 14px;
              resize: none; min-height: 44px; max-height: 200px;
              line-height: 1.5;
              font-family: var(--font-stack);
            " rows="1"></textarea>
            <button id="send-btn" style="
              padding: 10px 20px; height: 44px;
              background: var(--primary); color: white;
              border: none; border-radius: var(--border-radius);
              cursor: pointer; font-size: 14px; font-weight: 500;
              white-space: nowrap;
            ">Send</button>
          </div>
          <div style="margin-top: 8px; font-size: 11px; color: var(--text-muted);">
            Press <kbd style="background: var(--control-bg); border: 1px solid var(--border-color); border-radius: 3px; padding: 1px 4px;">Enter</kbd> to send,
            <kbd style="background: var(--control-bg); border: 1px solid var(--border-color); border-radius: 3px; padding: 1px 4px;">Shift+Enter</kbd> for new line
          </div>
        </div>
      </div>
    `;

    this.wrapper.querySelector(".page-content").appendChild(container);
    this.bindEvents();
  }

  bindEvents() {
    const w = this.wrapper;

    w.querySelector("#employee-select").addEventListener("change", (e) => {
      this.selectEmployee(e.target.value);
    });

    w.querySelector("#new-chat-btn").addEventListener("click", () => {
      this.newConversation();
    });

    const input = w.querySelector("#message-input");
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
      // Auto-resize
      setTimeout(() => {
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 200) + "px";
      }, 0);
    });

    w.querySelector("#send-btn").addEventListener("click", () => {
      this.sendMessage();
    });
  }

  async loadEmployees() {
    const r = await frappe.call({
      method: "erpnext_ai.erpnext_ai.api.chat.get_employees",
    });

    this.employees = r.message || [];
    const select = this.wrapper.querySelector("#employee-select");
    select.innerHTML =
      '<option value="">Choose an AI Employee...</option>' +
      this.employees
        .map(
          (e) =>
            `<option value="${e.name}">${e.nickname} — ${e.position}</option>`
        )
        .join("");

    // Auto-select first employee
    if (this.employees.length > 0) {
      select.value = this.employees[0].name;
      this.selectEmployee(this.employees[0].name);
    }
  }

  async selectEmployee(name) {
    this.currentEmployee = this.employees.find((e) => e.name === name);
    if (!this.currentEmployee) return;

    // Update header
    this.wrapper.querySelector("#employee-name").textContent =
      this.currentEmployee.nickname;
    this.wrapper.querySelector("#employee-position").textContent =
      this.currentEmployee.position;

    const avatarMap = { dex: "🔍", viz: "📊", avery: "⚡" };
    this.wrapper.querySelector("#employee-avatar").textContent =
      avatarMap[name] || "🤖";

    // Load conversations for this employee
    await this.loadConversations();

    // Start fresh conversation if none exists
    if (this.conversations.length === 0) {
      await this.newConversation();
    } else {
      await this.selectConversation(this.conversations[0].name);
    }
  }

  async loadConversations() {
    if (!this.currentEmployee) return;
    const r = await frappe.call({
      method: "erpnext_ai.erpnext_ai.api.chat.get_conversations",
      args: { employee_name: this.currentEmployee.name },
    });
    this.conversations = r.message || [];
    this.renderConversationList();
  }

  renderConversationList() {
    const list = this.wrapper.querySelector("#conversation-list");
    list.innerHTML = this.conversations
      .map(
        (c) => `
      <div class="conv-item" data-name="${c.name}" style="
        padding: 10px 16px; cursor: pointer;
        border-left: 3px solid transparent;
        transition: all 0.15s;
        ${c.name === this.currentConversation?.name ? "border-left-color: var(--primary); background: var(--bg-color);" : ""}
      ">
        <div style="font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${c.title}</div>
        <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">${frappe.datetime.prettyDate(c.modified)}</div>
      </div>
    `
      )
      .join("");

    list.querySelectorAll(".conv-item").forEach((item) => {
      item.addEventListener("click", () => {
        this.selectConversation(item.dataset.name);
      });
    });
  }

  async newConversation() {
    if (!this.currentEmployee) {
      frappe.msgprint("Please select an AI Employee first.");
      return;
    }
    const r = await frappe.call({
      method: "erpnext_ai.erpnext_ai.api.chat.create_conversation",
      args: { employee_name: this.currentEmployee.name },
    });
    const conv = r.message;
    await this.loadConversations();
    await this.selectConversation(conv.conversation);
  }

  async selectConversation(name) {
    const r = await frappe.call({
      method: "erpnext_ai.erpnext_ai.api.chat.get_messages",
      args: { conversation_name: name },
    });
    this.currentConversation = this.conversations.find((c) => c.name === name);
    this.messages = r.message || [];
    this.renderMessages();
    this.renderConversationList();
  }

  renderMessages() {
    const thread = this.wrapper.querySelector("#message-thread");

    if (this.messages.length === 0 && this.currentEmployee) {
      // Show greeting
      const greeting = this.currentEmployee.greeting || `Hi! I'm ${this.currentEmployee.nickname}. How can I help?`;
      thread.innerHTML = `
        <div style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
          <div style="font-size: 48px; margin-bottom: 12px;">${{ dex: "🔍", viz: "📊", avery: "⚡" }[this.currentEmployee.name] || "🤖"}</div>
          <div style="font-size: 16px; font-weight: 600; color: var(--text-color); margin-bottom: 8px;">${this.currentEmployee.nickname}</div>
          <div style="font-size: 14px; max-width: 400px; margin: 0 auto; line-height: 1.6;">${greeting}</div>
        </div>
      `;
      return;
    }

    thread.innerHTML = this.messages
      .filter((m) => m.role !== "system")
      .map((m) => this.renderMessage(m))
      .join("");

    thread.scrollTop = thread.scrollHeight;
  }

  renderMessage(msg) {
    const isUser = msg.role === "user";
    const isTool = msg.role === "tool";

    if (isTool) {
      return `
        <div style="
          background: var(--control-bg);
          border: 1px solid var(--border-color);
          border-radius: var(--border-radius);
          padding: 10px 14px;
          font-size: 12px;
          font-family: monospace;
          color: var(--text-muted);
        ">
          <span style="color: var(--yellow-600);">⚙ Tool result</span>
          <pre style="margin: 4px 0 0; white-space: pre-wrap; word-break: break-all;">${frappe.utils.escape_html(msg.content || "")}</pre>
        </div>
      `;
    }

    return `
      <div style="
        display: flex;
        flex-direction: ${isUser ? "row-reverse" : "row"};
        gap: 10px; align-items: flex-start;
      ">
        <div style="
          width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
          background: ${isUser ? "var(--primary)" : "var(--control-bg)"};
          border: 1px solid var(--border-color);
          display: flex; align-items: center; justify-content: center;
          font-size: 14px;
        ">${isUser ? "👤" : this.currentEmployee?.name === "viz" ? "📊" : this.currentEmployee?.name === "dex" ? "🔍" : "⚡"}</div>
        <div style="
          max-width: 75%;
          background: ${isUser ? "var(--primary)" : "var(--card-bg)"};
          color: ${isUser ? "white" : "var(--text-color)"};
          border: 1px solid ${isUser ? "var(--primary)" : "var(--border-color)"};
          border-radius: var(--border-radius);
          padding: 12px 16px;
          font-size: 14px;
          line-height: 1.6;
        ">
          ${frappe.utils.escape_html(msg.content || "").replace(/\n/g, "<br>")}
          ${msg.tool_calls ? `<div style="margin-top: 8px; font-size: 11px; opacity: 0.7;">Used tools: ${msg.tool_calls.map(t => t.function?.name || t.name || "tool").join(", ")}</div>` : ""}
        </div>
      </div>
    `;
  }

  async sendMessage() {
    const input = this.wrapper.querySelector("#message-input");
    const text = input.value.trim();
    if (!text || this.streaming) return;
    if (!this.currentConversation) {
      frappe.msgprint("Please start or select a conversation first.");
      return;
    }

    input.value = "";
    input.style.height = "auto";

    // Add user message to UI immediately
    this.messages.push({ role: "user", content: text });
    this.renderMessages();

    this.streaming = true;
    const sendBtn = this.wrapper.querySelector("#send-btn");
    sendBtn.textContent = "...";
    sendBtn.disabled = true;

    // Add streaming assistant message
    const thread = this.wrapper.querySelector("#message-thread");
    const streamDiv = document.createElement("div");
    streamDiv.style.cssText = `
      display: flex; gap: 10px; align-items: flex-start;
    `;
    streamDiv.innerHTML = `
      <div style="
        width: 32px; height: 32px; border-radius: 50%;
        background: var(--control-bg); border: 1px solid var(--border-color);
        display: flex; align-items: center; justify-content: center; font-size: 14px;
      ">${this.currentEmployee?.name === "viz" ? "📊" : this.currentEmployee?.name === "dex" ? "🔍" : "⚡"}</div>
      <div id="streaming-bubble" style="
        max-width: 75%; background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 12px 16px; font-size: 14px; line-height: 1.6;
        color: var(--text-color); min-width: 40px;
      "><span class="typing-dots" style="opacity: 0.5;">▊</span></div>
    `;
    thread.appendChild(streamDiv);
    thread.scrollTop = thread.scrollHeight;

    const bubble = streamDiv.querySelector("#streaming-bubble");
    let assistantText = "";

    try {
      // Call via frappe.call (sync for now — SSE upgrade later)
      const r = await frappe.call({
        method: "erpnext_ai.erpnext_ai.api.chat.send_message",
        args: {
          conversation_name: this.currentConversation.name,
          message: text,
          work_context: JSON.stringify({
            route: frappe.get_route_str(),
            doctype: frappe.get_route()[1] || null,
          }),
        },
      });

      // Parse SSE events from the response
      const raw = r.message || "";
      raw.split("\n\n").forEach((block) => {
        block.split("\n").forEach((line) => {
          if (line.startsWith("data: ")) {
            try {
              const evt = JSON.parse(line.slice(6));
              if (evt.type === "content_delta") {
                assistantText += evt.text;
              } else if (evt.type === "tool_call") {
                assistantText += `\n\n[Using tool: ${evt.tool}]`;
              }
            } catch {}
          }
        });
      });

      bubble.textContent = assistantText || "Done.";
    } catch (err) {
      bubble.textContent = "Error: " + (err.message || "Something went wrong.");
      bubble.style.color = "var(--red-500)";
    } finally {
      this.streaming = false;
      sendBtn.textContent = "Send";
      sendBtn.disabled = false;

      // Reload messages from server
      await this.selectConversation(this.currentConversation.name);
    }
  }
}
