# fpesa

## Developing

*Instructions are tested with debian 9.1.0*

### Fetch this repository

```bash
# as root
apt-get install git
```

``` bash
git clone #TODO: add address
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

### Local Setup

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

## Functional Requirements

* python3
* rest endpoint for ingestion of messages
* save messages to disk
* rest endpoint for receiving all messages
* webpage with life feed of messages via websockets

* scalability
* tests


## Possible Solution

### Components

* messag bus
* revers proxy and load balancer
* producer with rest endpoint for ingestion
* consumer to write to database
* consumer for websockets bridge (or message bus with websocket support)
* producer/consumer with rest endpoint to receive all messages
* webapp with websockets

#### Reverse Proxy / Load balancer

* nginx
    * [+] relative lightwight
    * [+] experience

#### Messag bus

Requirements: scalability, stores messages until fetched

* mqtt
    * [-] single instance
    * [-] does not nativly support rpc/request-response messages
    * [+] lighwight
    * [+] experience
* zmq
    * [-] low level
    * [-] only building blocks
    * [-] cluster mode seems complicated
    * [+] lighwight
    * [+] experience
* redis
    * [-] needs special docker setup for cluster mode
      [[1]](https://redis.io/topics/cluster-tutorial#redis-cluster-and-docker)
    * [+] lighwight
* kafka
    * [-] huge project
    * [-] does not nativly support rpc/request-response messages
    * [+] multiple instances
    * [+] seems like a solid foundation when adding more features
* rabbitmq
    * [+] multiple instances
    * [+] rpc/request-response
    * [+] mqtt websockets plugin


#### Database

Requirements: scalability, JSON-support

* mongodb
    * [+] cluster support
    * [+] JSON-support
    * [+] fast prototyping
    * [+] experience
    * [-] lack of transactions ?
* postgresql
    * [+] JSON-support for undefined data
    * [+] solid foundation for additional features
    * [+] cluster support

To show only two databases is kind of risky. A vague gut instinct makes me
drifting away from mongodb to postgresql. If most of the application data may
fit into a classic relational database I would clearly prefere postgresql. As
the problems I have experienced with mognodb
([SERVER-1243](https://jira.mongodb.org/browse/SERVER-1243)) are resolved and I
don't have any Information about the datastructures I'm choosing mongodb.

But what about Pagination? As it seems we receive a lot of messages, a simple
offset count will get inaccurate results, if we decide to get the second page
after a while. #TODO!

#### Restapi

* flask
    * [+] huge community
    * [+] experience
    * [-] no websockets support

my first thought was to spereate the two restpoints in two single applications.
but it seems like the rest endpoints ist only a protocoll converter between
rest and the messagebus. so the rest api does not contain any bussiness logic.
so it should be possible to build a simple mapper, with a configuration which
rest endpoints exists and what parameter they take

#### Webapp

* vue
    * [+] experience
    * [+] lightweight
* angular
* angularjs
    * [+] experience
    * [-] deprecated
