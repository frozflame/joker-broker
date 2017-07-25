from joker.broker.resource import ResourceBroker


__version__ = '0.0.6'


def setup_userdir():
    from joker.broker.userdefault import dump_default_conf
    dump_default_conf()


def get_resource_broker(path=None):
    import os
    from joker.broker import ResourceBroker
    if not path:
        path = os.path.expanduser('~/.joker/broker.yml')
    return ResourceBroker.create(path)
