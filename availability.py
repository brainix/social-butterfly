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


class AvailabilityHandler(base.WebHandler):
    """ """

    def make_available(self):
        """ """
        return self._change_availability(True)

    def make_unavailable(self):
        """ """
        return self._change_availability(False)

    def _change_availability(self, available):
        """ """
        alice, state, body, confirmed = self._confirm_availability(available)
        if confirmed:
            if alice.partner is not None:
                if available:
                    body += ', but already had partner %s' % alice.partner
                    _log.error(body)
                else:
                    _log.debug(body + '; had partner %s' % alice.partner)
            else:
                _log.debug(body + '; had no partner')
        return alice, confirmed

    @base.WebHandler.run_in_transaction
    def _confirm_availability(self, available):
        """ """
        alice = self.get_account()
        state = 'available' if available else 'unavailable'
        body = '%s became %s' % (alice, state)
        confirmed = False
        if not alice.started:
            _log.info(body + ", but hasn't /started")
        elif alice.available == available:
            _log.info(body + ", but was already marked %s" % state)
        else:
            alice.available = available
            db.put(alice)
            confirmed = True
        return alice, state, body, confirmed
