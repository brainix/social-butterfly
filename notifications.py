#-----------------------------------------------------------------------------#
#   notifications.py                                                          #
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


import functools
import logging
import string

from google.appengine.api import xmpp

import models


_log = logging.getLogger(__name__)


class Notifications(object):
    """ """

    def _send_notification(method):
        """ """
        @functools.wraps(method)
        def wrap(alice, *args, **kwds):
            if alice:
                body = method(alice, *args, **kwds)
                status = xmpp.send_message(str(alice), body)
                assert status in (xmpp.NO_ERROR, xmpp.INVALID_JID,
                                  xmpp.OTHER_ERROR)
                return body
        return wrap

    def _send_presence(method):
        """ """
        @functools.wraps(method)
        def wrap(alice, *args, **kwds):
            if alice:
                status = method(alice, *args, **kwds)
                xmpp.send_presence(str(alice), status=status)
                return status
        return wrap

    @staticmethod
    @_send_notification
    def requires_account(alice):
        """ """
        body = 'To chat with strangers, sign up here:\n\n'
        body += 'http://social-butterfly.appspot.com/\n\n'
        body += 'It takes 5 seconds!'
        return body

    @staticmethod
    @_send_notification
    def help(alice):
        """ """
        body = 'Type /start to make yourself available for chat.\n\n'
        body += 'Type /next to chat with someone else.\n\n'
        body += 'Type /stop to make yourself unavailable for chat.\n\n'
        body += 'Type /help to see this help text.'
        return body

    @staticmethod
    @_send_notification
    def already_started(alice):
        """ """
        body = "You'd already made yourself available for chat.\n\n"
        alice_partner_key = models.Account.partner.get_value_for_datastore(alice)
        if alice_partner_key is None:
            body += 'Looking for a chat partner...'
        else:
            body += "And you're already chatting with a partner!"
        return body

    @staticmethod
    @_send_notification
    def started(alice):
        """Notify Alice that she's made herself available for chat."""
        body = "You've made yourself available for chat.\n\n"
        alice_partner_key = models.Account.partner.get_value_for_datastore(alice)
        if alice_partner_key is None:
            body += 'Looking for a chat partner...'
        else:
            body += 'Now chatting with a partner.  Say hello!'
        return body

    @staticmethod
    @_send_notification
    def chatting(alice):
        """Notify Alice that she's now chatting with a partner."""
        body = 'Now chatting with a partner.  Say hello!'
        return body

    @staticmethod
    @_send_notification
    def not_started(alice):
        """ """
        body = "You're not currently chatting with a partner, and you're "
        body += 'unavailable for chat.\n\nType /start to make yourself '
        body += 'available for chat.'
        return body

    @staticmethod
    @_send_notification
    def not_chatting(alice):
        """ """
        body = "You're not currently chatting with a partner, but you're "
        body += 'available for chat.\n\nLooking for a chat partner...'
        return body

    @staticmethod
    @_send_notification
    def nexted(alice):
        """Notify Alice that she's /nexted her partner."""
        body = "You've disconnected from your current chat partner.\n\n"
        alice_partner_key = models.Account.partner.get_value_for_datastore(alice)
        if alice_partner_key is None:
            body += 'Looking for a new chat partner...'
        else:
            body += 'Now chatting with a new partner.  Say hello!'
        return body

    @staticmethod
    @_send_notification
    def been_nexted(alice):
        """Notify Alice that her partner has /nexted her."""
        body = 'Your current chat partner has disconnected.\n\n'
        alice_partner_key = models.Account.partner.get_value_for_datastore(alice)
        if alice_partner_key is None:
            body += 'Looking for a new chat partner...'
        else:
            body += 'Now chatting with a new partner.  Say hello!'
        return body

    @staticmethod
    @_send_notification
    def already_stopped(alice):
        """ """
        body = "You'd already made yourself unavailable for chat."
        return body

    @staticmethod
    @_send_notification
    def stopped(alice):
        """Notify Alice that she's made herself unavailable for chat."""
        body = "You've made yourself unavailable for chat."
        return body

    @staticmethod
    @_send_notification
    def me(alice, body):
        """ """
        body = string.replace(body, '/me ', '', 1)
        body = 'Your partner ' + body
        return body

    @staticmethod
    @_send_notification
    def message(alice, body):
        """ """
        body = 'Partner: ' + body
        return body

    @staticmethod
    @_send_notification
    def undeliverable(alice):
        """Notify Alice that we couldn't deliver her message to her partner."""
        body = "Couldn't deliver your message to your chat partner.\n\n"
        body += 'Please try to send your message again, '
        body += 'or type /next to chat with someone else.'
        return body

    @staticmethod
    @_send_notification
    def unknown_command(alice):
        """ """
        body = "Unknown command"
        return body

    @staticmethod
    @_send_notification
    def who(alice):
        """ """
        bob = alice.partner
        try:
            bob_partner_key = models.Account.partner.get_value_for_datastore(bob)
        except AttributeError:
            bob_partner_key = None
        alice_key = alice.key()

        if bob is None or bob_partner_key != alice_key:
            body = "You're not currently chatting with a partner."
        else:
            body = "You're currently chatting with: %s" % bob
        return body

    @staticmethod
    @_send_presence
    def status(alice, stats):
        """ """
        status = '%s users total, ' % stats['num_users']
        status += '%s available for chat' % stats['num_active_users']
        return status
