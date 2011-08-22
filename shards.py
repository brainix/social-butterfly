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

from config import DEFAULT_NUM_SHARDS


_log = logging.getLogger(__name__)


class _ShardConfig(db.Model):
    """Tracks the number of shards for each named counter."""

    name = db.StringProperty(required=True)
    num_shards = db.IntegerProperty(default=DEFAULT_NUM_SHARDS, required=True)
    datetime = db.DateTimeProperty(required=True, indexed=False, auto_now=True)


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
        config = _ShardConfig.get_or_insert(name, name=name)
        def txn():
            if config.num_shards < num:
                config.num_shards = num
                config.put()
        db.run_in_transaction(txn)

    @staticmethod
    def get_created_time(name):
        """ """
        config = _ShardConfig.get(name)
        if config is None:
            return None
        else:
            return config.datetime

    @classmethod
    def get_updated_time(cls, name):
        """ """
        shard = cls.all().filter('name = ', name).order('-datetime').get()
        if shard is None:
            return None
        else:
            return shard.datetime

    @classmethod
    def get_count(cls, name):
        """Retrieve the value for a given sharded counter."""
        total = memcache.get(name)
        if total is None:
            shards = cls.all().filter('name = ', name)
            total = 0
            for shard in shards:
                total += shard.count
            memcache.add(name, total)
        return total

    @classmethod
    def increment_count(cls, name):
        """Increment the value for a given sharded counter."""
        config = _ShardConfig.get_or_insert(name, name=name)
        def txn():
            index = random.randint(0, config.num_shards - 1)
            key_name = name + str(index)
            shard = cls.get_by_key_name(key_name)
            if shard is None:
                shard = cls(key_name=key_name, name=name)
            shard.count += 1
            shard.put()
        db.run_in_transaction(txn)
        memcache.incr(name)

    @classmethod
    def reset_count(cls, name):
        """Reset to 0 the value for a given sharded counter.
        
        For more information, see:
            http://stackoverflow.com/questions/3034327/google-app-engine-delete-until-count-0
        """
        config = _ShardConfig.get(name)
        if config is not None:
            config.delete()

        shards = cls.all(keys_only=True).filter('name = ', name)
        keys = shards.fetch(500)
        while keys:
            db.delete(keys)
            cursor = shards.cursor()
            shards = cls.all(keys_only=True).filter('name = ', name)
            shards = shards.with_cursor(cursor)
            keys = shards.fetch(500)

        memcache.delete(name)
