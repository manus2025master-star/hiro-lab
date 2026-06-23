#!/usr/bin/env python3
"""
hiro-lab site rebuild:
- 1) regenerate search-index.json from article pages
- 2) regenerate rankings.html from article metadata
- 3) regenerate tags.html from article tags
- 4) regenerate each tag/<tag>.html page

Usage: python3 build.py [--dry-run]
"""

import json, re, os, glob
from datetime import datetime
from collections import defaultdict

SITE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TAG_DIR = os.path.join(SITE_DIR, 'tag')
OUT_INDEX = os.path.join(SITE_DIR, 'search-index.json')

# ---- configurable mapping ----
RANKING_ORDER = ['ガジェット', '暮らし', '転職・キャリア', '暮らしの課題', 'サブカル', 'お金']
RANKING_EMOJI = {
    'ガジェット': '🎧',
    '暮らし': '🏠',
    '転職・キャリア': '💼',
    '暮らしの課題': '💊',
    'サブカル': '📚',
    'お金': '💰',
}

# ---- helpers ----

def slug(text: str) -> str:
    text = text.strip()
    text = re.sub(r'[\\/:*?"<>|]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:60]


def parse_article(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    title = re.search(r'<title>(.*?)</title>', html, re.S)
    title = title.group(1).split(' | ')[0].strip() if title else os.path.basename(path)
    # strip site suffix if present
    for suffix in ' | ヒロラボ', ' — ヒロラボ', ' | 比較と検証で、賢い選択を。':
        if title.endswith(suffix):
            title = title[:-len(suffix)]

    desc = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html, re.S)
    desc = desc.group(1) if desc else ''

    og_url = re.search(r'<meta[^>]+property="og:url"[^>]+content="([^"]+)"', html, re.S)
    og_url = og_url.group(1) if og_url else '/' + os.path.relpath(path, SITE_DIR)

    # category from breadcrumb "ホーム > 記事一覧 > <CATEGORY>" or first tag
    breadcrumb_cat = re.search(r'>\s*([^<]{2,20})\s*</a>\s*</nav>\s*<main', html, re.S)
    category = breadcrumb_cat.group(1).strip() if breadcrumb_cat else ''

    # tags from meta keywords or from tag chips in body
    tags = []
    kw = re.search(r'<meta[^>]+name="keywords"[^>]+content="([^"]+)"', html, re.S)
    if kw:
        tags = [t.strip() for t in kw.group(1).split(',') if t.strip()]
    if not tags:
        chips = re.findall(r'<a[^>]+class="[^"]*tag-chip[^"]*"[^>]*>([^<]+)</a>', html)
        tags = chips[:5]

    # date
    date_m = re.search(r'<(?:p|span|div)[^>]*>\s*(\d{4}\.\d{2}\.\d{2})\s*</(?:p|span|div)>', html)
    date_str = date_m.group(1) if date_m else datetime.today().strftime('%Y.%m.%d')

    # reading time
    read_m = re.search(r'(\d+)\s*分で読める', html)
    read_min = int(read_m.group(1)) if read_m else 8

    url = '/' + os.path.relpath(path, SITE_DIR).replace(os.sep, '/')
    if not url.startswith('/'):
        url = '/' + url
    if url.endswith('.html'):
        url = url[:-5]
    if url == '':
        url = '/'
    if url.endswith('/index'):
        url = url[:-5]

    return {
        'title': title,
        'excerpt': desc or title,
        'category': category,
        'tags': tags,
        'url': url,
        'date': date_str,
        'read_min': read_min,
        'path': path,
    }


def build_index(articles):
    items = []
    for a in articles:
        items.append({
            'title': a['title'],
            'excerpt': a['excerpt'],
            'category': a['category'],
            'tags': a['tags'],
            'url': a['url'],
        })
    return {'items': items}


def build_rankings(articles):
    # group by category and keep latest 5
    by_cat = defaultdict(list)
    for a in articles:
        by_cat[a['category'] or '未分類'].append(a)
    for k in by_cat:
        by_cat[k].sort(key=lambda x: x['date'], reverse=True)

    parts = []
    parts.append('<h1>ランキング</h1>\n')
    for cat in RANKING_ORDER:
        items = by_cat.get(cat, [])[:5]
        if not items:
            continue
        emoji = RANKING_EMOJI.get(cat, '📌')
        parts.append(f'<h2>{emoji} {cat}</h2>\n')
        parts.append(f'<p class="section-lede">{datetime.today().strftime("%Y年%m月%d日")} 更新 · {len(items)} アイテム</p>\n')
        parts.append('<ol class="ranking-list" reversed>\n')
        for i, a in enumerate(items, 1):
            label = '近日公開' if '近日' in a['title'] or '予定' == a['title'] else ''
            badge = '編集長おすすめ' if i == 1 else ''
            parts.append('  <li>\n')
            parts.append(f'    <span class="ranking-badge">#{i}</span>\n')
            if badge:
                parts.append(f'    <span class="ranking-badge">{badge}</span>\n')
            if label:
                parts.append(f'    <span class="ranking-badge upcoming">{label}</span>\n')
            parts.append(f'    <h3><a href="{a["url"]}">{a["title"]}</a></h3>\n')
            parts.append(f'    <p>{a["date"]}</p>\n')
            parts.append('  </li>\n')
        parts.append('</ol>\n')
    return '\n'.join(parts)


def build_tags(articles):
    # collect counts
    counts = defaultdict(int)
    for a in articles:
        main = a['category'] or '未分類'
        counts[main] += 1
        for t in a['tags']:
            counts[t] += 1
    sorted_tags = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    parts = ['<h1>タグ一覧</h1>\n', '<div class="tag-cloud">\n']
    for name, count in sorted_tags:
        parts.append(f'  <a href="tag/{slug(name)}.html" class="tag-chip" style="--size: {min(1.2 + count * 0.08, 1.5)}em">{name}<span class="tag-count">{count}</span></a>\n')
    parts.append('</div>\n')
    return '\n'.join(parts)


def build_tag_page(tag_name, articles):
    matched = [
        a for a in articles
        if tag_name == (a['category'] or '') or tag_name in a['tags']
    ]
    matched.sort(key=lambda x: x['date'], reverse=True)
    parts = [
        f'<h1>タグ: {tag_name}</h1>\n',
        f'<p>{tag_name}に関する記事一覧。{len(matched)} 記事</p>\n',
        '<div class="category-grid">\n',
    ]
    for a in matched:
        desc = a['excerpt'] or a['title']
        if len(desc) > 100:
            desc = desc[:100] + '…'
        parts.append('  <a href="{0}" class="category-tile">\n'.format(a['url']))
        parts.append(f'    <span class="icon">📄</span>\n')
        parts.append(f'    <span class="name">{a["title"]}</span>\n')
        parts.append(f'    <span class="count">{a["date"]} · {a["read_min"]}分</span>\n')
        parts.append('  </a>\n')
    parts.append('</div>\n')
    parts.append('<p class="mt-2"><a href="/tags.html" class="more-link">← タグ一覧に戻る</a></p>\n')
    return '\n'.join(parts)


# ---- main ----

def main():
    dry = '--dry-run' in (__import__('sys').argv)

    articles = []
    for pattern in [os.path.join(SITE_DIR, 'article*.html'), os.path.join(SITE_DIR, 'tag', '*.html')]:
        for path in glob.glob(pattern):
            if os.path.basename(path) in {'イヤホン.html','NISA.html','副業.html','Kindle.html','ふるさと納税.html'}:
                continue
            try:
                articles.append(parse_article(path))
            except Exception as e:
                print('skip', path, e)

    # also scan site root for article-like pages (handles variations)
    for path in glob.glob(os.path.join(SITE_DIR, '*.html')):
        name = os.path.basename(path)
        if name in {'index.html','articles.html','rankings.html','tags.html','about.html','contact.html',
                     'policy.html','disclaimer.html','404.html','特商法.html'}:
            continue
        if name.startswith('article') and name.endswith('.html'):
            try:
                articles.append(parse_article(path))
            except Exception:
                pass

    # dedupe by path
    seen = set()
    uniq = []
    for a in articles:
        if a['path'] not in seen:
            seen.add(a['path'])
            uniq.append(a)
    articles = uniq

    print(f'articles: {len(articles)}')
    if not articles:
        return

    # 1) search index
    index = build_index(articles)
    if not dry:
        with open(OUT_INDEX, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        print('wrote', OUT_INDEX)
    else:
        print('dry-run: skip writing', OUT_INDEX)

    # 2) rankings
    rankings_html = build_rankings(articles)
    if not dry:
        # minimal wrapper: insert between <main> tags, preserving header/footer
        target = os.path.join(SITE_DIR, 'rankings.html')
        with open(target, 'r', encoding='utf-8') as f:
            base = f.read()
        # quick strategy: replace content between <main> and </main>
        new_base = re.sub(
            r'(<main[^>]*>)(.*?)(</main>)',
            r'\1\n' + rankings_html + r'\n\3',
            base,
            flags=re.S,
        )
        with open(target, 'w', encoding='utf-8') as f:
            f.write(new_base)
        print('updated rankings.html')

    # 3) tags
    tags_html = build_tags(articles)
    if not dry:
        target = os.path.join(SITE_DIR, 'tags.html')
        with open(target, 'r', encoding='utf-8') as f:
            base = f.read()
        new_base = re.sub(
            r'(<main[^>]*>)(.*?)(</main>)',
            r'\1\n' + tags_html + r'\n\3',
            base,
            flags=re.S,
        )
        with open(target, 'w', encoding='utf-8') as f:
            f.write(new_base)
        print('updated tags.html')

    # 4) tag pages
    # collect all unique tags
    all_tags = set()
    for a in articles:
        all_tags.add(a['category'] or '未分類')
        all_tags.update(a['tags'])
    all_tags = sorted(t for t in all_tags if t)
    os.makedirs(TAG_DIR, exist_ok=True)
    for t in all_tags:
        page = os.path.join(TAG_DIR, slug(t) + '.html')
        body = build_tag_page(t, articles)
        if not dry:
            if os.path.exists(page):
                with open(page, 'r', encoding='utf-8') as f:
                    base = f.read()
                new_base = re.sub(
                    r'(<main[^>]*>)(.*?)(</main>)',
                    r'\1\n' + body + r'\n\3',
                    base,
                    flags=re.S,
                )
                with open(page, 'w', encoding='utf-8') as f:
                    f.write(new_base)
            else:
                # minimal shell using index.html as template
                with open(os.path.join(SITE_DIR, 'index.html'), 'r', encoding='utf-8') as f:
                    tmpl = f.read()
                shell = re.sub(
                    r'(<main[^>]*>)(.*?)(</main>)',
                    r'\1\n' + body + r'\n\3',
                    tmpl,
                    flags=re.S,
                )
                shell = re.sub(r'<title>.*?</title>', f'<title>タグ: {t} | ヒロラボ</title>', shell, flags=re.S)
                with open(page, 'w', encoding='utf-8') as f:
                    f.write(shell)
            print('updated', page)
        else:
            print('dry-run: skip', page)

    print('done')


if __name__ == '__main__':
    main()
