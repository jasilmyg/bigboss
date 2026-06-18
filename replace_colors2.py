with open('static/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

css = css.replace('--purple-dark:   #170500;', '--purple-dark:   #2a0040;')
css = css.replace('--purple-mid:    #2e0b00;', '--purple-mid:    #4a0072;')
css = css.replace('--purple-rich:   #6b1d00;', '--purple-rich:   #6a0dad;')
css = css.replace('--pink-hot:      #ff8800;', '--pink-hot:      #ff4081;')
css = css.replace('--pink-deep:     #cc3300;', '--pink-deep:     #c51162;')

with open('static/style.css', 'w', encoding='utf-8') as f:
    f.write(css)

print('Done 2')
