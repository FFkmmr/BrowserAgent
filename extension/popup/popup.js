/**
 * Popup UI Script
 */

// DOM элементы
const taskInput = document.getElementById('taskInput');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusEl = document.getElementById('status');
const backendStatusEl = document.getElementById('backendStatus');
const currentTaskEl = document.getElementById('currentTask');

// Состояние
let agentState = {
  isRunning: false,
  currentTask: null,
  websocketConnected: false
};

// Обновление UI
function updateUI() {
  // Статус
  if (agentState.isRunning) {
    statusEl.textContent = '🚀 Выполняется';
    statusEl.className = 'status running';
    startBtn.disabled = true;
    stopBtn.disabled = false;
    taskInput.disabled = true;
  } else {
    statusEl.textContent = '⏸️ Ожидание';
    statusEl.className = 'status idle';
    startBtn.disabled = false;
    stopBtn.disabled = true;
    taskInput.disabled = false;
  }
  
  // Backend статус
  if (agentState.websocketConnected) {
    backendStatusEl.textContent = '✅ Подключен';
  } else {
    backendStatusEl.textContent = '❌ Не подключен';
  }
  
  // Текущая задача
  if (agentState.currentTask) {
    currentTaskEl.textContent = agentState.currentTask.substring(0, 50) + '...';
  } else {
    currentTaskEl.textContent = 'Нет';
  }
}

// Запрос текущего состояния
function fetchState() {
  chrome.runtime.sendMessage({ type: 'get_state' }, (response) => {
    if (response && response.state) {
      agentState = response.state;
      updateUI();
    }
  });
}

// Запуск задачи
startBtn.addEventListener('click', () => {
  const task = taskInput.value.trim();
  
  if (!task) {
    alert('Пожалуйста, введите описание задачи');
    return;
  }
  
  chrome.runtime.sendMessage({
    type: 'start_task',
    task: task
  }, (response) => {
    if (response.success) {
      agentState.isRunning = true;
      agentState.currentTask = task;
      updateUI();
    }
  });
});

// Остановка задачи
stopBtn.addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'stop_task' }, (response) => {
    if (response.success) {
      agentState.isRunning = false;
      agentState.currentTask = null;
      updateUI();
    }
  });
});

// Примеры задач
document.querySelectorAll('.example-link').forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    taskInput.value = e.target.dataset.task;
  });
});

// Прослушивание обновлений состояния
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'state_update') {
    agentState = message.state;
    updateUI();
  }
});

// Инициализация
fetchState();
setInterval(fetchState, 2000); // Обновление каждые 2 секунды
