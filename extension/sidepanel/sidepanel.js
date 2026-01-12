const chatEl = document.getElementById('chat');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const stopBtn = document.getElementById('stop');
const backendStatusEl = document.getElementById('backendStatus');
const agentStatusEl = document.getElementById('agentStatus');

let state = {
  isRunning: false,
  currentTask: null,
  websocketConnected: false,
};

function appendMessage(role, text) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setPill(el, text, ok = null) {
  el.textContent = text;
  el.style.borderColor = ok === null ? 'var(--border)' : ok ? 'rgba(92,255,168,0.35)' : 'rgba(255,92,92,0.35)';
}

function updateUI() {
  setPill(
    backendStatusEl,
    state.websocketConnected ? 'Backend: подключен' : 'Backend: не подключен',
    state.websocketConnected
  );
  setPill(
    agentStatusEl,
    state.isRunning ? 'Agent: работает' : 'Agent: ожидание',
    !state.isRunning
  );

  sendBtn.disabled = state.isRunning;
  stopBtn.disabled = !state.isRunning;
  inputEl.disabled = state.isRunning;
}

function fetchState() {
  chrome.runtime.sendMessage({ type: 'get_state' }, (response) => {
    if (response && response.state) {
      state = {
        isRunning: !!response.state.isRunning,
        currentTask: response.state.currentTask || null,
        websocketConnected: !!response.state.websocketConnected,
      };
      updateUI();
    }
  });
}

function sendTask(text) {
  chrome.runtime.sendMessage({ type: 'chat_message', text }, (response) => {
    if (response && response.success) {
      appendMessage('user', text);
      inputEl.value = '';
      fetchState();
    }
  });
}

sendBtn.addEventListener('click', () => {
  const text = (inputEl.value || '').trim();
  if (!text) return;
  sendTask(text);
});

inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    sendBtn.click();
  }
});

stopBtn.addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'stop_task' }, () => fetchState());
});

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'state_update') {
    state = {
      isRunning: !!message.state.isRunning,
      currentTask: message.state.currentTask || null,
      websocketConnected: !!message.state.websocketConnected,
    };
    updateUI();
    return;
  }

  if (message.type === 'backend_event') {
    const payload = message.payload || {};

    if (payload.type === 'task_started') {
      appendMessage('system', `Задача запущена: ${payload.task}`);
      return;
    }

    if (payload.type === 'task_completed') {
      appendMessage('assistant', `Готово.\n\nРезультат:\n${payload.result}`);
      return;
    }

    if (payload.type === 'task_failed') {
      appendMessage('assistant', `Ошибка: ${payload.error || payload.result || 'unknown'}`);
      return;
    }

    if (payload.type === 'agent_message') {
      appendMessage(payload.role || 'assistant', payload.text || '');
      return;
    }
  }
});

appendMessage('system', 'Открой боковую панель и запусти backend: python run_backend.py');
fetchState();
setInterval(fetchState, 2000);
