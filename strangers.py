#-----------------------------------------------------------------------------#
#   strangers.py                                                              #
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

import models


_log = logging.getLogger(__name__)


class Strangers(object):
    """ """

    @staticmethod
    def _find_partner(alice, bob):
        """Alice is looking to chat.  Find her a partner, Carol.
        
        Bob was Alice's previous chat partner (if any).  Pair Alice with
        someone different this time (if possible).
        """
        carols = models.Account.get_users(keys_only=False, started=True,
                                          available=True, chatting=False,
                                          order=True)
        for carol in carols:
            # Make sure to not pair Alice with herself, and pair Alice with
            # someone other than Bob this time.
            if carol not in (alice, bob):

                # TODO: Use Google App Engine's XMPP API to ensure that Carol's
                # Google Talk status is available (and not idle or busy).
                #
                # Upon further research, I've discovered that it's currently
                # impossible to detect a user's status.  All we can see is
                # whether or not a user is online, but not if the user is
                # available, idle, or away.  Universal sadness.  :-(  For more
                # information, see:
                #     http://code.google.com/p/googleappengine/issues/detail?id=2238#c6

                # Hooray, we've found Alice a chat partner!
                return carol

        # Drat.  We couldn't find Alice a chat partner.  Either no one else is
        # available for chat, or everyone else available for chat already has a
        # partner.  Implicitly return None.

    @classmethod
    def _link_partners(cls, alice, bob):
        """Alice is looking to chat.  Find her a partner, and link them."""
        carol = cls._find_partner(alice, bob)
        alice.partner = carol
        if carol is not None:
            carol.partner = alice
        return alice, carol

    @staticmethod
    def _unlink_partners(alice):
        """Alice is not looking to chat.  Unlink her from her partner."""
        bob = alice.partner
        alice.partner = None
        if bob is not None:
            if bob.partner == alice:
                bob.partner = None
            else:
                bob = None
        return alice, bob

    @classmethod
    def _start_or_stop_chat(cls, alice, bob, start):
        """Alice is looking to either start or stop chatting.
        
        When Alice is looking to start chatting, we also pass Bob in.  Bob was
        Alice's previous chat partner (if any).  We pass Bob in so that we pair
        Alice with someone different this time (if possible).
        """
        if start:
            alice, carol = cls._link_partners(alice, bob)
        else:
            alice, carol = cls._unlink_partners(alice)
        accounts = [account for account in (alice, carol)
                    if account is not None]
        async = db.put_async(accounts)
        return alice, carol, async

    @classmethod
    def start_chat(cls, alice, bob):
        """ """
        return cls._start_or_stop_chat(alice, bob, True)

    @classmethod
    def stop_chat(cls, alice):
        """ """
        return cls._start_or_stop_chat(alice, None, False)

    @staticmethod
    def is_deliverable(alice):
        """Alice has typed an IM.  Determine if it can be delivered to Bob."""
        bob = alice.partner
        if bob is None:
            # Oops.  Alice doesn't have a chat partner.
            _log.warning('%s typed IM, but has no chat partner' % alice)
            return False

        bob_partner_key = models.Account.partner.get_value_for_datastore(bob)
        alice_key = alice.key()
        if bob_partner_key != alice_key:
            # Oops.  Alice thinks that her chat partner is Bob, but Bob doesn't
            # think that his chat partner is Alice.  This can happen because we
            # don't link/unlink chat partners transactionally, so we have to
            # check for this case every time anyone types a message.
            body = "%s typed IM, but %s's partner is %s and %s's partner is %s"
            _log.error(body % (alice, alice, bob, bob, bob.partner))
            return False

        # Nothing else can go wrong.  Alice's message must be deliverable to
        # Bob.
        _log.debug('%s typed IM, OK to deliver to %s' % (alice, bob))
        return True
