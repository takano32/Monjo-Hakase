# 文章博士（Monjo-Hakase）— Cloud Run 用コンテナ
#
# 現行の Perl CGI + jcorrect + CaboCha + MeCab + nkf スタックを「そのまま」動かす
# 移植版に、Astro 製の静的フロントエンド（web/）を載せた構成。
# Cloud Run は $PORT（既定 8080）で HTTP を待ち受けるコンテナを要求するため、
# Apache を $PORT で前面起動し、mod_cgid で njc.cgi を実行する。
#
#   Stage 1 (builder) … CRF++ / CaboCha をソースビルド
#   Stage 2 (web)     … Astro フロントエンドを静的ビルド（node）
#   Stage 3 (runtime) … Apache + Perl CGI + MeCab + nkf。DocumentRoot に
#                       legacy → app/njc.cgi → web/dist の順で上書き配置
#
# ── 注意（docs/to-be.md 参照）────────────────────────────────────────────
#  * CaboCha / CRF++ は GitHub の taku910/{crfpp,cabocha} を clone してビルド。
#    再現性のためコミット固定は未対応（TODO）。
# ────────────────────────────────────────────────────────────────────────

# ============================================================
# Stage 1: CRF++ と CaboCha をソースからビルド
# ============================================================
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential autoconf automake libtool autoconf-archive \
        pkg-config gettext git ca-certificates \
        mecab libmecab-dev mecab-ipadic-utf8 \
    && rm -rf /var/lib/apt/lists/*

# --- CRF++（CaboCha の依存）---
# taku910/crfpp の Git リポジトリは crf_learn.cpp が要求する winmain.h を欠く
# （公式 tarball にはあるが Git ミラーには無い）。学習用バイナリ crf_learn/crf_test は
# それでビルド不可だが、CaboCha の「実行」に必要なのは共有ライブラリ libcrfpp と
# crfpp.h だけ。よってライブラリターゲットのみをビルド・インストールする。
# TODO: 再現性のためコミットハッシュ/タグを固定する
RUN git clone --depth 1 https://github.com/taku910/crfpp.git /tmp/crfpp \
    && cd /tmp/crfpp \
    && ./configure --prefix=/usr/local \
    && make -j"$(nproc)" libcrfpp.la \
    && mkdir -p /usr/local/lib /usr/local/include \
    && ./libtool --mode=install install -c libcrfpp.la /usr/local/lib/ \
    && install -m 0644 crfpp.h /usr/local/include/ \
    && ldconfig

# --- CaboCha 本体（UTF-8 / IPA 品詞体系でビルド）---
# TODO: 再現性のためコミットハッシュ/タグを固定する
# 文字コードは MeCab 辞書(UTF-8)に合わせて UTF8 を指定
RUN git clone --depth 1 https://github.com/taku910/cabocha.git /tmp/cabocha \
    && cd /tmp/cabocha \
    # Git ミラーは configure を含むが install-sh 等の補助ファイルを欠くため、
    # autoreconf -fi で不足ファイルを生成し直す。
    && autoreconf -fi \
    && ./configure --prefix=/usr/local \
        --with-charset=UTF8 \
        --with-posset=IPA \
        --enable-utf8-only \
        CPPFLAGS="-I/usr/local/include" \
        LDFLAGS="-L/usr/local/lib" \
    && make -j"$(nproc)" \
    && make install \
    && ldconfig

# ============================================================
# Stage 2: フロントエンド（Astro）を静的ビルド
# ============================================================
FROM node:24-alpine AS web

WORKDIR /web
# 依存だけ先に入れてレイヤキャッシュを効かせる
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build
# → /web/dist に index.html, about/index.html, _astro/* が生成される

# ============================================================
# Stage 3: 実行イメージ
# ============================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
# Cloud Run が上書きする。ローカル実行時の既定値。
ENV PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
        apache2 \
        perl libcgi-pm-perl \
        nkf \
        mecab mecab-ipadic-utf8 libmecab2 \
        gettext-base \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# builder からビルド成果物（CRF++ / CaboCha 本体・ライブラリ・モデル）を取得
COPY --from=builder /usr/local/ /usr/local/
RUN ldconfig

# njc.cgi は cabocha を /usr/bin/cabocha 決め打ちで呼ぶため symlink を張る
# （jcorrect-hs は PATH 上の cabocha を open2 で呼ぶので /usr/local/bin でも可）
RUN ln -sf /usr/local/bin/cabocha /usr/bin/cabocha

# --- アプリ配置 ---
# 静的ファイルと CGI を DocumentRoot へ、jcorrect-hs は njc.cgi のハードコードパスへ。
# njc.cgi は legacy を土台に、保守版（app/）で上書きする。
#   legacy/ … 原状のアーカイブ（無改変）
#   app/    … 保守対象。コマンドインジェクション修正 + JSON API 追加版 njc.cgi。
COPY legacy/monjo-hakase/ /var/www/html/
COPY app/njc.cgi /var/www/html/njc.cgi
RUN cp /var/www/html/jcorrect-hs /var/www/jcorrect-hs \
    && chmod +x /var/www/jcorrect-hs /var/www/html/njc.cgi /var/www/html/jcorrect-hs

# 新フロントエンド（Astro の静的ビルド）を最後に重ねる。
#   /            … 校正画面（index.html）。旧 index.htm は /index.htm としてアーカイブ参照用に残る
#   /about/      … 使い方・備考（旧トップページの情報）
#   /_astro/*    … ハッシュ付きの CSS/JS
# njc.cgi は format=json で JSON を返し、フロントエンドが fetch で呼ぶ。
COPY --from=web /web/dist/ /var/www/html/
# 旧サイト配布の手引き PDF（備考ページからリンク）
COPY legacy/site/monjo-hakase-tebiki.pdf /var/www/html/monjo-hakase-tebiki.pdf

# --- Apache 設定（$PORT 待受 + CGI 実行）---
# 設定は entrypoint が $PORT を差し込んでレンダリングする（テンプレート方式）
COPY docker/apache-monjo.conf.template /etc/apache2/apache-monjo.conf.template
COPY docker/ports.conf.template /etc/apache2/ports.conf.template
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN a2enmod cgid setenvif headers \
    && chmod +x /usr/local/bin/entrypoint.sh \
    # Apache をフォアグラウンド前提に。ログは stdout/stderr へ
    && ln -sf /dev/stdout /var/log/apache2/access.log \
    && ln -sf /dev/stderr /var/log/apache2/error.log

EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
