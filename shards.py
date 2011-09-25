#-----------------------------------------------------------------------------#
#   shards.py                                                                 #
#                                                                             #
#   Copyright (c) 2010-2011, Code A La Mode, original authors.                #
#                                                                             #
#       This file is part of Social Butterfly.                                #
#                                                                             #
#       Social Butterfly is free software; you can redistribute it and/or     #
#       modify it under the terms of the GNU General Public License as        #
#       published by the Free Software Foundation, either version 3 of the    #
#       License, or (at your option) any later version.                       #
#                                                                             #
#       Social Butterfly is distributed in the hope that it will be useful,   #
#       but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#       GNU General Public License for more details.                          #
#                                                                             #
#       You should have received a copy of the GNU General Public License     #
#       along with Social Butterfly.  If not, see:                            #
#           <http://www.gnu.org/licenses/>.                                   #
#-----------------------------------------------------------------------------#
"""Sharding counters.

Some of this code was written by Joe Gregorio and swiftly yoinked by Raj Shah.
For more information, see:
    http://code.google.com/appengine/articles/sharding_counters.html
"""


import logging
import random

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import deferred

from config import DEFAULT_NUM_SHARDS, NUM_RETRIES


_log = logging.getLogger(__name__)


class _ShardConfig(db.Model):
    """Tracks the number of shards for each named counter."""

    name = db.StringProperty(required=True)
    num_shards = db.IntegerProperty(default=DEFAULT_NUM_SHARDS, required=True)
    datetime = db.DateTimeProperty(required=True, indexed=False, auto_now_add=True)

    @classmethod
    def memcache_get_or_insert(cls, name):
        """ """
        key_name = name + '_config'
        config = memcache.get(key_name)
        if config is None:
            config = cls.get_or_insert(name, name=name)
            memcache.add(key_name, config)
        return config

    @classmethod
    def memcache_get(cls, name):
        """ """
        key_name = name + '_config'
        config = memcache.get(key_name)
        if config is None:
            try:
                config = cls.get(name)
            except db.BadKeyError:
                config = None
            else:
                memcache.add(key_name, config)
        return config


class Shard(db.Model):
    """Shards for each named counter."""

    name = db.StringProperty(required=True)
    count = db.IntegerProperty(required=True, default=0)
    datetime = db.DateTimeProperty(required=True, auto_now=True)

    @staticmethod
    def set_num_shards(name, num):
        """Increase the number of shards for a given counter to the given num.

        This method never decreases the number of shards.
        """
        def txn():
            config = _ShardConfig.get_or_insert(name, name=name)
            if config.num_shards < num:
                config.num_shards = num
                db.put_async(config)
            return config
        config = db.run_in_transaction(txn)

        client = memcache.Client()
        key_name = name + '_config'
        memcached_config = client.gets(key_name)
        if memcached_config is None:
            client.add(key_name, config)
        elif memcached_config.num_shards < config.num_shards:
            client.cas(key_name, config)

    @staticmethod
    def get_created_time(name):
        """Get the date/time when a named counter was first incremented.
        
        If a counter with the given name has not yet been incremented, this
        method returns None.
        """
        config = _ShardConfig.memcache_get(name)
        if config is not None:
            return config.datetime

    @classmethod
    def get_updated_time(cls, name):
        """Get the date/time when a named counter was last incremented.

        If a counter with the given name has not yet been incremented, this
        method returns None.
        """
        shard = cls.all().filter('name = ', name).order('-datetime').get()
        if shard is not None:
            return shard.datetime

    @classmethod
    def get_count(cls, name, increment=0):
        """Retrieve the value for a given sharded counter."""
        client = memcache.Client()
        total = client.gets(name)
        if total is None:
            _log.info('memcache miss when getting count for ' + name)
            config = _ShardConfig.memcache_get(name)
            if config is not None:
                total = increment
                shards = cls.all().filter('name = ', name)
                for shard in shards:
                    total += shard.count
                client.add(name, total)
        else:
            _log.debug('memcache hit when getting count for ' + name)
            if increment:
                total += increment
                client.cas(name, total)
        return total

    @classmethod
    def increment_count(cls, name, defer=False):
        """Increment the memcached total value for a given sharded counter."""
        if memcache.incr(name) is None:
            cls.get_count(name, increment=1)
        if defer:
            deferred.defer(cls._increment_count, name)
        else:
            cls._increment_count(name)

    @classmethod
    def _increment_count(cls, name):
        """Increment the memcached and datastored values for a shard."""
        client = memcache.Client()
        config = _ShardConfig.memcache_get_or_insert(name)
        index = random.randint(0, config.num_shards-1)
        key_name = name + str(index)

        def txn():
            for retry in range(NUM_RETRIES):
                shard = client.gets(key_name)
                method_name = 'cas'
                if shard is None:
                    shard = cls.get_by_key_name(key_name)
                    if shard is None:
                        shard = cls(key_name=key_name, name=name)
                    method_name = 'add'
                shard.count += 1
                if getattr(client, method_name)(key_name, shard):
                    db.put_async(shard)
                    return True
            return False
        success = db.run_in_transaction(txn)

    @classmethod
    def reset_count(cls, name):
        """Reset to 0 the value for a given sharded counter."""

        # First, delete all of the datastored shards, 500 at a time.  We do 500
        # at a time because the datastore limits batch operations to 500 per
        # batch.  For more information, see:
        #     http://stackoverflow.com/questions/3034327/google-app-engine-delete-until-count-0
        shards = cls.all(keys_only=True).filter('name = ', name)
        keys = shards.fetch(500)
        while keys:
            db.delete_async(keys)
            cursor = shards.cursor()
            shards = cls.all(keys_only=True).filter('name = ', name)
            shards = shards.with_cursor(cursor)
            keys = shards.fetch(500)

        # Next, delete the datastored configuration.
        config = _ShardConfig.memcache_get(name)
        if config is None:
            num_shards = 0
        else:
            num_shards = config.num_shards
            db.delete_async(config)

        # Finally, delete the memcached count, configuration, and shards.
        client = memcache.Client()
        key_names = [name, name + '_config']
        for index in range(num_shards):
            key_names.append(name + str(index))
        client.delete_multi_async(key_names)
