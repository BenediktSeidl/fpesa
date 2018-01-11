set -auvx

# if we just cd into our project and run `npm install && npm run build` we
# create folders that are owend by root.
# to prevent this, we copy the whole frontend folder into this container and
# execute the scripts there

cd "$(dirname "$0")" # directory of this script
cd ../frontend

mkdir -p /opt/fpesa/frontend/
cp -r . /opt/fpesa/frontend/
cd /opt/fpesa/frontend/

npm install
npm run build

rm -rf /opt/fpesa/static/*
cp -r /opt/fpesa/frontend/dist/* /opt/fpesa/static/
