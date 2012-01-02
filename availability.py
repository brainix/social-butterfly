#-----------------------------------------------------------------------------#
#   availability.py                                                           #
#                                                                             #
#   Copyright (c) 2010-2012, Code A La Mode, original authors.                #
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


class AvailabilityHandler(base.WebHandler):
    """ """

    def make_available(self, available):
        """Make Alice either available or unavailable for chat.
        
        Return Alice's account entity, and whether or not we change Alice's
        available status.  (We may not end up changing Alice's available status
        for example, if she's already unavailable and someone calls this method
        to make her unavailable.)
        """
        alice, changed = self._change_available(available)
        self._log_available(available, alice, changed)
        return alice, changed

    @base.BaseHandler.run_in_transaction
    def _change_available(self, available):
        """ """
        alice = self.get_account(cache=False)
        change = alice is not None and \
                 alice.started and \
                 alice.available != available
        if change:
            alice.available = available
            db.put(alice)
        return alice, change

    def _log_available(self, available, alice, changed):
        """ """
        state = 'available' if available else 'unavailable'
        if alice is None:
            body = 'someone without an account subscribed, became %s?' % state
            _log.info(body)
        else:
            body = str(alice) + ' became ' + state
            if not changed:
                if not alice.started:
                    _log.info(body + ", but hasn't /started")
                elif alice.available == available:
                    _log.info(body + ", but was already marked " + state)
            else:
                if alice.partner is not None:
                    if available:
                        body += ', but already had partner %s' % alice.partner
                        _log.error(body)
                    else:
                        _log.debug(body + '; had partner %s' % alice.partner)
                else:
                    _log.debug(body + '; had no partner')
