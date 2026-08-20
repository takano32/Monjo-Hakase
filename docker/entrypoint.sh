#!/bin/sh
# Cloud Run は $PORT（既定 8080）で待ち受けるコンテナを要求する。
# Apache の Listen と vhost を $PORT に合わせてレンダリングしてから起動する。
set -e

: "${PORT:=8080}"
export PORT

# Listen ディレクティブと vhost を $PORT で生成
envsubst '${PORT}' < /etc/apache2/ports.conf.template \
    > /etc/apache2/ports.conf
envsubst '${PORT}' < /etc/apache2/apache-monjo.conf.template \
    > /etc/apache2/sites-available/000-default.conf

# Debian の apache2ctl が参照する環境変数
export APACHE_LOG_DIR=/var/log/apache2
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
export APACHE_PID_FILE=/var/run/apache2/apache2.pid
mkdir -p /var/run/apache2

# Apache をフォアグラウンドで起動（コンテナのメインプロセス）
exec apache2ctl -D FOREGROUND
