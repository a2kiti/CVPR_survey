# CVPR 2025 第一著者企業所属抽出パイプライン

処理を3段階のスクリプトに分割しています。

1. CVF Open Access の一覧から論文情報取得 + PDFダウンロード（礼儀的アクセス）
2. PDF解析による所属候補抽出（論文名・著者・著者所属・PDFパスの一覧生成）
3. 第一著者が企業所属と思われる論文の抽出

## 1) PDFダウンロード

```bash
python scripts/01_download_cvpr2025_pdfs.py \
  --out-dir data/cvpr2025 \
  --delay-seconds 1.5 \
  --resume
```

- 出力: `data/cvpr2025/downloaded_papers.json`
- PDF保存先: `data/cvpr2025/pdfs/*.pdf`
- 既定で `--resume` が有効なため、中断後に再実行すると完了済みPDFをスキップして途中から再開できます。

### ネットワーク制約がある場合

一覧HTMLを別環境で取得済みなら、ローカルファイル入力で実行できます。

```bash
python scripts/01_download_cvpr2025_pdfs.py \
  --out-dir data/cvpr2025 \
  --listing-html-path /path/to/CVPR2025_day_all.html \
  --resume
```

## 2) 所属抽出

```bash
python scripts/02_extract_affiliations.py \
  --in-json data/cvpr2025/downloaded_papers.json \
  --out-json data/cvpr2025/papers_with_affiliations.json
```

- 出力レコードには `title`, `authors`, `affiliations`, `pdf_path` を含みます。

## 3) 企業所属抽出

```bash
python scripts/03_filter_corporate_first_author.py \
  --in-json data/cvpr2025/papers_with_affiliations.json \
  --out-json data/cvpr2025/papers_first_author_corporate.json
```

## サーバー負荷への配慮

- 1リクエストごとに `delay-seconds + jitter(0.2~0.8秒)` 待機
- 並列ダウンロードなし
- User-Agent明示
- 通信エラー時のリトライ実装（過度な連続リクエストは避ける）

## 注意

- PDFテキスト抽出は `pdftotext` コマンドに依存します。
- `pdftotext` 未導入時、`affiliations` は空になります。
- 所属抽出・企業判定はヒューリスティックです。最終確認は人手で行ってください。
