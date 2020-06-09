
Changes of joker-broker
=======================

### 0.4.2
* Toolkit, Toolkit._get_resource_broker
* rename Toolbox to StandardToolkit (aliased Toolbox for backward compat.)
* deprecate form='p', use 'r' instead 

### 0.4.1
* change default conf path ~/.joker/broker/resources.yml
* remove lite section in in default conf

### 0.4.0
* Toolbox: do not close session in `__delete__` if created with external session passed in `__init__`
* DeclBase.create_all_tables: not allowed in non-abstract models
* DeclBase.find: rollback on error
* fix: FakeRedis has no attrib _db_num; rename redis_.py => redis.py
* use yaml.safe_load
* commit_or_rollback: do not close session
* rename redis_.py to redis.py
* remove rb.lite

### 0.3.0
* refactor: `ResourceBroker` is less verbose

### 0.2.3
* primary interface is not compulsory now

### 0.2.2
* add `Toolbox.bulk_insert`
* remove `j.b.default.locate_standard_conf`

### 0.2.1
* use `j.default` (package `joker`)


### 0.2.0
* remove `j.b.{model,logging,security}`
* rename `j.b.objective` to `j.b.base`
* rename `j.b.interfaces.rediz` to `j.b.interfaces.redis_`
* add `j.b.access.compute_hash`
* use `joker.space` (package `joker`)
