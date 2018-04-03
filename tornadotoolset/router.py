# -*- coding: utf-8 -*-
""" Tornado Router helper
Example:

route_user = Router()

@route.enroll_handler(r'/login/?')
class LoginHandler(...):
    pass

route_root = Router()
route_root.mount_handler(r'/user', route_user)
"""


class Router():
    def __init__(self):
        self._routes = []

    def mount_handler(self, path, handler, data=None):
        self._routes.append((path, handler, data) if data else (path, handler))

    def get_routes(self):
        return self._routes

    def mount_router(self, base_path, router):
        for route in router.get_routes():
            self.mount_handler(base_path + route[0], *route[1:])

    def enroll_handler(self, path, data=None):
        def decorator(handler):
            self.mount_handler(path, handler, data)
            return handler

        return decorator
