# -*- coding: utf-8 -*-
""" BaseTestCase for handler testing
"""

from requests import Request
from requests.cookies import RequestsCookieJar
from tornado.httpclient import HTTPRequest
from tornado.testing import AsyncHTTPTestCase
from tornadotoolset.pymonorm import get_database_from_env

import urllib

from backend.app import make_app


class HandlerTestCase(AsyncHTTPTestCase):
    def setUp(self):
        super().setUp()
        self._db = get_database_from_env()
        self._db.client.drop_database(self._db.name)
        self._cookies = RequestsCookieJar()

    def get_app(self):
        return make_app()

    def get_request(self, method, path, params={}, data={}, file={}):
        url = self.get_url(path)
        requests_req = Request(
            method,
            url,
            params=params,
            data=data,
            files=file,
            cookies=self._cookies).prepare()
        body = (None
                if method.upper() == 'GET' else (requests_req.body
                                                 if requests_req.body else ''))
        return HTTPRequest(
            url=requests_req.url,
            method=method,
            headers=requests_req.headers,
            body=body,
            validate_cert=False)

    def update_cookies(self, res):
        for cookie in res.headers.get_list('Set-Cookie'):
            key, val = cookie.split('=')[:2]
            self._cookies.set(key, val)

    async def _do_fetch(self, req):
        res = await self.http_client.fetch(req, raise_error=False)
        self.update_cookies(res)
        return res

    async def get(self, path, params={}):
        return await self._do_fetch(
            self.get_request('GET', path, params=params))

    async def post(self, path, data={}, file={}):
        return await self._do_fetch(
            self.get_request('POST', path, data=data, file=file))
