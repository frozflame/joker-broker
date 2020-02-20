joker-broker
============

Access resources conveniently.


### Installation

Install with `pip`:

    python3 -m pip install joker-broker

Create default config file at `~/.joker/broker/resources.yml`

    python3 -m joker.broker.default
    
    
### Usage

Use in an interactive shell like this:

    from joker.broker import get_resource_broker
    
    # use default conf file just created by `python3 -m joker.broker.default`
    rb = get_resource_broker() 
    
    rb.primary.execute('create table users(id int, username text, email text)')
    
    records = [
        {
            'id': 1, 
            'username': 'Alice', 
            'email': 'alice@example.com',
        },
        {
            'id': 2, 
            'username': 'Bob', 
            'email': 'bob@example.com',
        }
    ]
    
    tbl = rb.primary.get_table('users')
    ins = tbl.insert()
    ins.execute(records)
    
    list(tbl.select().execute())
    
    
Use `ResourceBroker` for your project:
    
    _resource_broker = None

    def get_resource_broker():
        global _resource_broker
        if _resource_broker is None:
            path = '/data/myapp/broker.yml'  # path to your conf
            _resource_broker = ResourceBroker.create(path)
        return _resource_broker
