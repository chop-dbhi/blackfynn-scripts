# -*- coding: utf-8 -*-
 
import json
import base64
import logging
import settings
import requests
from concurrent.futures import TimeoutError
from requests_futures.sessions import FuturesSession

# blackfynn
from blackfynn.utils import log
from blackfynn.models import User


class UnauthorizedException(Exception):
    pass


class BlackfynnRequest(object):
    def __init__(self, func, uri, *args, **kwargs):
        self._func = func
        self._uri = uri
        self._args = args
        self._kwargs = kwargs
        self._request = None
        self.call()

    def _handle_response(self, sess, resp):
        log.debug("resp = {}".format(resp))
        log.debug("resp.content = {}".format(resp.content))
        if resp.status_code in [requests.codes.forbidden, requests.codes.unauthorized]:
            raise UnauthorizedException()

        if not resp.status_code in [requests.codes.ok, requests.codes.created]:
            msg = "status: {} method: {} url:{} responseBody: {}".format(
                resp.status_code, resp.request.method, resp.url, resp.content)
            log.error(msg)
            resp.raise_for_status()
        try:
            # return object from json
            resp.data = json.loads(resp.content)
        except:
            # if not json, still return response content
            resp.data = resp.content

    def call(self):
        self._request = self._func(self._uri, background_callback=self._handle_response, *self._args, **self._kwargs)
        return self

    def result(self,*args, **kwargs):
        return self._request.result(*args, **kwargs)


class ClientSession(object):
    def __init__(self, user, password, host=None, streaming_host=None):
        self._session = None
        self._host = host
        self._streaming_host = streaming_host
        self._token = None
        self._context = None
        self._user = user
        self._password = base64.b64encode(password)
        self.profile = None

    def login(self):
        """
        Use credentials to connect to Blackfynn platform. Session token returned
        from API call is used for all subsequent API calls.
        """
        # make login request
        auth = {'email': self._user, 'password': base64.b64decode(self._password)}
        resp = self._post('/account/login', data=auth)

        # parse response, update session
        self.token = resp['sessionToken']
        self.profile = User.from_dict(resp, object_key='profile')

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value
        self.session.headers.update({'X-SESSION-ID': value})

    @property
    def session(self):
        """
        Make requests-futures work within threaded/distributed environment.
        """
        if not hasattr(self._session, 'session'):
            self._session = FuturesSession(max_workers=4)
            self._session.headers.update({'X-SESSION-ID': self._token})

            if self._context is not None:
                self._session.headers.update({'X-ORGANIZATION-ID': self._context.id})

        return self._session

    def _make_call(self, func, uri, *args, **kwargs):
        log.debug("uri = {}".format(uri))
        log.debug("args = {}".format(args))
        log.debug("kwargs = {}".format(kwargs))
        return BlackfynnRequest(func, uri, *args, **kwargs)

    def _call(self, method, endpoint, base='', async=False, *args, **kwargs):
        if method == 'get':
            func = self.session.get
        elif method == 'put':
            func = self.session.put
        elif method == 'post':
            func = self.session.post
        elif method == 'delete':
            func = self.session.delete

        # serialize data
        if 'data' in kwargs:
            kwargs['data'] = json.dumps(kwargs['data'])

        # we might specify a different host
        if 'host' in kwargs:
            host = kwargs['host']
            kwargs.pop('host')
        else:
            host = self._host

        # call endpoint
        uri = self._uri(endpoint, base=base, host=host)
        req = self._make_call(func, uri, *args, **kwargs)

        if async:
            return req
        else:
            return self._get_response(req)

    def _uri(self, endpoint, base, host=None):
        if host is None:
            host = self._host
        return '{}{}{}'.format(host, base, endpoint)

    def _get(self, endpoint, async=False, *args, **kwargs):
        return self._call('get', endpoint, async=async, *args, **kwargs)

    def _post(self, endpoint, async=False, *args, **kwargs):
        return self._call('post', endpoint, async=async, *args, **kwargs)

    def _put(self, endpoint, async=False, *args, **kwargs):
        return self._call('put', endpoint, async=async, *args, **kwargs)

    def _del(self, endpoint, async=False, *args, **kwargs):
        return self._call('delete', endpoint, async=async, *args, **kwargs)

    def _get_result(self, req, count=0):
        try:
            resp = req.result(timeout=settings.max_request_time)
        except TimeoutError as e:
            if count < settings.max_request_timeout_retries:
                # timeout! trying again...
                resp = self._get_result(req.call(), count=count+1)
        except UnauthorizedException as e:
            # try refreshing the session
            if self._token is not None and count==0:
                self.login()
                # re-request
                resp = self._get_result(req.call(), count=count+1)
            else:
                raise e
        return resp

    def _get_response(self, req):
        resp = self._get_result(req)
        return resp.data

    def register(self, *components):
        """
        Register API component with session. Components should all be of 
        APIBase type and have a name and base_uri property. 

        The registered component will have reference to base session to 
        make higher-level calls outside of its own scope, if needed.
        """
        # initialize
        for component in components:
            c = component(session=self)
            assert len(component.name) > 1, "Invalid API component name"
            # component is accessible via session.(name)
            self.__dict__.update({ component.name: c })

    @property
    def headers(self):
        return self.session.headers
