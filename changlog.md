
Change Log
----------

#### 0.0.5

* add methods `find` and `load_with` to `AbstractModel`


#### 0.0.4

* user directory (`~/.joker`) and default config file creation 
* bugfix: StaticInterface.get lacks *args so that `si.get('DEBUG', False)` fails 
* joker.broker.interfaces.sql -> ...sequel
