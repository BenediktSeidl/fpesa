# fpesa

## Developing

### Starting all Components

All commands shown in this section show the developing setup. For instructions
on how to run the project in production see #TODO

When all Components are running you can access the frontend with
http://127.0.0.1:8888/

#### Frontend

```bash
cd frontend
npm install  # only once
npm run dev
```

#### Webserver

```bash
cd dev/nginx
./run.sh
```

### Tests

```bash
rabbitmq-plugins enable rabbitmq_management
pip install pytest requests
py.test
```

### Docs

```bash
sphinx-build doc doc/_build
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
