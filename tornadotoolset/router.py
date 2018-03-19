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

    def mount_handler(self, path, handler):
        self._routes.append((path, handler))

    def get_routes(self):
        return self._routes

    def mount_router(self, base_path, router):
        for route in router.get_routes():
            new_route = (base_path + route[0], route[1])
            self._routes.append(new_route)

    def enroll_handler(self, path):
        def decorator(handler):
            self.mount_handler(path, handler)
            return handler

        return decorator
