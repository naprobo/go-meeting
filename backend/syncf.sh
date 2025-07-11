cd /xxxxxxxxxx/frontend/meeting-record-frontend
./releaseBuild.sh
cd -
cd static/
rm -fr *
cp -r ../../frontend/meeting-record-frontend/dist/* ./
ls -lrt
cd ..

