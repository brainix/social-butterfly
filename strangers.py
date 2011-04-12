#-----------------------------------------------------------------------------#
#   strangers.py                                                              #
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

import models


_log = logging.getLogger(__name__)


class StrangerMixin(object):
    """ """

    def _get_users(self, started=True, available=True, chatting=False):
        """ """
        assert started in (None, False, True)
        assert available in (None, False, True)
        assert chatting in (None, False, True)

        carols = models.Account.all()
        if started is not None:
            carols = carols.filter('started =', started)
        if available is not None:
            carols = carols.filter('available =', available)
        if chatting == False:
            carols = carols.filter('partner =', None)
        elif chatting == True:
            carols = carols.filter('partner !=', None)
            carols.order('partner')
        carols = carols.order('datetime')

        return carols

    def num_active_users(self):
        """Return the number of started and available users."""
        carols = self._get_users(started=True, available=True, chatting=None)
        num_carols = carols.count()
        return num_carols

    def _find_partner(self, alice, bob):
        """Alice is looking to chat.  Find her a partner, Carol.
        
        Bob was Alice's previous chat partner (if any).  Pair Alice with
        someone different this time (if possible).
        """
        carols = self._get_users(started=True, available=True, chatting=False)
        only_one = carols.count(2) == 1

        for carol in carols:
            # Make sure to not pair Alice with herself.
            if carol != alice:
                # Try to pair Alice with someone other than Bob this time,
                # unless Bob is the only other user available for chat.
                if carol != bob or only_one:
                    # Hooray, we've found Alice a chat partner!
                    return carol

        # Drat.  We couldn't find Alice a chat partner.  Either no one else is
        # available for chat, or everyone else available for chat already has a
        # partner.  Implicitly return None.

    def _link_partners(self, alice, bob):
        """Alice is looking to chat.  Find her a partner, and link them."""
        carol = self._find_partner(alice, bob)
        alice.partner = carol
        if carol is not None:
            carol.partner = alice
        return alice, carol

    def _unlink_partners(self, alice):
        """Alice is not looking to chat.  Unlink her from her partner."""
        bob = alice.partner
        alice.partner = None
        if bob is not None:
            if bob.partner == alice:
                bob.partner = None
            else:
                bob = None
        return alice, bob

    def _start_or_stop_chat(self, alice, bob=None, start=True):
        """Alice is looking to either start or stop chatting.
        
        When Alice is looking to start chatting, we also pass Bob in.  Bob was
        Alice's previous chat partner (if any).  We pass Bob in so that we pair
        Alice with someone different this time (if possible).
        """
        if start:
            alice, carol = self._link_partners(alice, bob)
        else:
            alice, carol = self._unlink_partners(alice)
        accounts = [account for account in (alice, carol)
                    if account is not None]
        db.put(accounts)
        return alice, carol

    def start_chat(self, alice, bob):
        """ """
        return self._start_or_stop_chat(alice, bob=bob, start=True)

    def stop_chat(self, alice):
        """ """
        return self._start_or_stop_chat(alice, start=False)
