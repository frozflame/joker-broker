from joker.broker.resource import ResourceBroker

__version__ = '0.0.3'


rb = None


def get_rb(path=None):
    import os
    from joker.broker import ResourceBroker
    global rb
    if not path:
        path = os.path.expanduser('~/.joker/broker.yml')
    if isinstance(rb, ResourceBroker):
        return rb
    rb = ResourceBroker.create(path)
    return rb
