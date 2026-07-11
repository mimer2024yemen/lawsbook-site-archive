from __future__ import annotations
import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_BASE = "/lawsbook-site-archive"


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def copy(src: Path, dst: Path):
    ensure_parent(dst)
    shutil.copy2(src, dst)


def sanitize_query_filename(name: str) -> str:
    name = name.replace('?', '__').replace('&', '_').replace('=', '-').replace(':', '-')
    name = name.replace(';', '_').replace('%', '_').replace('+', '_').replace('@', '_')
    return name


def remove_lovable(html_text: str) -> str:
    html_text = re.sub(r'<script defer src="~flock\.js"[^>]*></script>', '', html_text)
    html_text = re.sub(r'<script defer src="__l5e/events\.js"[^>]*></script>', '', html_text)
    html_text = re.sub(r'<aside\s+id="lovable-badge"[\s\S]*?</script>\s*</body>', '</body>', html_text, count=1)
    return html_text


# 1) Flatten/copy assets that were mirrored with query-string file names.
asset_replacements: list[tuple[str, str]] = []

# pravatar
for src in sorted((ROOT / 'i.pravatar.cc' / 'i.pravatar.cc').glob('*')):
    if not src.is_file() or src.name == 'robots.txt':
        continue
    new_name = sanitize_query_filename(src.name) + '.jpg'
    dst = ROOT / 'i.pravatar.cc' / new_name
    copy(src, dst)
    old_raw = f'i.pravatar.cc/{src.name}'
    old_enc = old_raw.replace('?', '%3F').replace('&', '&amp;')
    new_url = f'{REPO_BASE}/i.pravatar.cc/{new_name}'
    asset_replacements.extend([(old_raw, new_url), (old_enc, new_url)])

# unsplash
for src in sorted((ROOT / 'images.unsplash.com' / 'images.unsplash.com').glob('*')):
    if not src.is_file() or src.name == 'robots.txt':
        continue
    new_name = sanitize_query_filename(src.name) + '.jpg'
    dst = ROOT / 'images.unsplash.com' / new_name
    copy(src, dst)
    old_raw = f'images.unsplash.com/{src.name}'
    old_enc = old_raw.replace('?', '%3F').replace('&', '&amp;')
    new_url = f'{REPO_BASE}/images.unsplash.com/{new_name}'
    asset_replacements.extend([(old_raw, new_url), (old_enc, new_url)])

# fonts google css
for src in sorted((ROOT / 'fonts.googleapis.com' / 'fonts.googleapis.com').glob('*')):
    if not src.is_file() or src.name == 'robots.txt':
        continue
    if src.suffix == '.css':
        dst = ROOT / 'fonts.googleapis.com' / 'css2-tajawal-amiri.css'
        text = src.read_text('utf-8', errors='ignore')
        text = text.replace('../fonts.gstatic.com/', f'{REPO_BASE}/fonts.gstatic.com/')
        ensure_parent(dst)
        dst.write_text(text, encoding='utf-8')
        old_raw = f'fonts.googleapis.com/{src.name}'
        old_enc = old_raw.replace('?', '%3F').replace('&', '&amp;')
        new_url = f'{REPO_BASE}/fonts.googleapis.com/{dst.name}'
        asset_replacements.extend([(old_raw, new_url), (old_enc, new_url)])

# fonts gstatic flatten
for src in sorted((ROOT / 'fonts.gstatic.com' / 'fonts.gstatic.com').rglob('*')):
    if src.is_file():
        rel = src.relative_to(ROOT / 'fonts.gstatic.com' / 'fonts.gstatic.com')
        dst = ROOT / 'fonts.gstatic.com' / rel
        copy(src, dst)

# cdn.gpteng flatten
for src in sorted((ROOT / 'cdn.gpteng.co' / 'cdn.gpteng.co').rglob('*')):
    if src.is_file():
        rel = src.relative_to(ROOT / 'cdn.gpteng.co' / 'cdn.gpteng.co')
        dst = ROOT / 'cdn.gpteng.co' / rel
        copy(src, dst)

# robots copies
for host in ['i.pravatar.cc', 'images.unsplash.com', 'fonts.googleapis.com']:
    nested = ROOT / host / host / 'robots.txt'
    if nested.exists():
        copy(nested, ROOT / host / 'robots.txt')


# 2) Route/page directory structure for static hosting.
route_pages = {
    'explore.html': 'explore/index.html',
    'library.html': 'library/index.html',
    'messages.html': 'messages/index.html',
    'notifications.html': 'notifications/index.html',
    'profile.html': 'profile/index.html',
    'reels.html': 'reels/index.html',
    'settings.html': 'settings/index.html',
    'create.html': 'create/index.html',
    'profile/edit.html': 'profile/edit/index.html',
}
for src_rel, dst_rel in route_pages.items():
    src = ROOT / src_rel
    dst = ROOT / dst_rel
    copy(src, dst)

