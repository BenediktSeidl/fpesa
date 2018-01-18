--------
Overview
--------

Block Diagram
-------------

::

 +----------------------------------------------------------------+
 |              FRONTEND (browser based)                          |
 +----------------------------------------------------------------+
            |                    |                     |
            | HTTP               | HTTP/REST           | websockets
            |                    |                     |
 +----------------------------------------------------------------+
 |                 REVERSE PROXY (nginx)                          |
 +----------------------------------------------------------------+
            |                    |                     |
            | HTTP               | HTTP/REST           | websockets
            |                    |                     |
 +--------------------+  +------------------+  +------------------+
 | npm / static files |  | fpesa restmapper |  | fpesa liveupdate |
 +--------------------+  +------------------+  +------------------+
                                 |                     |
                                 |                     |
 +----------------------------------------------------------------+
 |                 MESSAGE BUS (rabbitmq)                         |
 +----------------------------------------------------------------+
                 |                                |
                 |                                |
 +------------------------------+  +------------------------------+
 | fpesa messages_post          |  | fpesa messages_get           |
 +------------------------------+  +------------------------------+
                 |                                |
                 |                                |
 +----------------------------------------------------------------+
 |                 DATABASE (postgresql)                          |
 +----------------------------------------------------------------+


Components
----------

Frontend
~~~~~~~~

The frontend is written in vue_, the important files are:

* ``frontend/src/components/Index.vue`` shows the live feed
* ``frontend/src/components/Saved.vue`` receives saved messages
* ``frontend/src/components/Dev.vue`` provides forms to test out the available
  API

As the frontend project was started with `vue-cli`_, with the `webpack template`_
it provides some fancy features like hot reloading of the frontend when files
where changed and code minification. In order to use the hot reloading the
built in webserver is used that can be run with ``npm run dev`` in the frontend
folder. The minification can be started by ``npm run build``. Latter is used by
the docker-compose setup.

.. _vue: https://vuejs.org/
.. _vue-cli: https://github.com/vuejs/vue-cli
.. _webpack template: http://vuejs-templates.github.io/webpack/

Reverse Proxy
~~~~~~~~~~~~~

nginx is used to bring the three web application under one domain: the
frontend, the websocket connection and the restapi are brought together by
nginx. Nginx is also responsible to strip away the ``/api/v1/`` prefix of the api
urls.

restmapper
~~~~~~~~~~

The restmapper webapplication is a generic rest to rabbitmq mapper. It is
configured by :py:func:`fpesa.restapp.get_endpoints`. See
:ref:`generic-restmapper` for a explanation. The idea was to reduce the
overhead when new rest endpoints are introduced.

liveupdate
~~~~~~~~~~

Liveupdate is also a mapper. It maps reabbitmq to websocket connections.

messages_post and messages_get
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

messages_post and messages_get are two consumers. messages_post is responsible
of getting messages off the bus and putting them in the database and
messages_get fetches messages from the database putting them on the message bus.


Data Flow
---------

Inserting Messages
~~~~~~~~~~~~~~~~~~

* **restmapper** transforms the request into a rabbitmq message but answers the
  request immediately with ``{}``. The message is put on the exchange
  ``/messages/:POST``.  The exchange is of the type fanout, this means all
  attached queues will receive all messages that where put on the exchange.
* **messages_post** reads from the queue ``/messages/:POST`` attached to the
  exchange ``/messages/:POST`` and puts the messages into the database.
* **liveupdate** reads from the queue ``liveupdate`` attached to the exchange
  ``/message/:POST`` and puts the messages into connected websockets

Getting messages
~~~~~~~~~~~~~~~~

* **restmapper** transforms the request into a rabbitmq message and waits for
  the response. rabbitmq does not natively support request response model, but
  it can be easily emulated as shown in the `RPC Tutorial`_. The restmapper
  uses the same principles. Therefore a exchange ``RPC`` is created. The
  restmapper creates a randomly named queue and attaches it to this exchange.
  When putting the message into the exchange ``/messages/:GET`` the restmapper
  specifies the routing key the worker has to use when answering to this
  request. The restmapper waits until the answer is provided in his queue ans
  responses the http request with this message.
* **messages_get** connects to the queue name ``/messages/:GET`` that is
  connected to the exchange ``/messages/:GET``. If a message arrives it sends it
  to to exchange ``RPC`` with the routing key provided in the request.

.. _RPC Tutorial: https://www.rabbitmq.com/tutorials/tutorial-six-python.html

Toughts
-------

Scalability
~~~~~~~~~~~

To provide true scalability all components used need to be run in parallel. The
reverse proxy layer can be scaled by providing multiple IPs for a sinlge DNS
entry. If the Server used is strong enough it's also possible to to configure
nginx so round robin between different upstreams, so the restmapper and
liveupdate web applications can be run in parallel per host. Both rabbitmq and
postgresql support some kind of cluster mode, so both of them should not become
a bottle neck. Last but not least it is supported to simply run multiple
instances of messages_post and messages_get worker.

Pagination
~~~~~~~~~~

I thought the user of the API might be more interested in recent messages than
the very first one, so the rest endpoint will return the messages sorted from
newest to oldest. As there is a live feed of messages displayed on the website
I concluded that there may be many messages in a short time, in order to
prevent seeing duplicated messages while iterating over all messages a
pagination identifier was introduced.

Tests
~~~~~

The tests are a mix of end to end tests and integrations tests.
