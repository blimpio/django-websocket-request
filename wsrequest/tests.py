import json

from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import resolve
from django.views.generic import View
from django.conf.urls import patterns
from django.http import HttpResponse

from . import WebSocketRequest


class MockAPIView(View):
    def get(self, request, **kwargs):
        data = json.dumps({'foo': ['bar', 'baz']})
        response_kwargs = {
            'content_type': 'application/json'
        }

        return HttpResponse(data, **response_kwargs)


class RestrictedAPIView(View):
    def get(self, request, **kwargs):
        data = json.dumps(
            {
                'foo': ['bar', 'baz'],
                'HTTP_AUTHORIZATION': request.META.get('HTTP_AUTHORIZATION')
            }
        )
        response_kwargs = {
            'content_type': 'application/json'
        }

        return HttpResponse(data, **response_kwargs)

urlpatterns = patterns(
    '',
    (r'^api/mock/$', MockAPIView.as_view()),
    (r'^api/restricted/$', RestrictedAPIView.as_view()),
)


class WebSocketRequestTestCase(TestCase):
    urls = 'wsrequest.tests'

    def test_initilize_needs_message(self):
        with self.assertRaises(TypeError):
            WebSocketRequest()

    def test_initilize_with_message(self):
        message = json.dumps({'url': '/api/mock/'})
        request = WebSocketRequest(message)

        self.assertEqual(request.message, message)

    def test_get_url_should_return_url(self):
        message = json.dumps({'url': '/api/mock/'})
        request = WebSocketRequest(message)
        request.is_valid_message()

        self.assertEqual(request.get_url(), '/api/mock/')

    def test_get_url_should_return_none(self):
        message = json.dumps({})
        request = WebSocketRequest(message)
        request.is_valid_message()

        self.assertEqual(request.get_url(), None)

    def test_get_method_should_return_lower_method(self):
        message = json.dumps({'method': 'POST'})
        request = WebSocketRequest(message)
        request.is_valid_message()

        self.assertEqual(request.get_method(), 'post')

    def test_get_method_should_return_default_lower_method(self):
        message = json.dumps({})
        request = WebSocketRequest(message)
        request.is_valid_message()

        self.assertEqual(request.get_method(), 'get')

    def test_get_data_should_return_data(self):
        data = {
            'data': {
                'good': 1
            }
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)
        request.is_valid_message()

        self.assertEqual(request.get_data(), data['data'])

    def test_get_data_should_return_default_empty_dict(self):
        message = json.dumps({})
        request = WebSocketRequest(message)
        request.is_valid_message()

        self.assertEqual(request.get_data(), {})

    def test_get_token_should_return_token(self):
        data = {
            'token': 'abc123'
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)
        request.is_valid_message()

        self.assertEqual(request.get_token(), data['token'])

    def test_get_token_should_return_none(self):
        message = json.dumps({})
        request = WebSocketRequest(message)
        request.is_valid_message()

        self.assertEqual(request.get_token(), None)

    def test_set_error_should_set_error_message_and_code(self):
        message = json.dumps({})
        request = WebSocketRequest(message)
        request.set_error('Error message', 123)

        expected_error = {
            'error': 'Error message',
            'status_code': 123
        }

        self.assertEqual(request.error, expected_error)

    def test_is_valid_should_return_true_for_valid_message(self):
        data = {
            'url': '/api/mock/',
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)

        self.assertTrue(request.is_valid())

    def test_is_valid_should_return_false_for_invalid_message(self):
        data = {
            'url': '/api/nonexistent/',
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)

        self.assertFalse(request.is_valid())

    def test_is_valid_message_should_return_true_for_valid_message(self):
        data = {
            'url': '/api/mock/',
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)

        self.assertTrue(request.is_valid_message())

    def test_is_valid_message_should_return_false_for_invalid_message(self):
        request = WebSocketRequest('errormsg')

        self.assertFalse(request.is_valid_message())

    def test_is_valid_message_should_set_error_on_invalid_message(self):
        request = WebSocketRequest('{')
        request.is_valid_message()

        expected_error = {
            'status_code': 400,
            'error': 'Invalid formatted message.'
        }

        self.assertEqual(request.error, expected_error)

    def test_get_url_resolver_match_should_return_resolver_match(self):
        data = {
            'url': '/api/mock/',
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)
        expected_match = resolve('/api/mock/')
        request.is_valid()
        resolver_match = request.get_url_resolver_match()

        self.assertEqual(resolver_match.url_name, expected_match.url_name)

    def test_get_url_resolver_match_should_set_error_when_no_match(self):
        data = {
            'url': '/api/nonexistent/',
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)
        request.is_valid()
        request.get_url_resolver_match()

        expected_error = {
            'error': 'Resource not found.',
            'status_code': 404
        }

        self.assertEqual(request.error, expected_error)

    def test_get_factory_should_return_request_factory(self):
        data = {
            'url': '/api/mock/',
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)
        request.is_valid()

        factory = request.get_factory()

        self.assertTrue(isinstance(factory, RequestFactory))

    def test_get_factory_should_includ_auth_header_if_token_is_set(self):
        data = {
            'url': '/api/mock/',
            'token': 'abc'
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)
        request.is_valid()

        factory = request.get_factory()

        expected_headers = {
            'HTTP_AUTHORIZATION': 'JWT abc'
        }

        self.assertEqual(factory.defaults, expected_headers)

    def test_get_request_should_return_request_factory_request(self):
        data = {
            'url': '/api/mock/',
            'token': 'abc'
        }

        message = json.dumps(data)
        request = WebSocketRequest(message)
        request.is_valid()
        factory = request.get_factory()
        request = request.get_request(factory)

        self.assertEqual(request.path, '/api/mock/')

    def test_get_view_should_return_view_function(self):
        data = {
            'url': '/api/mock/',
            'token': 'abc'
        }

        message = json.dumps(data)
        wsrequest = WebSocketRequest(message)
        wsrequest.is_valid()
        resolver_match = wsrequest.get_url_resolver_match()
        factory = wsrequest.get_factory()
        request = wsrequest.get_request(factory)
        view = wsrequest.get_view(resolver_match, request)

        self.assertEqual(view.status_code, 200)

    def test_get_response_should_return_view_data(self):
        data = {
            'url': '/api/mock/',
            'token': 'abc'
        }

        message = json.dumps(data)
        wsrequest = WebSocketRequest(message)
        response = wsrequest.get_response()

        expected_response = {
            'foo': ['bar', 'baz']
        }

        json_content = json.loads(response.content.decode('utf-8'))

        self.assertEqual(json_content, expected_response)

    def test_get_response_should_return_error(self):
        data = {
            'url': '/api/mock/',
            'token': 'abc',
            'method': 'put'
        }

        message = json.dumps(data)
        wsrequest = WebSocketRequest(message)
        response = wsrequest.get_response()

        self.assertEqual(response.status_code, 405)

    def test_request_with_token_should_have_http_authorization(self):
        data = {
            'username': 'jpueblo',
            'password': 'abc123'
        }

        data = {
            'url': '/api/restricted/',
            'method': 'get',
            'token': 'mytoken'
        }

        message = json.dumps(data)
        wsrequest = WebSocketRequest(message)
        response = wsrequest.get_response()

        json_content = json.loads(response.content.decode('utf-8'))

        self.assertEqual(json_content['HTTP_AUTHORIZATION'], 'JWT mytoken')

    def test_request_without_token_shouldnt_have_http_authorization(self):
        data = {
            'url': '/api/restricted/',
            'method': 'get',
        }

        message = json.dumps(data)
        wsrequest = WebSocketRequest(message)
        response = wsrequest.get_response()

        json_content = json.loads(response.content.decode('utf-8'))

        self.assertEqual(json_content['HTTP_AUTHORIZATION'], None)