for src in sorted((ROOT / 'read').glob('*.html')):
    copy(src, ROOT / 'read' / src.stem / 'index.html')
for src in sorted((ROOT / 'u').glob('*.html')):
    copy(src, ROOT / 'u' / src.stem / 'index.html')
for src in sorted((ROOT / 'post').glob('*.html')):
    # p2?c=c3.html => post/p2/index.html
    post_id = src.name.split('?')[0].split('.')[0]
    dst = ROOT / 'post' / post_id / 'index.html'
    if not dst.exists():
        copy(src, dst)

# dedicated create/book route
book_src = ROOT / 'create?type=book.html'
if book_src.exists():
    copy(book_src, ROOT / 'create' / 'book' / 'index.html')

# root index for project root path
copy(ROOT / 'index.html', ROOT / '404.html')

# 3) Text replacements across html/css/js.
text_files = [*ROOT.rglob('*.html'), *ROOT.rglob('*.css'), *ROOT.rglob('*.js')]

# Route replacements in HTML and JS.
replacements = {
    'href="index.html"': f'href="{REPO_BASE}/"',
    'href="explore.html"': f'href="{REPO_BASE}/explore/"',
    'href="library.html"': f'href="{REPO_BASE}/library/"',
    'href="messages.html"': f'href="{REPO_BASE}/messages/"',
    'href="notifications.html"': f'href="{REPO_BASE}/notifications/"',
    'href="profile.html"': f'href="{REPO_BASE}/profile/"',
    'href="reels.html"': f'href="{REPO_BASE}/reels/"',
    'href="settings.html"': f'href="{REPO_BASE}/settings/"',
    'href="create.html"': f'href="{REPO_BASE}/create/"',
    'href="profile/edit.html"': f'href="{REPO_BASE}/profile/edit/"',
    'href="create?type=book.html"': f'href="{REPO_BASE}/create/book/"',
    'href="post/p2?c=c3.html"': f'href="{REPO_BASE}/post/p2/?c=c3"',
    'href="post/p2?c=c4.html"': f'href="{REPO_BASE}/post/p2/?c=c4"',
    'href="post/p5?c=c7.html"': f'href="{REPO_BASE}/post/p5/?c=c7"',
    'href="post/p9?c=c11.html"': f'href="{REPO_BASE}/post/p9/?c=c11"',
    'href="u/': f'href="{REPO_BASE}/u/',
    'href="read/': f'href="{REPO_BASE}/read/',
    '.html"': '/"',
    'src: url(../fonts.gstatic.com/': f'src: url({REPO_BASE}/fonts.gstatic.com/',
    "src: url('../../cdn.gpteng.co/": f"src: url('{REPO_BASE}/cdn.gpteng.co/",
    "src: url('../cdn.gpteng.co/": f"src: url('{REPO_BASE}/cdn.gpteng.co/",
}

js_route_map = {
    '"/explore"': f'"{REPO_BASE}/explore/"',
    '"/library"': f'"{REPO_BASE}/library/"',
    '"/messages"': f'"{REPO_BASE}/messages/"',
    '"/notifications"': f'"{REPO_BASE}/notifications/"',
    '"/profile/edit"': f'"{REPO_BASE}/profile/edit/"',
    '"/profile/"': f'"{REPO_BASE}/profile/"',
    '"/profile"': f'"{REPO_BASE}/profile/"',
    '"/reels"': f'"{REPO_BASE}/reels/"',
    '"/settings"': f'"{REPO_BASE}/settings/"',
    '"/create"': f'"{REPO_BASE}/create/"',
    '"/admin"': f'"{REPO_BASE}/admin/"',
    '"/read/$docId"': f'"{REPO_BASE}/read/$docId/"',
    '"/u/$handle"': f'"{REPO_BASE}/u/$handle/"',
    '"/post/$postId"': f'"{REPO_BASE}/post/$postId/"',
}

# exact user/profile/read clean URL completions in hrefs generated from HTML copies
entity_route_suffixes = [
    '/u/abdulmalik_hameed', '/u/ahmed_m', '/u/ayman_judge', '/u/basem_contracts', '/u/fares_policy',
    '/u/hind_privacy', '/u/jana_copyright', '/u/khaled_h', '/u/layla_docs', '/u/nour_ai', '/u/reem_books',
    '/u/salman_lib', '/u/sara_law', '/u/shahd_media', '/u/yousef_case',
    '/read/d1', '/read/d2', '/read/d3', '/read/d4', '/read/d5', '/read/d6', '/read/d7', '/read/d8'
]

