# 文章博士（Monjo-Hakase）

技術文書・テクニカルライティング向けの **日本語 自動文章校正支援システム**。
フォームに文章を入力すると、係り受け解析にかけて読みにくい箇所（主語なし・冗長表現・
語順・文節長さ・係り受けの深さ/量）を色付きで指摘します。

2011〜2015年に公開されていた個人開発ツール（作者: Lunar-K）を、
無改造に近い形で現代のインフラに載せ替える **リブートプロジェクト**です。

## 稼働中サービス

- **公開URL:** https://monjo-hakase-v3aibpl2aa-an.a.run.app
- Google Cloud Run（東京リージョン, `asia-northeast1`）/ scale-to-zero
- HTTPS、`--max-instances 3`

トップページ `/` が校正画面です（開いてすぐ入力できます）。旧トップページにあった説明・使い方・
制限事項・更新履歴・リンクは `/about/`（使い方・備考）にまとめました。

## 仕組み

Perl CGI が外部エンジンを順に呼ぶパイプライン構成:

```
入力 → nkf(UTF-8化) → jcorrect（主語なし/冗長表現/語順）
                     → CaboCha（係り受け解析・深さ/量）  ← 内部で MeCab
     → 7種のエラーに分類して JSON（format=json）または HTML で返す
```

フロントエンドは [Astro](https://astro.build/) で静的に生成した画面（`web/`）で、
フォーム送信を横取りして `POST /njc.cgi`（`format=json`）を `fetch` し、
本文ハイライト・指摘一覧・解説をページ遷移なしに描画します。
JavaScript が無効な場合は同じフォームが通常 POST され、従来の HTML 画面にフォールバックします。

エンジン: **CaboCha**（係り受け解析）, **MeCab**（形態素解析）, **CRF++**（CaboCha 依存）,
**jcorrect**（GPL, 大崎博之氏。UTF-8 対応の改造版 `jcorrect-hs` を同梱）, **nkf**。

## リポジトリ構成

| パス | 内容 |
|------|------|
| `legacy/` | 旧システムの原本アーカイブ（**無改変**）。`monjo-hakase/`＝配布ソース, `site/`＝公開サイトのスナップショット |
| `app/` | 保守対象のオーバーレイ。コマンドインジェクション修正 + JSON API（`format=json`）追加版 `njc.cgi` |
| `web/` | Astro 製フロントエンド。`/`（校正画面）と `/about/`（使い方・備考）。Docker ビルド時に静的生成して配置 |
| `Dockerfile` | CRF++/CaboCha をソースビルドし、Apache+Perl CGI+MeCab+nkf で起動するコンテナ |
| `docker/` | Cloud Run 用の Apache 設定と `$PORT` 対応 entrypoint（テンプレート方式） |
| `.github/workflows/docker.yml` | ビルド + スモークテスト + セキュリティ回帰 + GHCR push |
| `.github/workflows/deploy.yml` | Cloud Run 自動デプロイ（WIF キーレス認証） |
| `scripts/` | WIF / GitHub 側セットアップの再現スクリプト |
| `docs/as-is.md` | 旧システムの現状調査（時点固定・不変） |
| `docs/to-be.md` | リブート方針と進捗 |

## 開発・デプロイ

手元に Docker が無くても CI で完結します。

- **ビルド検証:** `Dockerfile`/`docker/`/`legacy/`/`app/`/`web/` を変更して push すると
  `docker-build.yml` がビルド・起動・校正疎通・フロントエンド配置・JSON API・https 化・
  インジェクション無害化を検証。
- **デプロイ:** `master` への push（対象パス変更時）で `deploy.yml` が Cloud Run へ自動反映。
  手動実行は `gh workflow run deploy.yml`。認証はキーレス（Workload Identity Federation）で
  長期鍵を持たない。初期セットアップは `scripts/setup-wif.sh` / `scripts/setup-github.sh`。

ローカルで動かす場合:

```sh
docker build -t monjo-hakase .
docker run --rm -p 8080:8080 monjo-hakase
# http://localhost:8080/ を開く
```

フロントエンドだけを手元で編集する場合（校正 API は上のコンテナ、または本番へ中継）:

```sh
cd web
npm ci
MONJO_API_ORIGIN=http://localhost:8080 npm run dev   # http://localhost:4321/
npm run build                                        # dist/ に静的生成
```

## リブートで解消したこと

- **フロント刷新**（Astro。トップ＝校正画面、旧トップの情報は `/about/` へ。死んだ第三者ウィジェット・旧 GA を除去。
  ダークモード・スマートフォン対応、下書きのブラウザ内保存、Ctrl/⌘+Enter 送信）
- **HTTPS 化**（旧環境は HTTP 平文のみ。Cloud Run が TLS 終端。フォーム action も https）
- **コマンドインジェクション（CWE-78）の解消**（`echo|cabocha` のシェル経由呼び出しを
  `IPC::Open2` に置換。CI 回帰テスト付き）
- **再現可能ビルド / 自動デプロイ**（Docker + GitHub Actions）

詳細な経緯は [`docs/as-is.md`](docs/as-is.md) と [`docs/to-be.md`](docs/to-be.md) を参照。

## ライセンス

BSDL / GPL デュアルライセンス（同梱 jcorrect が GPL のため）。
`legacy/monjo-hakase/GPL`・`legacy/monjo-hakase/BSDL` を参照。
