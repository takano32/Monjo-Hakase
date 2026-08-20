# legacy/ — 旧「文章博士」アーカイブ

リブートの参照元として保存した、旧システムの原本一式。**改変せず原状のまま**保持する。
実態の解説は [`../docs/as-is.md`](../docs/as-is.md) を参照。

## 来歴（provenance）

| ディレクトリ | 取得元 | 内容 |
|---|---|---|
| `monjo-hakase/` | 配布ソース `monjo-hakase-r2.zip`（Rev.2, 2013-07-08） | 自前設置用に公開されていたソース一式。本サイト稼働版との差はトラッキングコードの有無のみ（作者記載）。 |
| `site/` | 公開サイト http://monjo.lunark.org/ のスナップショット（2026-08-21 取得） | zip に含まれない公開物。トップのランディングページと手引きPDF。 |

## ファイル

### monjo-hakase/（Rev.2 ソース）

- `njc.cgi` — 本体（Perl CGI）。入力処理・エンジン呼び出し・結果整形・HTML出力。
- `jcorrect-hs` — UTF-8 対応の改造版 jcorrect（大崎博之氏, GPL）。
- `index.htm` — 入力フォーム画面。
- `njc.css` — スタイル（エラー種別ごとの色定義）。
- `GPL` / `BSDL` — ライセンス全文（本ソフトは両者のデュアルライセンス）。
- `*.png` / `*.gif` — バナー・アイコン。

### site/（公開サイトスナップショット）

- `index.html` — トップのランディングページ（説明・更新履歴・リンク集。`monjo-hakase/index.htm` の入力フォームとは別物）。
- `monjo-hakase-tebiki.pdf` — 印刷用の手引き（3ページ）。

## ライセンス

BSDL / GPL デュアル（同梱 jcorrect が GPL のため）。詳細は `monjo-hakase/GPL`・`monjo-hakase/BSDL`。
