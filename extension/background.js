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

// Подключение к Python backend
function connectToBackend() {
  try {
    ws = new WebSocket('ws://localhost:8765');
    
    ws.onopen = () => {
      console.log('Connected to Python backend');
      agentState.websocketConnected = true;
      broadcastState();
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleBackendMessage(message);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      agentState.websocketConnected = false;
    };
    
    ws.onclose = () => {
      console.log('Disconnected from Python backend');
      agentState.websocketConnected = false;
      // Переподключение через 5 секунд
      setTimeout(connectToBackend, 5000);
    };
    
  } catch (error) {
    console.error('Failed to connect to backend:', error);
  }
}

// Обработка сообщений от Python backend
function handleBackendMessage(message) {
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
      startTask(message.task);
      sendResponse({ success: true });
      break;
      
    case 'get_state':
      sendResponse({ state: agentState });
      break;
      
    case 'stop_task':
      stopTask();
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
  // Попытка подключения к backend
  connectToBackend();
});

// Попытка подключения при старте
connectToBackend();
