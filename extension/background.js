/**
 * Background Service Worker для AI Browser Agent
 * Координирует работу расширения и связь с Python backend
 */

console.log('AI Browser Agent: Background service worker started');

// Состояние агента
let agentState = {
  isRunning: false,
  currentTask: null,
  websocketConnected: false
};

// WebSocket соединение с Python backend (опционально)
let ws = null;
let wsConnecting = false;

const WS_URL = 'ws://localhost:8765/ws';

// Подключение к Python backend
function connectToBackend() {
  if (wsConnecting) return;
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

  wsConnecting = true;
  try {
    ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
      console.log('Connected to Python backend');
      agentState.websocketConnected = true;
      wsConnecting = false;
      broadcastState();
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleBackendMessage(message);
    };
    
    ws.onerror = (error) => {
      // Don't spam extension error panel when backend isn't running.
      console.warn('WebSocket error:', error);
      agentState.websocketConnected = false;
      wsConnecting = false;
    };
    
    ws.onclose = () => {
      console.log('Disconnected from Python backend');
      agentState.websocketConnected = false;
      wsConnecting = false;
      // Переподключение через 5 секунд
      setTimeout(connectToBackend, 5000);
    };
    
  } catch (error) {
    console.warn('Failed to connect to backend:', error);
    wsConnecting = false;
  }
}

// Обработка сообщений от Python backend
function handleBackendMessage(message) {
  // Relay everything to sidepanel/popup UIs.
  chrome.runtime.sendMessage({ type: 'backend_event', payload: message });

  switch (message.type) {
    case 'task_started':
      agentState.isRunning = true;
      agentState.currentTask = message.task;
      broadcastState();
      break;
      
    case 'task_completed':
      agentState.isRunning = false;
      agentState.currentTask = null;
      broadcastState();
      break;

    case 'task_failed':
      agentState.isRunning = false;
      agentState.currentTask = null;
      broadcastState();
      break;
      
    case 'action_executed':
      // Действие выполнено, можно обновить UI
      broadcastState();
      break;
  }
}

// Отправка сообщения в Python backend
function sendToBackend(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  } else {
    // Attempt to connect and let UI show status.
    connectToBackend();
    console.warn('WebSocket not connected');
  }
}

// Broadcast состояния всем слушателям
function broadcastState() {
  chrome.runtime.sendMessage({
    type: 'state_update',
    state: agentState
  });
}

// Обработка сообщений от popup и content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Received message:', message);
  
  switch (message.type) {
    case 'start_task':
      connectToBackend();
      startTask(message.task);
      sendResponse({ success: true });
      break;
      
    case 'get_state':
      connectToBackend();
      sendResponse({ state: agentState });
      break;
      
    case 'stop_task':
      connectToBackend();
      stopTask();
      sendResponse({ success: true });
      break;

    case 'chat_message':
      connectToBackend();
      sendToBackend({ type: 'start_task', task: message.text });
      sendResponse({ success: true });
      break;
      
    default:
      sendResponse({ error: 'Unknown message type' });
  }
  
  return true; // Keep channel open for async response
});

// Запуск задачи
function startTask(taskDescription) {
  console.log('Starting task:', taskDescription);
  
  agentState.isRunning = true;
  agentState.currentTask = taskDescription;
  
  // Отправить задачу в Python backend
  sendToBackend({
    type: 'start_task',
    task: taskDescription
  });
  
  broadcastState();
}

// Остановка задачи
function stopTask() {
  console.log('Stopping task');
  
  agentState.isRunning = false;
  agentState.currentTask = null;
  
  sendToBackend({
    type: 'stop_task'
  });
  
  broadcastState();
}

// Инициализация при загрузке
chrome.runtime.onInstalled.addListener(() => {
  console.log('AI Browser Agent installed');
  // Side panel behavior
  if (chrome.sidePanel && chrome.sidePanel.setPanelBehavior) {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
  }
});

// Lazy connect: only connect when UI asks / task starts.
