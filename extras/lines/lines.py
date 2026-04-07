import argparse
import os
import random
import string

import pygments
from flask import Flask, abort, redirect, request
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer

app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("root_dir", help="Path to directory with pastes")
args = parser.parse_args()

SLUG_CHARS = string.ascii_lowercase + string.digits
SLUG_LEN = 4
MAX_SLUG_GENERATION_ATTEMPTS = 256
MAX_CONTENT_BYTES = 1024 * 1024  # 1 MB

UPLOAD_FORM = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fiche Pastebin</title>
  <style>
    body { font-family: monospace; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #1e1e1e; color: #d4d4d4; }
    h1 { color: #9cdcfe; }
    textarea { width: 100%; height: 300px; background: #252526; color: #d4d4d4; border: 1px solid #444; padding: 10px; font-family: monospace; font-size: 14px; box-sizing: border-box; }
    input[type=submit] { margin-top: 10px; padding: 8px 20px; background: #0e639c; color: #fff; border: none; cursor: pointer; font-size: 14px; }
    input[type=submit]:hover { background: #1177bb; }
    p { color: #888; font-size: 13px; }
  </style>
</head>
<body>
  <h1>Fiche Pastebin</h1>
  <p>Paste your text below and click <strong>Submit</strong> to get a shareable URL.<br>
     You can also use <code>cat file.txt | nc &lt;host&gt; 9999</code> from the command line.</p>
  <form method="POST" action="/submit">
    <textarea name="content" placeholder="Paste your text here..."></textarea><br>
    <input type="submit" value="Submit">
  </form>
</body>
</html>"""


def generate_slug():
    """Generate a unique slug that does not collide with an existing directory."""
    root = os.path.abspath(args.root_dir)
    for _ in range(MAX_SLUG_GENERATION_ATTEMPTS):
        slug = ''.join(random.choices(SLUG_CHARS, k=SLUG_LEN))
        target = os.path.join(root, slug)
        if not os.path.exists(target):
            return slug
    return None


@app.route('/')
def main():
    return UPLOAD_FORM


@app.route('/submit', methods=['POST'])
def submit():
    content = request.form.get('content', '')
    if not content.strip():
        return 'No content provided.', 400

    if len(content.encode('utf-8')) > MAX_CONTENT_BYTES:
        return 'Content exceeds maximum allowed size (1 MB).', 413

    root = os.path.abspath(args.root_dir)
    os.makedirs(root, exist_ok=True)

    slug = generate_slug()
    if slug is None:
        return 'Could not generate a unique slug. Try again.', 500

    paste_dir = os.path.join(root, slug)
    os.makedirs(paste_dir)

    paste_file = os.path.join(paste_dir, 'index.txt')
    with open(paste_file, 'w') as f:
        f.write(content)

    return redirect('/' + slug, code=302)


@app.route('/<slug>')
def beautify(slug):
    # Return 404 in case of urls longer than 64 chars
    if len(slug) > 64:
        abort(404)

    root = os.path.abspath(args.root_dir)

    # Create path for the target dir
    target_dir = os.path.join(root, slug)

    # Block directory traversal attempts
    if not os.path.abspath(target_dir).startswith(root):
        abort(404)

    # Check if directory with requested slug exists
    if os.path.isdir(target_dir):
        target_file = os.path.join(target_dir, 'index.txt')

        # File index.txt found inside that dir
        with open(target_file) as f:
            code = f.read()
            # Identify language
            lexer = guess_lexer(code)
            # Create formatter with line numbers
            formatter = HtmlFormatter(linenos=True, full=True)
            # Return parsed code
            return highlight(code, lexer, formatter)

    # Not found
    abort(404)


if __name__ == '__main__':
    app.run()
