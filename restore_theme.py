import re

# Update style.css
with open('static/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Reverse replacements
css = css.replace('#d500f9', '#ff6600')
css = css.replace('213,0,249', '255,102,0')
css = css.replace('213, 0, 249', '255, 102, 0')

# Body background
css = re.sub(r'linear-gradient\(135deg, #2b0057 0%, #1a0033 50%, #3a0062 100%\)', 'linear-gradient(135deg, #0a0a0a 0%, #1f0f00 50%, #050505 100%)', css)

# Nav background
css = css.replace('background: #1a0033;', 'background: #0b0f19;')
# The script previously replaced border-bottom: 2px solid #d500f9; with border-bottom: 2px solid #8e24aa;
css = css.replace('border-bottom: 2px solid #8e24aa;', 'border-bottom: 2px solid #ff6600;')

# Form card
css = re.sub(r'background: rgba\(45, 0, 75, 0\.6\);\s*border: 1px solid rgba\(213, 0, 249, 0\.3\);', 'background: transparent;\n  border: 1px solid rgba(255, 255, 255, 0.1);', css)

with open('static/style.css', 'w', encoding='utf-8') as f:
    f.write(css)

# Update index.html
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace SVG fills and strokes in nav (reverse)
html = html.replace('fill="#ce93d8" stroke="none"', 'fill="#170500" stroke="#ff6600"')
# Also fix the shape SVG stroke which was hardcoded
html = html.replace('stroke="#d500f9"', 'stroke="#ff6600"')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Done restoring theme')
