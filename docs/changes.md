
Changes of joker-broker
=======================

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


[1] http://docs.sqlalchemy.org/en/latest/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
