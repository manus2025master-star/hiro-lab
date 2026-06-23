#!/usr/bin/env python3
"""
hiro-lab new article generator:
- create article.html / article-review.html / article-howto.html from a simple data file
- format: JSON/YAML-like Python dict in a .json or .md frontmatter block

Usage:
  python3 new_article.py --sample          # print sample input
  python3 new_article.py --input a.json    # generate into site/
"""
from __future__ import annotations

import argparse, json, os, re, sys
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parents[1]
SITE = REPO
TAG_DIR = SITE / 'tag'
TPL_DIR = REPO / 'builder' / 'templates'

DATE_FMT = '%Y.%m.%d'


def slug(text: str) -> str:
    text = text.strip()
    text = re.sub(r'[\\/:*?"<>|]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:64]


def render_rating_stars(score: float, max_score: int = 5) -> str:
    filled = int(score)
    half = (score - filled) >= 0.5
    out = ['<div class="rating-wrap" aria-label="%s / %s">' % (score, max_score)]
    for _ in range(filled):
        out.append('<span class="star">★</span>')
    if half:
        out.append('<span class="star half">★</span>')
    for _ in range(max_score - filled - (1 if half else 0)):
        out.append('<span class="star">☆</span>')
    out.append('</div>')
    return '\n'.join(out)


def render_spec_table(rows: list[dict]) -> str:
    parts = ['<div class="spec-table">', '  <table>', '    <thead><tr><th>項目</th><th>内容</th></tr></thead>', '    <tbody>']
    for row in rows:
        parts.append('      <tr><td>%s</td><td>%s</td></tr>' % (row.get('name',''), row.get('value','')))
    parts.append('    </tbody>')
    parts.append('  </table>')
    parts.append('</div>')
    return '\n'.join(parts)


def render_share_bar(category: str, title: str) -> str:
    text = ('%s「%s」をヒロラボが検証しました。' % (category, title))
    encoded = text.replace(' ', '%20')
    return (
        '<aside class="share-bar">'
        '<span>シェアする</span>'
        '<a class="share-btn" rel="nofollow noopener" target="_blank" href="https://twitter.com/intent/tweet?text=%s">X</a>'
        '<a class="share-btn" rel="nofollow noopener" target="_blank" href="https://www.facebook.com/sharer/sharer.php?u=%s">Facebook</a>'
        '<a class="share-btn" rel="nofollow noopener" target="_blank" href="https://timeline.line.me/social-plugin/share?url=%s">LINE</a>'
        '</aside>' % (encoded, encoded, encoded)
    )


def render_breadcrumb(kind: str, category: str = '') -> str:
    parts = ['<nav class="breadcrumb" aria-label="パンくずリスト">', '  <ul>', '    <li><a href="/">ホーム</a></li>']
    parts.append('    <li><a href="%s">%s</a></li>' % (_kind_target(kind), _kind_label(kind, category)))
    parts.append('  </ul>')
    parts.append('</nav>')
    return '\n'.join(parts)


def _kind_target(kind: str) -> str:
    return {
        'article': 'articles.html',
        'review': 'articles.html',
        'howto': 'articles.html',
    }.get(kind, 'articles.html')


def _kind_label(kind: str, category: str = '') -> str:
    return {
        'article': '記事一覧',
        'review': 'レビュー',
        'howto': 'ハウツー',
    }.get(kind, '記事一覧')


def load_input(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    # strip yaml-like frontmatter between first two '---'
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
    if m:
        meta = {}
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2).strip()
        data = dict(meta)
        data['body'] = body
        return data
    return json.loads(raw)


def build_article(data: dict) -> str:
    dt = data.get('date', datetime.today().strftime(DATE_FMT))
    kind = data.get('type', 'article')
    category = data.get('category', '未分類')
    title = data.get('title', '無題')
    tags = [t.strip() for t in data.get('tags', '').split(',') if t.strip()]
    lead = data.get('lead', '')
    body = data.get('body', '')
    
    slug_name = '%s_%s' % (dt.replace('.', ''), slug(title))
    
    tpl = REPO / 'builder' / 'templates' / ('article-review.html' if kind == 'review' else 'article-howto.html' if kind == 'howto' else 'article.html')
    with open(tpl, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # inject essential metadata
    html = re.sub(r'<title>.*?</title>', '<title>%s | ヒロラボ</title>' % title, html, flags=re.S)
    meta_desc = re.search(r'<meta name="description" content="[^"]*">', html)
    if meta_desc:
        html = html.replace(meta_desc.group(0), '<meta name="description" content="%s">' % lead[:120])
    og_url = data.get('url', '/%s.html' % slug_name)
    html = html.replace('/article.html', og_url)
    
    # date + title block
    html = html.replace('<h1>記事</h1>', '%s\n<h1>%s</h1>\n<p>%s</p>' % ('<p class="article-meta">%s · %s</p>' % (dt, kind_label(kind)), title, lead))
    
    # breadcrumb
    html = html.replace('<nav class="breadcrumb" aria-label="パンくずリスト">', render_breadcrumb(kind, category), 1)
    
    # review-specific extras
    if kind == 'review':
        score = float(data.get('score', 4.0))
        if '<!-- rating card -->' in html:
            rating_block = '<h2>総合評価</h2>\n' + render_rating_stars(score) + '\n<p class="center-text">%s / 5</p>' % score
            html = html.replace('<!-- rating card -->', rating_block)
        rows = data.get('specs', [])
        if rows and '<!-- spec table -->' in html:
            html = html.replace('<!-- spec table -->', render_spec_table(rows))
    
    if kind == 'howto':
        if '<!-- steps -->' in html and data.get('steps'):
            parts = ['<ol class="howto-steps">']
            for step in data['steps']:
                parts.append('  <li>%s</li>' % step)
            parts.append('</ol>')
            html = html.replace('<!-- steps -->', '\n'.join(parts))
    
    # related entries
    if '<!-- related articles -->' in html:
        related = data.get('related', [])
        if related:
            block = ['<div class="related-articles">', '  <h3>関連記事</h3>']
            for r in related[:3]:
                block.append('  <a href="%s" class="category-tile">' % r.get('url', '#'))
                block.append('    <span class="name">%s</span>' % r.get('title', ''))
                block.append('  </a>')
            block.append('</div>')
            html = html.replace('<!-- related articles -->', '\n'.join(block))
        else:
            html = html.replace('<!-- related articles -->', '')
    
    # share
    if '<!-- share bar -->' in html:
        html = html.replace('<!-- share bar -->', render_share_bar(category, title))
    
    # tags
    if tags:
        chips = ''.join('<a href="tag/%s.html" class="tag-chip">%s</a>' % (slug(t), t) for t in tags)
        html = html.replace('<!-- article tags -->', chips)
    
    # keyword meta
    kw = ','.join(tags)
    if kw and '<meta name="keywords"' in html:
        html = re.sub(r'<meta name="keywords" content="[^"]*">', '<meta name="keywords" content="%s">' % kw, html)
    
    out_name = '%s.html' % slug_name
    out_path = SITE / out_name
    out_path.write_text(html, encoding='utf-8')
    return str(out_path), slug_name, kind


def kind_label(kind: str) -> str:
    return {'review': 'レビュー', 'howto': 'ハウツー', 'article': '記事'}.get(kind, '記事')


def sample() -> str:
    return """---
title: Soundcore Liberty 4 Pro を 1 ヶ月使った
kind: review
category: ガジェット
tags: イヤホン, Anker, ワイヤレス
date: 2026.06.23
lead: 日常使いと通勤で 1 か月間、実機比較しながら評価した結論。
score: 4.2
specs:
  - {name: 接続, value: Bluetooth 5.3}
  - {name: 再生時間, value: 約9時間 + 36時間 (充電ケース)}
  - {name: 防水, value: IPX4}
  - {name: 重さ, value: 56g (ケース) / 約5.4g (片耳)}
steps: []
related:
  - {title: ワイヤレスイヤホン 5 機種を 3 ヶ月使って比較した結論, url: ./article.html}
body: |
  ## 買った目的
  イヤホンは毎日す...
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', help='input markdown/json/yaml-like file')
    ap.add_argument('--sample', action='store_true')
    ap.add_argument('--kind', default='article', choices=['article', 'review', 'howto'])
    ap.add_argument('--title', default='')
    ap.add_argument('--category', default='未分類')
    ap.add_argument('--tags', default='')
    ap.add_argument('--date', default=datetime.today().strftime(DATE_FMT))
    ap.add_argument('--lead', default='')
    ap.add_argument('--score', type=float, default=4.0)
    ap.add_argument('--body', default='')
    args = ap.parse_args()

    if args.sample:
        print(sample())
        return

    if args.input:
        data = load_input(args.input)
    else:
        data = {
            'kind': args.kind,
            'type': args.kind,
            'title': args.title or ('新しい%s' % args.kind),
            'category': args.category,
            'tags': args.tags,
            'date': args.date,
            'lead': args.lead or '記事本文をご確認ください。',
            'score': args.score,
            'specs': [],
            'steps': [],
            'related': [],
            'body': args.body,
        }

    out, slug_name, kind = build_article(data)
    print('created:', out)


if __name__ == '__main__':
    main()
