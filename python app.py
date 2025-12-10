# app.py
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# ---------------------------
# YOUR GEMINI API KEY (hard-coded)
# ---------------------------
GEMINI_API_KEY = "AIzaSyAQYQRc80LvZD34_dp2N6F61Mr6Xt9EGWk"
# ---------------------------

# Import Google GenAI SDK (install with pip install google-genai)
try:
    from google import genai
except Exception as e:
    raise RuntimeError("Install google-genai: pip install google-genai") from e

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)
CORS(app)

# Simple in-memory sessions -> { session_id: [ {role, text, ts} ] }
SESSIONS = {}
MODEL = "gemini-2.5-flash"

# -----------------------------
# BEAUTIFUL UI / UX with Key Benefits & Integrations
# -----------------------------
INDEX_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Gemini Chatbot — UX Upgrade</title>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">

<style>
:root{
  --bg:#0b1220; --panel:#07101a; --muted:#94a3b8; --accent:#60a5fa; --accent-2:#6ee7b7;
  --surface: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  --glass: rgba(255,255,255,0.03);
  --radius:14px;
  --max-width:1100px;
}
*{box-sizing:border-box}
body{
  font-family:Inter,system-ui,Segoe UI,Roboto,Arial;
  margin:0; background:linear-gradient(180deg,#031026 0%,#041a2b 100%);
  color:#e6eef8; display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;
}
.app{width:100%; max-width:var(--max-width); border-radius:16px; overflow:hidden; background:var(--panel); display:grid; grid-template-columns:340px 1fr; gap:18px; box-shadow:0 10px 40px rgba(2,6,23,0.7);}

/* SIDEBAR */
.sidebar{padding:18px;border-right:1px solid rgba(255,255,255,0.03); display:flex;flex-direction:column; gap:12px}
.brand{display:flex;align-items:center;gap:12px}
.logo{width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,var(--accent-2),var(--accent));display:flex;align-items:center;justify-content:center;color:#042b4f;font-weight:800}
.brand h1{margin:0;font-size:16px}
.controls{display:flex;gap:8px;margin-top:6px}
.btn{padding:8px 10px;border-radius:10px;background:transparent;border:1px solid rgba(255,255,255,0.04);cursor:pointer;color:var(--muted);font-size:13px}
.btn.primary{background:linear-gradient(90deg,var(--accent),var(--accent-2));color:#042b4f;border:none;font-weight:700}

/* Value card */
.value-card{margin-top:8px;padding:12px;border-radius:10px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.02)}
.value-card h3{margin:0 0 8px 0;font-size:14px}
.value-card ul{margin:0;padding-left:18px;color:var(--muted);font-size:13px}
.value-card li{margin-bottom:6px}

/* integration list */
.integrations{margin-top:10px;padding:10px;border-radius:10px;background:transparent;border:1px solid rgba(255,255,255,0.015)}
.integrations h4{margin:0 0 8px 0;font-size:13px}
.integration-item{font-size:13px;color:var(--muted);margin-bottom:6px}

/* session list */
.sessions{margin-top:10px;display:flex;flex-direction:column;gap:8px;overflow:auto;padding-right:6px}
.session{display:flex;align-items:center;gap:10px;padding:10px;border-radius:10px;background:transparent;border:1px solid rgba(255,255,255,0.015);cursor:pointer}
.session.active{background:linear-gradient(90deg, rgba(96,165,250,0.06), rgba(110,231,183,0.02));outline:2px solid rgba(96,165,250,0.08)}
.session .meta{font-size:12px;color:var(--muted)}

/* CHAT AREA */
.chat-wrap{display:flex;flex-direction:column;height:calc(80vh); min-height:480px}
.chat-header{display:flex;align-items:center;justify-content:space-between;padding:18px;border-bottom:1px solid rgba(255,255,255,0.02)}
.chat-title{display:flex;align-items:center;gap:12px}
.avatar{width:44px;height:44px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center;color:#042b4f;font-weight:800}
.model-tag{font-size:13px;color:var(--muted)}
.messages{flex:1;overflow:auto;padding:20px;display:flex;flex-direction:column;gap:12px;background:linear-gradient(180deg, rgba(255,255,255,0.01), transparent)}
.msg-row{display:flex;gap:12px;align-items:flex-end}
.msg-row.user{justify-content:flex-end}
.bubble{max-width:72%;padding:12px 14px;border-radius:12px;line-height:1.4;box-shadow:0 6px 18px rgba(2,6,23,0.45)}
.bubble.user{background:linear-gradient(180deg,#071022,#0b1626);border:1px solid rgba(255,255,255,0.02);align-self:flex-end}
.bubble.bot{background:linear-gradient(180deg,#06121a,#071726);border:1px solid rgba(255,255,255,0.015);align-self:flex-start}
.meta-time{display:block;font-size:11px;color:var(--muted);margin-top:6px}
.actions{display:flex;gap:8px;margin-left:6px}
.icon-btn{background:transparent;border:0;color:var(--muted);cursor:pointer;font-size:13px}

/* composer */
.composer{display:flex;gap:10px;padding:14px;border-top:1px solid rgba(255,255,255,0.02)}
.input{flex:1;background:transparent;border:1px solid rgba(255,255,255,0.04);padding:12px;border-radius:10px;color:inherit;min-height:56px;resize:vertical}
.row-right{display:flex;gap:8px;align-items:center}
.small{font-size:12px;color:var(--muted)}

/* utility */
.center{display:flex;align-items:center;justify-content:center}
.footer-note{font-size:12px;color:var(--muted);margin-top:auto;padding-top:8px}

/* responsive */
@media (max-width:900px){
  .app{grid-template-columns:1fr;min-height:90vh}
  .sidebar{display:none}
}
</style>
</head>
<body>
  <div class="app" role="application" aria-label="Gemini Chatbot">
    <aside class="sidebar" aria-label="Sidebar">
      <div class="brand">
        <div class="logo">G</div>
        <div>
          <h1>Gemini Chat</h1>
          <div class="small">Local • Chatbot-Project</div>
        </div>
      </div>

      <div class="controls">
        <button id="newChat" class="btn">+ New</button>
        <button id="exportBtn" class="btn">Export</button>
        <button id="clearBtn" class="btn">Clear</button>
      </div>

      <!-- Value proposition card with Key Benefits -->
      <div class="value-card" aria-label="Key Benefits">
        <h3>Key Benefits</h3>
        <ul>
          <li>24/7 automated support</li>
          <li>Faster response times</li>
          <li>Reduced manual workload</li>
          <li>Scalable & customizable conversational flows</li>
          <li>Integration with website, WhatsApp, CRM, etc.</li>
        </ul>
      </div>

      <!-- Integrations block -->
      <div class="integrations" aria-label="Integrations">
        <h4>Integrations</h4>
        <div class="integration-item">Website widget (JS)</div>
        <div class="integration-item">WhatsApp (Twilio)</div>
        <div class="integration-item">CRM (Zendesk / HubSpot)</div>
        <div class="integration-item">Internal API / Webhooks</div>
      </div>

      <div style="margin-top:10px;font-size:13px;color:var(--muted)">Conversations</div>
      <div class="sessions" id="sessions" aria-live="polite"></div>

      <div class="footer-note">Tip: Ctrl+Enter to send • Enter = newline</div>
    </aside>

    <main class="chat-wrap" aria-live="polite">
      <div class="chat-header">
        <div class="chat-title">
          <div class="avatar">AI</div>
          <div>
            <div style="font-weight:700">Gemini Chatbot</div>
            <div class="model-tag">Model: gemini-2.5-flash</div>
          </div>
        </div>
        <div class="row-right">
          <button id="themeBtn" class="btn">Toggle Theme</button>
        </div>
      </div>

      <div class="messages" id="messages" role="log" aria-live="polite" aria-atomic="false"></div>

      <div class="composer" role="region" aria-label="Message composer">
        <textarea id="input" class="input" placeholder="Type your message..."></textarea>
        <div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end">
          <button id="send" class="btn primary">Send</button>
          <div style="font-size:12px;color:var(--muted)">Session: <span id="sessionId" class="small"></span></div>
        </div>
      </div>
    </main>
  </div>

<script>
/* UI + client logic */
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const sessionsEl = document.getElementById('sessions');
const newChatBtn = document.getElementById('newChat');
const exportBtn = document.getElementById('exportBtn');
const clearBtn = document.getElementById('clearBtn');
const themeBtn = document.getElementById('themeBtn');
const sessionLabel = document.getElementById('sessionId');

let sessionId = localStorage.getItem('session_active') || 'local-' + Date.now();
sessionLabel.textContent = sessionId;
let sessions = JSON.parse(localStorage.getItem('session_list') || '{}');

// helper to render sessions
function renderSessions() {
  sessionsEl.innerHTML = '';
  const keys = Object.keys(sessions).sort((a,b)=>sessions[a].last - sessions[b].last).reverse();
  if(keys.length === 0) {
    const el = document.createElement('div'); el.className='small'; el.textContent='No conversations yet'; sessionsEl.appendChild(el);
    return;
  }
  keys.forEach(k=>{
    const s = document.createElement('div');
    s.className = 'session' + (k===sessionId ? ' active' : '');
    s.innerHTML = `<div style="flex:1"><div style="font-weight:600">${k}</div><div class="meta">${sessions[k].count} messages • ${new Date(sessions[k].last).toLocaleString()}</div></div>`;
    s.onclick = ()=>{ sessionId = k; sessionLabel.textContent = sessionId; localStorage.setItem('session_active', sessionId); renderSessions(); loadHistory(k); };
    sessionsEl.appendChild(s);
  });
}

// load conversation history into messages view
function loadHistory(sid) {
  messagesEl.innerHTML = '';
  const hist = sessions[sid] && sessions[sid].history ? sessions[sid].history : [];
  hist.forEach(m => {
    addBubble(m.role, m.text, m.ts);
  });
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// UI bubble creation
function addBubble(role, text, ts=null, opts={}) {
  const row = document.createElement('div');
  row.className = 'msg-row ' + (role==='user' ? 'user' : 'bot');
  const bubble = document.createElement('div');
  bubble.className = 'bubble ' + (role==='user' ? 'user' : 'bot');
  bubble.innerHTML = `<div>${escapeHtml(text)}</div><div class="meta-time">${ts ? new Date(ts).toLocaleTimeString() : new Date().toLocaleTimeString()}</div>`;
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

// small escape
function escapeHtml(str){ return String(str).replace(/[&<>"'`]/g, s=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;','`':'&#96;'})[s]); }

// persist message to sessions structure
function persistMessage(sid, role, text) {
  if(!sessions[sid]) sessions[sid] = { history: [], last: Date.now(), count: 0 };
  sessions[sid].history.push({ role, text, ts: Date.now() });
  sessions[sid].last = Date.now();
  sessions[sid].count = sessions[sid].history.length;
  localStorage.setItem('session_list', JSON.stringify(sessions));
  renderSessions();
}

// function to show typing skeleton
function showTyping() {
  const row = document.createElement('div'); row.className = 'msg-row'; row.id = 'typingRow';
  row.innerHTML = '<div class="bubble bot"><div><em>Typing…</em></div></div>';
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
function hideTyping(){ const r = document.getElementById('typingRow'); if(r) r.remove(); }

// send message to backend
async function sendMessage() {
  const text = inputEl.value.trim();
  if(!text) return;
  addBubble('user', text);
  persistMessage(sessionId, 'user', text);
  inputEl.value = '';
  showTyping();

  try{
    const res = await fetch('/chat', {
      method:'POST',
      headers:{ 'Content-Type':'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: text })
    });
    const json = await res.json();
    hideTyping();
    if(res.ok){
      addBubble('assistant', json.reply || '(no reply)');
      persistMessage(sessionId, 'assistant', json.reply || '');
    } else {
      addBubble('assistant', 'Error: ' + (json.error || JSON.stringify(json)));
      persistMessage(sessionId, 'assistant', 'Error: ' + (json.error || JSON.stringify(json)));
    }
  } catch(err){
    hideTyping();
    addBubble('assistant', 'Network error: ' + err.message);
    persistMessage(sessionId, 'assistant', 'Network error: ' + err.message);
  }
}

// initial setup
(function init(){
  // ensure session entry exists
  if(!sessions[sessionId]) sessions[sessionId] = { history: [], last: Date.now(), count:0 };
  localStorage.setItem('session_list', JSON.stringify(sessions));
  renderSessions();
  loadHistory(sessionId);

  // handlers
  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', (e)=>{
    if(e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault(); sendMessage();
    }
  });
  newChatBtn.onclick = ()=>{
    const sid = 'local-' + Date.now();
    sessionId = sid; sessions[sid] = { history: [], last: Date.now(), count:0 };
    localStorage.setItem('session_list', JSON.stringify(sessions));
    localStorage.setItem('session_active', sessionId);
    renderSessions(); loadHistory(sessionId);
  };
  exportBtn.onclick = ()=>{
    const data = sessions[sessionId] || { history: [] };
    const blob = new Blob([JSON.stringify(data.history, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = sessionId + '.json'; a.click(); URL.revokeObjectURL(url);
  };
  clearBtn.onclick = ()=>{
    if(confirm('Clear this conversation?')) {
      sessions[sessionId] = { history: [], last: Date.now(), count:0 };
      localStorage.setItem('session_list', JSON.stringify(sessions));
      loadHistory(sessionId);
      renderSessions();
    }
  };
  themeBtn.onclick = ()=>{
    document.documentElement.style.filter = document.documentElement.style.filter ? '' : 'brightness(1.03) saturate(1.05)';
  };
})();
</script>
</body>
</html>
"""

# -----------------------------
# Server routes
# -----------------------------
def build_prompt(history, new_message):
    """Simple chat prompt builder matching UI style."""
    lines = []
    for turn in history:
        r = turn.get("role", "user")
        txt = turn.get("text", "")
        if r == "user":
            lines.append(f"User: {txt}")
        else:
            lines.append(f"Assistant: {txt}")
    lines.append(f"User: {new_message}")
    lines.append("Assistant:")
    return "\n".join(lines)

@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_HTML)

@app.route("/chat", methods=["POST"])
def chat():
    payload = request.json or {}
    session_id = payload.get("session_id")
    message = (payload.get("message") or "").strip()
    if not session_id or not message:
        return jsonify({"error":"session_id and message required"}), 400

    # append to in-memory history (simple)
    history = SESSIONS.setdefault(session_id, [])
    # store minimal structure
    history.append({"role":"user","text":message,"ts": datetime.utcnow().isoformat()})

    prompt = build_prompt(history, message)

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
    except Exception as e:
        return jsonify({"error":"Gemini API error","details": str(e)}), 500

    reply = getattr(response, "text", None) or str(response)
    history.append({"role":"assistant","text": reply, "ts": datetime.utcnow().isoformat()})

    return jsonify({"reply": reply, "session_id": session_id})

@app.route("/reset", methods=["POST"])
def reset():
    sid = request.json.get("session_id")
    if sid in SESSIONS:
        SESSIONS.pop(sid, None)
    return jsonify({"ok": True})

if __name__ == "__main__":
    print("🚀 Gemini Chatbot (rich UI) running at http://127.0.0.1:5000")
    app.run(debug=True)
