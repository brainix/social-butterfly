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
            memcache.set(key_name, config)
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
                memcache.set(key_name, config)
        return config

    def memcache_put(self):
        """ """
        key_name = self.name + '_config'
        memcache.set(key_name, self)
        db.put_async(self)

    @classmethod
    def memcache_delete(cls, name):
        """ """
        key_name = name + '_config'
        memcache.delete(key_name)
        try:
            config = cls.get(name)
        except db.BadKeyError:
            pass
        else:
            db.delete_async(config)


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
            config = _ShardConfig.memcache_get_or_insert(name)
            if config.num_shards < num:
                config.num_shards = num
                config.memcache_put()
        db.run_in_transaction(txn)

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
    def get_count(cls, name):
        """Retrieve the value for a given sharded counter."""
        total = memcache.get(name)
        if total is not None:
            _log.debug('memcache hit when getting count for ' + name)
        else:
            _log.info('memcache miss when getting count for ' + name)
            total = 0
            config = _ShardConfig.memcache_get(name)
            if config is not None:
                shards = cls.all().filter('name = ', name)
                for shard in shards:
                    total += shard.count
                memcache.set(name, total)
        return total

    @classmethod
    def increment_count(cls, name):
        """Increment the value for a given sharded counter."""
        client = memcache.Client()
        config = _ShardConfig.memcache_get_or_insert(name)
        index = random.randint(0, config.num_shards-1)
        key_name = name + str(index)

        def txn():
            for retry in range(NUM_RETRIES):
                shard = client.gets(key_name)
                if shard is None:
                    shard = cls.get_by_key_name(key_name)
                    if shard is None:
                        shard = cls(key_name=key_name, name=name)
                    shard.count += 1
                    client.add(key_name, shard)
                    shard.put()
                    return True
                else:
                    shard.count += 1
                    if client.cas(key_name, shard):
                        shard.put()
                        return True
            return False

        success = db.run_in_transaction(txn)
        memcache.incr(name, initial_value=0)

    @classmethod
    def reset_count(cls, name):
        """Reset to 0 the value for a given sharded counter."""

        # First, delete the memcached shards.
        config = _ShardConfig.memcache_get(name)
        if config:
            for index in range(config.num_shards):
                key_name = name + str(index)
                memcache.delete(key_name)

        # Next, delete the sharding counter's configuration.
        _ShardConfig.memcache_delete(name)

        # Next, delete all of the shards, 500 at a time.  We do 500 at a time
        # because the datastore limits batch operations to 500 per batch.  For
        # more information, see:
        #     http://stackoverflow.com/questions/3034327/google-app-engine-delete-until-count-0
        shards = cls.all(keys_only=True).filter('name = ', name)
        keys = shards.fetch(500)
        while keys:
            db.delete_async(keys)
            cursor = shards.cursor()
            shards = cls.all(keys_only=True).filter('name = ', name)
            shards = shards.with_cursor(cursor)
            keys = shards.fetch(500)

        # Finally, delete the memcached count.
        memcache.delete(name)
