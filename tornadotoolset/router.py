class Router():
    def __init__(self):
        self._routes = []

    def mountHandler(self, path, handler):
        self._routes.append((path, handler))

    def getRoutes(self):
        return self._routes

    def mountRouter(self, base_path, router):
        for route in router.getRoutes():
            new_route = (base_path + route[0], route[1])
            self._routes.append(new_route)

    def enrollHandler(self, path):
        def decorator(handler):
            self.mountHandler(path, handler)
            return handler

        return decorator
