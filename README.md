# django-websocket-request

[![Build Status](https://travis-ci.org/GetBlimp/django-websocket-request.png?branch=master)](https://travis-ci.org/GetBlimp/django-websocket-request) [![PyPI version](https://badge.fury.io/py/django-websocket-request.png)](http://badge.fury.io/py/django-websocket-request)

## Overview
This package provides support for transport agnostic routing to allow the Django's request/response lifecycle to automatically WebSocket messages. It borrows a WebSocket message format from [Sails.js](http://sailsjs.org/).

**Note**: This is more of an experiment than anything else. We are not using this in any projects. This has a huge limitation, sending messages on events initiated by the server is not possible, so you're only able to do one way communication from the browser to the server.

## Installation

Install using `pip`...

```
$ pip install django-websocket-request
```

## Usage

### ws.py

```python
# Set Django Environment
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_project.settings'

from wsrequest import WebSocketRequest

message = '{"method": "GET", "url": "/api/projects/"}'
request = WebSocketRequest(message)
response = request.get_response()

print(response.content)

```

### WebSocket message format

The method key can be any HTTP method: GET, POST, PUT, DELETE, PATCH, HEAD, or OPTIONS. The url key is an absolute URL without the domain name. The data key is an optional dictionary in which the key-value pairs in used to create the method’s data payload. The token key is also optional, and used to recreate an HTTP Authorization header, Authorization: JWT YOUR_TOKEN_HERE. If you're using Django REST framework, you might like to check out [django-rest-framework-jwt](https://github.com/GetBlimp/django-rest-framework-jwt).

```json
{
  "method": "POST",
  "url": "/api/companies/",
  "data": {
    "name": "Acme Inc."
  },
  "token": "MY_JSON_WEB_TOKEN"
}
```

## Live Demo

Check out [GetBlimp/django-websocket-request-example](https://github.com/GetBlimp/django-websocket-request-example) for an example implementation and a live demo.

## Example implementation with sockjs + tornado
```python
import os
import json

from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection

# Set Django Environment
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_project.settings'

from wsrequest import WebSocketRequest


class RESTAPIConnection(SockJSConnection):
    def on_open(self, info):
        self.send(json.dumps({'connected': True}))

    def on_message(self, data):
        response = WebSocketRequest(data).get_response()
        self.send(response.content)


if __name__ == '__main__':
    import logging

    port = 8080

    logging.getLogger().setLevel(logging.INFO)

    Router = SockJSRouter(RESTAPIConnection, '/ws/api')

    app = web.Application(Router.urls)
    app.listen(port)

    logging.info(" [*] Listening on 0.0.0.0:{}".format(port))

    ioloop.IOLoop.instance().start()

```
