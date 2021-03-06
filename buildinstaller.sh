set -e

rm -rf bin/serverthrall/dist
mkdir -p bin/serverthrall
cp serverthrall.ico bin/serverthrall/serverthrall.ico

pyinstaller main.py \
	--name serverthrall \
	--workpath .\\bin\\serverthrall\\build \
	--distpath .\\bin\\serverthrall\\dist \
	--specpath .\\bin\\serverthrall \
	--icon .\\bin\\serverthrall\\serverthrall.ico \
	--console \
	--onedir \
	--onefile \
	--noconfirm \
	--clean

 mkdir bin/serverthrall/dist/vendor
 mkdir bin/serverthrall/dist/vendor/steamcmd
 cp -r vendor/steamcmd/steamcmd.exe bin/serverthrall/dist/vendor/steamcmd/steamcmd.exe
