#!/bin/sh

mkdir livelist/static/css -p
#wget -O livelist/static/css/bootstrap.min.css https://bootswatch.com/5/darkly/bootstrap.min.css
wget -O livelist/static/css/bootstrap.min.css https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css

wget -O ehtml.zip https://github.com/Guseyn/EHTML/archive/refs/tags/v3.0.9.zip
mkdir livelist/static/js/ehtml -p
unzip -o ehtml
mv EHTML-*/src/* livelist/static/js/ehtml
rm -rf EHTML-*

wget -O bootstrap-icons.zip https://github.com/twbs/icons/releases/download/v1.13.1/bootstrap-icons-1.13.1.zip
unzip -o bootstrap-icons
mkdir livelist/static/css/fonts -p
mv bootstrap-icons-*/bootstrap-icons.min.css livelist/static/css/
mv bootstrap-icons-*/fonts/* livelist/static/css/fonts/
rm -rf bootstrap-icons-*

wget -O livelist/static/js/bootstrap.bundle.min.js https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js
wget -O livelist/static/js/socket.io.min.js https://cdn.socket.io/3.1.3/socket.io.min.js

rm bootstrap-icons.zip ehtml.zip
