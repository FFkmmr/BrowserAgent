/**
 * Content Script для AI Browser Agent
 * Инжектируется в каждую страницу для выполнения действий
 */

console.log('AI Browser Agent: Content script loaded');

// Прослушивание команд от background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content script received:', message);
  
  switch (message.type) {
    case 'execute_action':
      executeAction(message.action)
        .then(result => sendResponse({ success: true, result }))
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true; // Async response
      
    case 'analyze_page':
      const pageInfo = analyzePage();
      sendResponse({ success: true, data: pageInfo });
      break;
      
    case 'highlight_element':
      highlightElement(message.selector);
      sendResponse({ success: true });
      break;
      
    default:
      sendResponse({ success: false, error: 'Unknown action' });
  }
  
  return true;
});

// Выполнение действия на странице
async function executeAction(action) {
  const { type, parameters } = action;
  
  switch (type) {
    case 'click':
      return await clickElement(parameters.selector);
      
    case 'type':
      return await typeText(parameters.selector, parameters.text);
      
    case 'extract_text':
      return extractText(parameters.selector);
      
    case 'scroll':
      return scrollPage(parameters.direction, parameters.amount);
      
    default:
      throw new Error(`Unknown action type: ${type}`);
  }
}

// Клик по элементу
async function clickElement(selector) {
  const element = document.querySelector(selector);
  if (!element) {
    throw new Error(`Element not found: ${selector}`);
  }
  
  element.click();
  return { clicked: true, selector };
}

// Ввод текста
async function typeText(selector, text) {
  const element = document.querySelector(selector);
  if (!element) {
    throw new Error(`Element not found: ${selector}`);
  }
  
  element.value = text;
  element.dispatchEvent(new Event('input', { bubbles: true }));
  return { typed: true, selector, text };
}

// Извлечение текста
function extractText(selector = 'body') {
  const element = document.querySelector(selector);
  if (!element) {
    throw new Error(`Element not found: ${selector}`);
  }
  
  return element.textContent.trim();
}

// Прокрутка страницы
function scrollPage(direction, amount = 500) {
  switch (direction) {
    case 'down':
      window.scrollBy(0, amount);
      break;
    case 'up':
      window.scrollBy(0, -amount);
      break;
    case 'top':
      window.scrollTo(0, 0);
      break;
    case 'bottom':
      window.scrollTo(0, document.body.scrollHeight);
      break;
  }
  
  return { scrolled: true, direction };
}

// Анализ страницы
function analyzePage() {
  return {
    url: window.location.href,
    title: document.title,
    interactiveElements: findInteractiveElements()
  };
}

// Поиск интерактивных элементов
function findInteractiveElements() {
  const elements = [];
  
  // Buttons
  document.querySelectorAll('button, input[type="button"], input[type="submit"]').forEach((el, idx) => {
    elements.push({
      type: 'button',
      text: el.textContent.trim() || el.value,
      selector: generateSelector(el)
    });
  });
  
  // Links
  document.querySelectorAll('a[href]').forEach((el, idx) => {
    if (idx < 20) { // Limit
      elements.push({
        type: 'link',
        text: el.textContent.trim(),
        href: el.href,
        selector: generateSelector(el)
      });
    }
  });
  
  // Inputs
  document.querySelectorAll('input[type="text"], input[type="email"], input[type="search"]').forEach((el, idx) => {
    elements.push({
      type: 'input',
      name: el.name,
      placeholder: el.placeholder,
      selector: generateSelector(el)
    });
  });
  
  return elements;
}

// Генерация селектора для элемента
function generateSelector(element) {
  if (element.id) return `#${element.id}`;
  if (element.name) return `[name="${element.name}"]`;
  if (element.className) {
    const classes = element.className.split(' ').filter(c => c).slice(0, 2);
    if (classes.length > 0) {
      return `${element.tagName.toLowerCase()}.${classes.join('.')}`;
    }
  }
  return element.tagName.toLowerCase();
}

// Подсветка элемента
function highlightElement(selector) {
  const element = document.querySelector(selector);
  if (!element) return;
  
  element.style.outline = '3px solid #ff6b6b';
  element.style.backgroundColor = 'rgba(255, 107, 107, 0.1)';
  
  setTimeout(() => {
    element.style.outline = '';
    element.style.backgroundColor = '';
  }, 2000);
}
