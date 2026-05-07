import argparse
import os
import random
import re
import string

import pygments
from flask import Flask, abort, redirect, request, send_from_directory, url_for
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer
from werkzeug.utils import secure_filename

app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("root_dir", help="Path to directory with pastes")
args = parser.parse_args()

SLUG_CHARS = string.ascii_lowercase + string.digits
SLUG_LEN = 4
MAX_SLUG_GENERATION_ATTEMPTS = 256
MAX_CONTENT_BYTES = 1024 * 1024       # 1 MB for text pastes
MAX_UPLOAD_BYTES = 5 * 1024 * 1024    # 5 MB for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'pdf'}
# Extensions that should never appear anywhere in an uploaded filename
DANGEROUS_EXTENSIONS = {
    'php', 'php3', 'php4', 'php5', 'phtml', 'asp', 'aspx', 'jsp',
    'cgi', 'pl', 'py', 'rb', 'sh', 'bash', 'exe', 'bat', 'cmd', 'ps1',
}

app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_BYTES

UPLOAD_FORM = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fiche Pastebin</title>
  <style>
    body { font-family: monospace; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #1e1e1e; color: #d4d4d4; }
    h1 { color: #9cdcfe; }
    h2 { color: #9cdcfe; font-size: 16px; margin-top: 30px; }
    textarea { width: 100%; height: 300px; background: #252526; color: #d4d4d4; border: 1px solid #444; padding: 10px; font-family: monospace; font-size: 14px; box-sizing: border-box; }
    input[type=submit] { margin-top: 10px; padding: 8px 20px; background: #0e639c; color: #fff; border: none; cursor: pointer; font-size: 14px; }
    input[type=submit]:hover { background: #1177bb; }
    input[type=file] { margin-top: 8px; color: #d4d4d4; }
    p { color: #888; font-size: 13px; }
    hr { border: none; border-top: 1px solid #444; margin: 30px 0; }
  </style>
</head>
<body>
  <h1>Fiche Pastebin</h1>
  <h2>Text paste</h2>
  <p>Paste your text below and click <strong>Submit</strong> to get a shareable URL.<br>
     You can also use <code>cat file.txt | nc &lt;host&gt; 9999</code> from the command line.</p>
  <form method="POST" action="/submit">
    <textarea name="content" placeholder="Paste your text here..."></textarea><br>
    <input type="submit" value="Submit">
  </form>
  <hr>
  <h2>File upload</h2>
  <p>Upload an image or PDF (max 5 MB). Allowed types: png, jpg, jpeg, gif, webp, bmp, svg, pdf.</p>
  <form method="POST" action="/upload" enctype="multipart/form-data">
    <input type="file" name="file" accept=".png,.jpg,.jpeg,.gif,.webp,.bmp,.svg,.pdf"><br>
    <input type="submit" value="Upload">
  </form>
</body>
</html>"""


def allowed_file(filename):
    if '.' not in filename:
        return False
    parts = filename.split('.')
    base, ext = parts[0], parts[-1].lower()
    if not base:
        return False
    # Reject if any component of the filename is a dangerous extension
    if any(p.lower() in DANGEROUS_EXTENSIONS for p in parts[1:]):
        return False
    return ext in ALLOWED_EXTENSIONS


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


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part in the request.', 400

    file = request.files['file']

    if file.filename == '':
        return 'No selected file.', 400

    if not allowed_file(file.filename):
        return 'File type not allowed.', 400

    filename = secure_filename(file.filename)
    if not filename or not allowed_file(filename):
        return 'Invalid filename.', 400

    root = os.path.abspath(args.root_dir)
    os.makedirs(root, exist_ok=True)

    slug = generate_slug()
    if slug is None:
        return 'Could not generate a unique slug. Try again.', 500

    paste_dir = os.path.join(root, slug)
    os.makedirs(paste_dir)

    file_path = os.path.join(paste_dir, filename)
    file.save(file_path)

    meta_path = os.path.join(paste_dir, 'meta.txt')
    with open(meta_path, 'w') as f:
        f.write(f'original_filename={filename}\n')

    return redirect(url_for('view_paste', slug=slug), code=302)


@app.route('/<slug>')
def view_paste(slug):
    # Validate slug to only contain safe generated characters
    if not re.fullmatch(r'[a-z0-9]{1,64}', slug):
        abort(404)

    root = os.path.abspath(args.root_dir)

    # Create path for the target dir
    target_dir = os.path.join(root, slug)

    # Block directory traversal attempts
    if not os.path.abspath(target_dir).startswith(root + os.sep):
        abort(404)

    # Check if directory with requested slug exists
    if not os.path.isdir(target_dir):
        abort(404)

    text_file = os.path.join(target_dir, 'index.txt')
    if os.path.isfile(text_file):
        # File index.txt found inside that dir
        with open(text_file) as f:
            code = f.read()
        # Identify language
        lexer = guess_lexer(code)
        # Create formatter with line numbers
        formatter = HtmlFormatter(linenos=True, full=True)
        # Return parsed code
        return highlight(code, lexer, formatter)

    # Try to serve an uploaded file
    meta_file = os.path.join(target_dir, 'meta.txt')
    if os.path.isfile(meta_file):
        filename = None
        with open(meta_file) as f:
            for line in f:
                if line.startswith('original_filename='):
                    filename = line.split('=', 1)[1].strip()
                    break
        # filename was already sanitized with secure_filename at upload time;
        # re-validate defensively in case meta.txt is tampered with
        if filename:
            safe = secure_filename(filename)
            if safe and allowed_file(safe) and os.path.isfile(os.path.join(target_dir, safe)):
                return send_from_directory(target_dir, safe)

    # Not found
    abort(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
