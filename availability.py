#-----------------------------------------------------------------------------#
#   availability.py                                                           #
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


import logging

from google.appengine.ext import db

import base


_log = logging.getLogger(__name__)


class AvailabilityHandler(base.WebRequestHandler):
    """ """

    @base.WebRequestHandler.run_in_transaction
    def make_available(self):
        """ """
        alice = self.request_to_account()
        made_available = False
        if not alice.started:
            _log.info("%s became available, but hasn't /started" % alice)
        elif alice.available:
            body = '%s became available, but was already marked available'
            _log.info(body % alice)
        else:
            if alice.partner is not None:
                body = '%s became available, but already had partner %s'
                _log.error(body % (alice, alice.partner))
            else:
                _log.debug('%s became available; had no partner' % alice)
                alice.available = True
                db.put(alice)
                made_available = True
        return alice, made_available

    @base.WebRequestHandler.run_in_transaction
    def make_unavailable(self):
        """ """
        alice = self.request_to_account()
        made_unavailable = False
        if not alice.started:
            _log.info("%s became unavailable, but hasn't /started" % alice)
        elif not alice.available:
            body = '%s became unavailable, but was already marked unavailable'
            _log.info(body % alice)
        else:
            if alice.partner is not None:
                body = '%s became unavailable; had partner %s'
                _log.debug(body % (alice, alice.partner))
            else:
                _log.debug('%s became unavailable; had no partner' % alice)
            alice.available = False
            db.put(alice)
            made_unavailable = True
        return alice, made_unavailable
