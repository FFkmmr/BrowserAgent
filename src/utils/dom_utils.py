"""
Утилиты для работы с DOM
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag


def simplify_dom(html: str, max_depth: int = 5) -> str:
    """
    Упрощает DOM для подачи в LLM
    Удаляет лишние элементы, оставляет только важное
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # Удаляем ненужные теги
    for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
        tag.decompose()
    
    # Удаляем комментарии
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
        comment.extract()
    
    # Удаляем hidden элементы
    for tag in soup.find_all(style=lambda value: value and 'display:none' in value.replace(' ', '')):
        tag.decompose()
    
    for tag in soup.find_all(hidden=True):
        tag.decompose()
    
    return str(soup)


def extract_interactive_elements(html: str) -> List[Dict[str, Any]]:
    """
    Извлекает интерактивные элементы со страницы
    """
    soup = BeautifulSoup(html, 'lxml')
    elements = []
    
    # Buttons
    for idx, button in enumerate(soup.find_all(['button', 'input'])):
        if button.name == 'input' and button.get('type') not in ['button', 'submit', 'reset']:
            continue
        
        elements.append({
            'type': 'button',
            'id': f'btn_{idx}',
            'text': button.get_text(strip=True)[:100],
            'selector': generate_selector(button),
            'aria_label': button.get('aria-label', ''),
        })
    
    # Links
    for idx, link in enumerate(soup.find_all('a', href=True)):
        elements.append({
            'type': 'link',
            'id': f'link_{idx}',
            'text': link.get_text(strip=True)[:100],
            'href': link['href'],
            'selector': generate_selector(link),
        })
    
    # Inputs
    for idx, input_elem in enumerate(soup.find_all('input')):
        input_type = input_elem.get('type', 'text')
        if input_type in ['text', 'email', 'password', 'search', 'tel', 'url']:
            elements.append({
                'type': 'input',
                'id': f'input_{idx}',
                'input_type': input_type,
                'name': input_elem.get('name', ''),
                'placeholder': input_elem.get('placeholder', ''),
                'selector': generate_selector(input_elem),
            })
    
    # Select
    for idx, select in enumerate(soup.find_all('select')):
        options = [opt.get_text(strip=True) for opt in select.find_all('option')]
        elements.append({
            'type': 'select',
            'id': f'select_{idx}',
            'name': select.get('name', ''),
            'options': options[:10],  # Ограничиваем количество опций
            'selector': generate_selector(select),
        })
    
    return elements


def generate_selector(element: Tag) -> str:
    """
    Генерирует CSS селектор для элемента
    Приоритет: id > data-testid > aria-label > class + tag
    """
    # 1. Если есть id
    if element.get('id'):
        return f"#{element['id']}"
    
    # 2. Если есть data-testid
    if element.get('data-testid'):
        return f"[data-testid='{element['data-testid']}']"
    
    # 3. Если есть aria-label
    if element.get('aria-label'):
        return f"{element.name}[aria-label='{element['aria-label']}']"
    
    # 4. Если есть name
    if element.get('name'):
        return f"{element.name}[name='{element['name']}']"
    
    # 5. Комбинация тега и класса
    classes = element.get('class', [])
    if classes:
        class_str = '.'.join(classes[:2])  # Берём первые 2 класса
        return f"{element.name}.{class_str}"
    
    # 6. Просто тег (последний вариант)
    return element.name


def clean_text(text: str) -> str:
    """Очистка текста от лишних пробелов и символов"""
    return ' '.join(text.split())
