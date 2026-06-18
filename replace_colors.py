import re

# Update style.css
with open('static/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

css = css.replace('#ff6600', '#d500f9')
css = css.replace('255,102,0', '213,0,249')
css = css.replace('255, 102, 0', '213, 0, 249')

# Body background
css = re.sub(r'linear-gradient\(135deg, #0a0a0a 0%, #1f0f00 50%, #050505 100%\)', 'linear-gradient(135deg, #2b0057 0%, #1a0033 50%, #3a0062 100%)', css)

# Nav background
css = css.replace('background: #0b0f19;', 'background: #1a0033;')
css = css.replace('border-bottom: 2px solid #d500f9;', 'border-bottom: 2px solid #8e24aa;')

# Form card
css = re.sub(r'background: transparent;\s*border: 1px solid rgba\(255, 255, 255, 0.1\);', 'background: rgba(45, 0, 75, 0.6);\n  border: 1px solid rgba(213, 0, 249, 0.3);', css)

with open('static/style.css', 'w', encoding='utf-8') as f:
    f.write(css)

# Update index.html
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace SVG fills and strokes in nav
html = html.replace('fill=\"#170500\" stroke=\"#ff6600\"', 'fill=\"#ce93d8\" stroke=\"none\"')
html = html.replace('fill=\"#170500\" stroke=\"#d500f9\"', 'fill=\"#ce93d8\" stroke=\"none\"')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Done')
