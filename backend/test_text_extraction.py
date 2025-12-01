from lxml import html

def extract_text_with_spacing(element):
    """Extract text preserving some layout (newlines for br and block elements)."""
    text = []
    
    def _process(node):
        if node.text:
            text.append(node.text)
        
        for child in node:
            if child.tag == 'br':
                text.append('\n')
            elif child.tag in ['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr']:
                text.append('\n')
                _process(child)
                text.append('\n')
            else:
                _process(child)
            
            if child.tail:
                text.append(child.tail)
                
    _process(element)
    return "".join(text).strip()

# Test cases
cases = [
    '<p>Line1<br>Line2</p>',
    '<div><p>Para1</p><p>Para2</p></div>',
    '<li><p>Title</p>Content</li>',
    '<p>Text <span>Span</span> More</p>'
]

for c in cases:
    t = html.fromstring(c)
    print(f"HTML: {c}")
    print(f"Result: {repr(extract_text_with_spacing(t))}")
    print("-" * 20)
