# hiro-lab Design Tokens

最終更新: 2026-06-23

## 目的
このドキュメントは、**作る行為自体が美学を再生産する**ための設計基準である。
ページ追加・変更時は、この値を優先し、場当たり的な色・余白・タイポの追加を禁止する。

## 1. 色（和紙ベース・墨アクセント）

### 背景と面
- `--color-bg`: `#f5f1e8` — 和紙色（body 常時）
- `--color-surface`: `#fbf9f2` — やや明るい和紙（カード等）
- `--color-accent-light`: `#e8e3d6` — 淡墨和紙（薄い強調面）

### 文字
- `--color-text`: `#1a1a1a` — 墨黒
- `--color-text-muted`: `#5a5650` — 墨グレー
- `--color-sumi-soft`: `#8a857a` — 中間墨（メタ情報等）
- `--color-accent-dark`: `#0a0a10` — 濃墨（CTA等の濃い表現に限る）

### アクセント
- `--color-vermilion`: `#9c3a2e` — 朱（ランキング 1 位・強調点のみ）
- `--color-warn-light`: `#f6e9e2` — 朱薄（アフィリエイト明示ブロック用）

### 境界と影
- `--color-border`: `#d8d2c2` — 墨ぼかし枠
- `--shadow-sm`: `0 1px 2px rgba(40, 30, 20, 0.06)`
- `--shadow-md`: `0 4px 14px rgba(40, 30, 20, 0.10)`
- `--shadow-lg`: `0 12px 34px rgba(40, 30, 20, 0.14)`

## 2. タイポグラフィ（明朝中心）

- フォント: `--font-mincho` (Hiragino Mincho ProN / Yu Mincho / Noto Serif JP / serif)
- 本文サイズ: `1.0625rem` (article-body)
- 本文行送り: `1.95`
- 見出し明朝 weight: `400` または `500`。`700` は使わない
- 字間（letter-spacing）: 舛目 `0.02em〜0.18em` の範囲で統一
- 見出し supported: `inline-block` + 下線・上線アクセントを基本形とする

## 3. 余白とリズム

- Section padding: `4rem` 前後
- Article card padding: `1.25rem 1.4rem` 前後
- カード間 gap: `1.5rem`
- 余白で「間」を作る。情報を詰めすぎない

## 4. 共通構造

- Container 最大幅: `1100px` (main sections), `720px` (article body)
- カード共通: `border-radius: 4px`, `border: 1px solid var(--color-border)`, 背景 `var(--color-surface)`
- Hover 共通: `translateY(-1px)`〜`(-3px)` + `border-color: var(--color-text)`

## 5. 禁止事項

- 動的な墨要素（blob / brush / drop 等）の追加禁止
- 明朝以外の見出しフォントへの変更禁止
- `color-accent-dark` の全面適用禁止（補助に限る）
- checklist 未適用でのページ公開禁止
