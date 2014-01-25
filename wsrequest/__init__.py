import json

from django.test.client import RequestFactory
from django.core.urlresolvers import resolve, Resolver404


__version__ = '0.1.1'

# Version synonym
VERSION = __version__


class WebSocketRequest(object):
    def __init__(self, message, factory_defaults=None):
        self.message = message
        self.factory_defaults = factory_defaults
        self.error = None

        self.validate()

    def get_url(self):
        return self.json_message.get('url')

    def get_method(self):
        return self.json_message.get('method', 'GET').lower()

    def get_data(self):
        return self.json_message.get('data', {})

    def get_token(self):
        return self.json_message.get('token')

    def set_error(self, error_message, status_code=400):
        self.error = {
            'error': error_message,
            'status_code': status_code
        }

    def validate(self):
        if self.is_valid_message():
            self.url = self.get_url()
            self.method = self.get_method()
            self.data = self.get_data()
            self.token = self.get_token()

            if self.url:
                self.get_url_resolver_match()
            else:
                self.set_error('Missing URL')

    def is_valid(self):
        return not self.error

    def is_valid_message(self):
        try:
            self.json_message = json.loads(self.message)
        except ValueError:
            self.set_error('Invalid formatted message.')

            return False

        return True

    def get_url_resolver_match(self):
        try:
            return resolve(self.url)
        except Resolver404:
            self.set_error('Resource not found.', 404)

    def get_factory(self):
        defaults = {}

        if self.token:
            defaults['HTTP_AUTHORIZATION'] = "JWT {0}".format(self.token)

        if self.factory_defaults:
            defaults.update(self.factory_defaults)

        return RequestFactory(**defaults)

    def get_request(self, factory):
        if self.method != 'get':
            self.data = json.dumps(self.data)

        return getattr(factory, self.method)(
            self.url,
            self.data,
            content_type='application/json'
        )

    def get_view(self, resolver_match, request):
        args = resolver_match.args
        kwargs = resolver_match.kwargs

        return resolver_match.func(request, *args, **kwargs)

    def get_response(self):
        if self.is_valid():
            factory = self.get_factory()
            request = self.get_request(factory)
            resolver_match = self.get_url_resolver_match()
            view = self.get_view(resolver_match, request)

            return view

        return self.error
