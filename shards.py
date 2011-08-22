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


class ShardConfig(db.Model):
    """Tracks the number of shards for each named counter."""

    name = db.StringProperty(required=True)
    num_shards = db.IntegerProperty(required=True, default=DEFAULT_NUM_SHARDS)

    @classmethod
    def increase_shards(cls, name, num):
        """Increase the number of shards for a given sharded counter.

        This method never decreases the number of shards.
        """
        config = cls.get_or_insert(name, name=name)
        def txn():
            if config.num_shards < num:
                config.num_shards = num
                config.put()
        db.run_in_transaction(txn)


class Shard(db.Model):
    """Shards for each named counter."""

    name = db.StringProperty(required=True)
    count = db.IntegerProperty(required=True, default=0)

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
    def increment(cls, name):
        """Increment the value for a given sharded counter."""
        config = ShardConfig.get_or_insert(name, name=name)
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
