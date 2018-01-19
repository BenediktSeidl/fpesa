---
API
---

.. automodule:: fpesa
   :members:

REST
----

Errors
~~~~~~

If there is a serverside Problem or the client sends unexpected data the Server
answers with a http staus code ``500`` and the following json:

.. code-block:: javascript

  {
    "error" {
      "code": 500,
      "description": <string>
    }
  }

In most cases the key description holds a human readable explanation of the
problem

Endpoints
~~~~~~~~~

.. object:: GET /api/v1/messages/

   **Request Parameter:**

   * paginationId
   * offset
   * limit

   **Returns:**

    .. code-block:: javascript

      {
        "offset": <int>,
        "limit": <int>,
        "paginationId": <int>,
        "total": <int>,
        "messages": [
            <Object>,
            ...
        ]
      }

   See :py:func:`fpesa.message.message_get`


.. object:: POST /api/v1/messages/

   **Request Data**

   .. code-block:: javascript

     <Object>

   **Returns:**

   .. code-block:: javascript

     {}

   See :py:func:`fpesa.message.message_post`

Websocket
---------

The websocket connection is reachable at ``/ws/v1/`` and will send json
decodable objects that consist of the messages as inserted via ``POST
/api/v1/messages/``
