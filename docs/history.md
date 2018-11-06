
History of joker-broker
=======================

### 0.1.12
* warns importing joker.broker.model
* DeclBase.representation_columns


### 0.1.11
* add DeclBase.find(), DeclBase.create_all_tables()

### 0.1.10
* add locate_standard_conf()


### 0.1.10
* RedisInterface.__repr__
* commit_or_rollback()


### 0.1.8
* RedisInterface.rekom_getsetx()


### 0.1.7
* add rb.store intended for persisted redis interface


### 0.1.6
* objective.Toolbox from a ResourceBroker instance
* DeclBase.load_many from cache pipeline and single sql execution


### 0.1.5
* redis set and get many items using pipeline


### 0.1.4
* follow [this rule][1] and keep session away from Model
* unify NoncachedBase and CachedBase into DeclBase


### 0.1.3
* `as_json_serializable` support fields selection
* `joker.cast.represent` for `NoncachedBase.__repr__`
* add `NoncachedBase.load_many()`


### 0.1.2cc
* apply `abc.abstractmethod` for `cls.get_resource_broker()`


### 0.1.1
* `rb.standby` randomly pickup from `rb.standby_interfaces`


### 0.1.0
* use `sqlalchemy.orm` and session


#### 0.0.14
* rename interfaces.redis to rediz (for python2 import error)
* python -m joker.broker.default


#### 0.0.13
* remove psycopg2 from requirements
* rewrite userdefault.py (parts moved to joker-cast)


#### 0.0.12
* bug fix: nullredis from_url returns None


#### 0.0.11
* AbstractModel.find(.., many=, limit=, offset=)
* add psycopg2 to requirements.txt


#### 0.0.10
* AbstractModel.delete: multiple primary keys
* AbstractModel.delete_cache


#### 0.0.9
* AbstractModel.find: update_cache() and mark_permanet()
* gen_random_string() now uses os.urandom, and is unexposed


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


[1] http://docs.sqlalchemy.org/en/latest/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
