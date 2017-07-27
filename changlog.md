
Change Log
----------

#### 0.0.8

* AbstractModel._update_cache -> AbstractModel.update_cache
* remove AbstractModel.load_with 
* new AbstractModel.find, returning objects in stead of pk

#### 0.0.7

* move MultiFernetWrapper away to joker.masquerade 

#### 0.0.6

* add SQLInterface.execute
* remove redundant Table cache from SQLInterface, which is done by SQLAlchemy already
* remove client_encoding for sqlite
* start to write README
* setup_userdir, get_resource_broker. No magic at broker.__init__
* less redundancy creating a new @property interface


#### 0.0.5

* add methods `find` and `load_with` to `AbstractModel`


#### 0.0.4

* user directory (`~/.joker`) and default config file creation 
* bugfix: StaticInterface.get lacks *args so that `si.get('DEBUG', False)` fails 
* joker.broker.interfaces.sql -> ...sequel