for path in text_files:
    text = path.read_text('utf-8', errors='ignore')
    orig = text
    if path.suffix == '.html':
        text = remove_lovable(text)
        # make common nav routes absolute to repo base
        text = text.replace('href="explore/"', f'href="{REPO_BASE}/explore/"')
        text = text.replace('href="library/"', f'href="{REPO_BASE}/library/"')
        text = text.replace('href="messages/"', f'href="{REPO_BASE}/messages/"')
        text = text.replace('href="notifications/"', f'href="{REPO_BASE}/notifications/"')
        text = text.replace('href="profile/"', f'href="{REPO_BASE}/profile/"')
        text = text.replace('href="reels/"', f'href="{REPO_BASE}/reels/"')
        text = text.replace('href="settings/"', f'href="{REPO_BASE}/settings/"')
        text = text.replace('href="create/"', f'href="{REPO_BASE}/create/"')
        text = text.replace('href="profile/edit/"', f'href="{REPO_BASE}/profile/edit/"')
        # normalize generated entity pages if they ended with '/"' via generic replacement
        for suffix in entity_route_suffixes:
            text = text.replace(f'href="{REPO_BASE}{suffix}/"', f'href="{REPO_BASE}{suffix}/"')
    for old, new in asset_replacements:
        text = text.replace(old, new)
    for old, new in replacements.items():
        text = text.replace(old, new)
    if path.suffix == '.js':
        for old, new in js_route_map.items():
            text = text.replace(old, new)
        text = text.replace('"/_serverFn/"', '"/_serverFn/"')
    # Fix read and user hrefs after .html slash cleanup
    text = re.sub(rf'href="{re.escape(REPO_BASE)}/(u/[^"/]+)\.html"', rf'href="{REPO_BASE}/\1/"', text)
    text = re.sub(rf'href="{re.escape(REPO_BASE)}/(read/[^"/]+)\.html"', rf'href="{REPO_BASE}/\1/"', text)
    text = re.sub(rf'href="{re.escape(REPO_BASE)}/profile/edit\.html"', rf'href="{REPO_BASE}/profile/edit/"', text)
    text = re.sub(rf'href="{re.escape(REPO_BASE)}/([a-z-]+)\.html"', rf'href="{REPO_BASE}/\1/"', text)
    if text != orig:
        path.write_text(text, encoding='utf-8')

# 4) Improve 404 for GitHub Pages project routes.
redirect_404 = f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>إعادة التوجيه...</title>
  <script>
    (function() {{
      var base = '{REPO_BASE}';
      var path = window.location.pathname;
      if (path === base || path === base + '/') {{
        window.location.replace(base + '/');
        return;
      }}
      if (path.startsWith(base + '/')) {{
        var fixed = path.endsWith('/') ? path : path + '/';
        window.location.replace(fixed + window.location.search + window.location.hash);
        return;
      }}
      window.location.replace(base + '/');
    }})();
  </script>
</head>
<body>جاري إعادة التوجيه...</body>
</html>
'''
(ROOT / '404.html').write_text(redirect_404, encoding='utf-8')

# 5) Add GitHub Pages workflow.
workflow = ROOT / '.github' / 'workflows' / 'deploy-pages.yml'
ensure_parent(workflow)
workflow.write_text('''name: Deploy static site to GitHub Pages\n\non:\n  push:\n    branches: [main]\n  workflow_dispatch:\n\npermissions:\n  contents: read\n  pages: write\n  id-token: write\n\nconcurrency:\n  group: pages\n  cancel-in-progress: true\n\njobs:\n  deploy:\n    environment:\n      name: github-pages\n      url: ${{ steps.deployment.outputs.page_url }}\n    runs-on: ubuntu-latest\n    steps:\n      - name: Checkout\n        uses: actions/checkout@v4\n\n      - name: Setup Pages\n        uses: actions/configure-pages@v5\n\n      - name: Upload artifact\n        uses: actions/upload-pages-artifact@v3\n        with:\n          path: .\n\n      - name: Deploy to GitHub Pages\n        id: deployment\n        uses: actions/deploy-pages@v4\n''', encoding='utf-8')

# 6) Tiny deployment note.
(ROOT / 'DEPLOYMENT_NOTES.txt').write_text(
    'Static archive repaired for GitHub Pages project deployment under /lawsbook-site-archive/.\n'
    'Remaining limitations are documented by the assistant after verification.\n',
    encoding='utf-8'
)

print('Repair completed.')
