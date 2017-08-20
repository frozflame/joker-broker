joker-broker
============

Access resources conveniently.

Do this only once before you use `joker.broker`:
    
    from joker.broker import setup_userdir
    setup_userdir()
    
Use in an interactive shell like this:

    from joker.broker import get_resource_broker
    
    # use default conf file just created by setup_userdir()
    rb = get_resource_broker() 
    
    rb.lite.execute('create table users(id int, username text, email text)')
    
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
    
    tbl = rb.lite.get_table('users')
    ins = tbl.insert()
    ins.execute(records)
    
    list(tbl.select().execute()) 
