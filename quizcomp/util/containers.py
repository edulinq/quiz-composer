class LayeredDict(object):
    """
    A Layered dict that holds sets of values as layers.
    Containers can push_layer() to add a new layer,
    and pop_layer() to remove the most recent layer.
    When a key is fetched, the layers will be checked (recent to oldest)
    and the first found instance will be returned (allowing new layers to mask old values).
    The initial layer cannot be popped (an error will be raised).
    """

    def __init__(self):
        self._layers = [{}]

    def push_layer(self):
        return self._layers.append({})

    def pop_layer(self):
        if (len(self._layers) == 1):
            raise ValueError("Cannot pop initial layer.")

        return self._layers.pop()

    def get(self, key, default_value = None):
        for layer in reversed(self._layers):
            if (key in layer):
                return layer[key]

        return default_value

    def set(self, key, item, base_layer = False):
        layer = self._layers[-1]
        if (base_layer):
            layer = self._layers[0]

        layer[key] = item

    def delete(self, key, base_layer = False):
        if (base_layer):
            del self._layers[-1][key]
            return

        for layer in reversed(self._layers):
            if (key in layer):
                del layer[key]

    def items(self):
        items = {}

        for layer in self._layers:
            for (key, value) in layer.items():
                items[key] = value

        return items.items()

    def to_pod(self):
        return self._layers

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, item):
        return self.set(key, item)

    def __delitem__(self, key):
        return self.delete(key)

    def __contains__(self, key):
        for layer in reversed(self._layers):
            if (key in layer):
                return True

        return False
