# 文章博士（Monjo-Hakase）— Cloud Run 用コンテナ（たたき台）
#
# 現行の Perl CGI + jcorrect + CaboCha + MeCab + nkf スタックを「そのまま」動かす
# 最小移植版。Cloud Run は $PORT（既定 8080）で HTTP を待ち受けるコンテナを要求するため、
# Apache を $PORT で前面起動し、mod_cgid で njc.cgi を実行する。
#
# ── 注意（未確定ポイント。docs/to-be.md 参照）──────────────────────────────
#  * CaboCha / CRF++ はソースからビルドする。GitHub の taku910/{crfpp,cabocha}
#    を clone してビルドしているが、CaboCha の学習済みモデル同梱状況は要検証。
#    モデルが無いと係り受け解析が動かないため、ビルド後に動作確認すること。
#    モデルを別途持っている場合は docker/vendor/ に置いて COPY する方式に変える。
#  * as-is.md に記載のコマンドインジェクション（njc.cgi の echo+バッククォート）は
#    このコンテナ化では未修正のまま。公開前に必ず修正すること。
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
# Stage 2: 実行イメージ
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
#   app/    … 保守対象。現状はコマンドインジェクション修正版 njc.cgi のみ。
COPY legacy/monjo-hakase/ /var/www/html/
COPY app/njc.cgi /var/www/html/njc.cgi
RUN cp /var/www/html/jcorrect-hs /var/www/jcorrect-hs \
    && chmod +x /var/www/jcorrect-hs /var/www/html/njc.cgi /var/www/html/jcorrect-hs \
    # トップは index.htm を使う
    && ln -sf /var/www/html/index.htm /var/www/html/index.html

# --- Apache 設定（$PORT 待受 + CGI 実行）---
# 設定は entrypoint が $PORT を差し込んでレンダリングする（テンプレート方式）
COPY docker/apache-monjo.conf.template /etc/apache2/apache-monjo.conf.template
COPY docker/ports.conf.template /etc/apache2/ports.conf.template
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN a2enmod cgid setenvif \
    && chmod +x /usr/local/bin/entrypoint.sh \
    # Apache をフォアグラウンド前提に。ログは stdout/stderr へ
    && ln -sf /dev/stdout /var/log/apache2/access.log \
    && ln -sf /dev/stderr /var/log/apache2/error.log

EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
