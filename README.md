# fpesa

fpesa is a python3.5 and python3.6 compatible webapp that provides a restapi to
save and receive messages and a websocket connection that receives live updates
when a new message is saved.

It comes with a simple web frontend that allows to test the features described
above.

## Overview

For getting an overview of the whole project, see
[docs/overview.rst](docs/overview.rst)

## Developing

*Instructions are tested with debian 9.1.0*

### Fetch this repository

```bash
# as root
apt-get install git
```

``` bash
git clone https://github.com/BenediktSeidl/fpesa.git
cd fpesa
```

### Run fpesa with `docker-compose`

Install docker according to the [offical docker
docs](https://docs.docker.com/engine/installation/linux/docker-ce/debian/)

```bash
# as root
apt-get install docker-compose
# grant access to docker for your personal user account
usermod -aG docker <your-developer-user>
```

```bash
# inside fpesa folder
docker-compose build  # only needed for first run or for updating changed code
docker-compose up
```
*`fpesa-frontend-build` and `fpesa-base` are ment to exit early.*

Wait until the static files are build and fpesa-frontend-build exits, then
open http://127.0.0.1:8099/

### Run fpesa locally

```bash
# as root
apt-get install python3 python-virtualenv postgresql rabbitmq-server nginx

# install nodejs
cd /tmp/
wget "https://nodejs.org/dist/v8.9.4/node-v8.9.4-linux-x64.tar.xz"
xz -d node-v8.9.4-linux-x64.tar.xz
tar -xf node-v8.9.4-linux-x64.tar
cd node-v8.9.4-linux-x64
cp -r {bin,include,lib,share} /usr/

# setup database for production and tests
su - postgres
psql
CREATE ROLE fpesa LOGIN PASSWORD 'fpesa';
CREATE DATABASE fpesa WITH OWNER = fpesa;
CREATE DATABASE fpesa_test WITH OWNER = fpesa;
\q
exit

# enable http api of rabbitmq for tests
rabbitmq-plugins enable rabbitmq_management
```

```bash
virtualenv --python=python3 v
source v/bin/activate
python setup.py develop
# running the tests to make sure everything works
pip install pytest requests
pytest tests
```

#### Starting the Components

All commands shown in this section show the developing setup. For instructions
on how to run the project in production see docker-compose.yml

When all Components are running you can access the frontend on
http://127.0.0.1:8888/

##### Frontend

```bash
cd frontend
npm install  # only once and after changes on package.json
npm run dev
```

##### Webserver

```bash
cd dev/nginx
./run.sh
```

###### Websocket Server

```
./v/bin/fpesa -v liveupdate
```

###### Restapi

```
./v/bin/fpesa -v restmapper
```

###### Worker for ingesting messages

```
./v/bin/fpesa -v messages_post
```

###### Worker for emitting messages

```
./v/bin/fpesa -v messages_get --debug
```

### Docs

```bash
source v/bin/activate
pip install -r docs/requirements.txt
sphinx-build docs docs/_build
# open docs/_build/index.html with your browser
```
