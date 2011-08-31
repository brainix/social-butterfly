#-----------------------------------------------------------------------------#
#   channels.py                                                               #
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
""" """


import datetime
import logging
import random

from google.appengine.api import channel
from google.appengine.ext import db
from google.appengine.ext import deferred

from config import CLIENT_IDS_KEY, NUM_RETRIES


_log = logging.getLogger(__name__)


class Channel(db.Model):
    """ """

    datetime = db.DateTimeProperty(required=True, indexed=False, auto_now=True)

    @classmethod
    def create(cls):
        """ """
        _log.info('creating channel')

        def txn():
            for retry in range(NUM_RETRIES):
                client_id = 'client' + str(random.randint(0, 10 ** 8 - 1))
                chan = cls.get_by_key_name(client_id)
                if chan is None:
                    chan = cls(key_name=client_id)
                    chan.put()
                    return client_id

        client_id = db.run_in_transaction(txn)
        if client_id is None:
            _log.warning("couldn't create channel; couldn't allocate ID")
        else:
            token = channel.create_channel(client_id)
            deferred.defer(cls.destroy, client_id, _countdown=2*60*60)
            _log.info('created channel %s, token %s' % (client_id, token))
            return token

    @classmethod
    def destroy(cls, client_id):
        """ """
        _log.info('destroying channel %s' % client_id)
        chan = cls.get_by_key_name(client_id)
        if chan is None:
            body = "couldn't destroy channel %s; already destroyed" % client_id
            _log.info(body)
        else:
            chan.delete()
            _log.info('destroyed channel %s' % client_id)

    @classmethod
    def broadcast(cls, json):
        """ """
        deferred.defer(cls._deferred_broadcast, json)

    @classmethod
    def _deferred_broadcast(cls, json):
        """ """
        keys = cls.all(keys_only=True)
        client_ids = [key.name() for key in keys]
        for client_id in client_ids:
            channel.send_message(client_id, json)

    @classmethod
    def flush(cls):
        """ """
        now = datetime.datetime.now()
        timeout = datetime.timedelta(hours=2)
        expired = now - timeout
        keys = cls.all(keys_only=True).filter('datetime <=', expired)
        db.delete(keys)
