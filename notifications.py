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


class NotificationMixin(object):
    """ """

    def _send_notification(method):
        """ """
        @functools.wraps(method)
        def wrap(self, alice, *args, **kwds):
            if alice:
                body = method(self, alice, *args, **kwds)
                status = xmpp.send_message(str(alice), body)
                assert status in (xmpp.NO_ERROR, xmpp.INVALID_JID,
                                  xmpp.OTHER_ERROR)
                return body
        return wrap

    def _send_presence(method):
        """ """
        @functools.wraps(method)
        def wrap(self, alice, *args, **kwds):
            if alice:
                status = method(self, alice, *args, **kwds)
                xmpp.send_presence(str(alice), status=status)
                return status
        return wrap

    @_send_notification
    def notify_requires_account(self, alice):
        """ """
        body = 'To chat with strangers, sign up here:\n\n'
        body += 'http://social-butterfly.appspot.com/\n\n'
        body += 'It takes 5 seconds!'
        return body

    @_send_notification
    def send_help(self, alice):
        """ """
        body = 'Type /start to make yourself available for chat.\n\n'
        body += 'Type /next to chat with someone else.\n\n'
        body += 'Type /stop to make yourself unavailable for chat.\n\n'
        body += 'Type /help to see this help text.'
        return body

    @_send_notification
    def notify_already_started(self, alice):
        """ """
        body = "You'd already made yourself available for chat.\n\n"
        alice_partner_key = models.Account.partner.get_value_for_datastore(alice)
        if alice_partner_key is None:
            body += 'Looking for a chat partner...'
        else:
            body += "And you're already chatting with a partner!"
        return body

    @_send_notification
    def notify_started(self, alice):
        """Notify Alice that she's made herself available for chat."""
        body = "You've made yourself available for chat.\n\n"
        alice_partner_key = models.Account.partner.get_value_for_datastore(alice)
        if alice_partner_key is None:
            body += 'Looking for a chat partner...'
        else:
            body += 'Now chatting with a partner.  Say hello!'
        return body

    @_send_notification
    def notify_chatting(self, alice):
        """Notify Alice that she's now chatting with a partner."""
        body = 'Now chatting with a partner.  Say hello!'
        return body

    @_send_notification
    def notify_not_started(self, alice):
        """ """
        body = "You're not currently chatting with a partner, and you're "
        body += 'unavailable for chat.\n\nType /start to make yourself '
        body += 'available for chat.'
        return body

    @_send_notification
    def notify_not_chatting(self, alice):
        """ """
        body = "You're not currently chatting with a partner, but you're "
        body += 'available for chat.\n\nLooking for a chat partner...'
        return body

    @_send_notification
    def notify_nexted(self, alice):
        """Notify Alice that she's /nexted her partner."""
        body = "You've disconnected from your current chat partner.\n\n"
        alice_partner_key = models.Account.partner.get_value_for_datastore(alice)
        if alice_partner_key is None:
            body += 'Looking for a new chat partner...'
        else:
            body += 'Now chatting with a new partner.  Say hello!'
        return body

    @_send_notification
    def notify_been_nexted(self, alice):
        """Notify Alice that her partner has /nexted her."""
        body = 'Your current chat partner has disconnected.\n\n'
        alice_partner_key = models.Account.partner.get_value_for_datastore(alice)
        if alice_partner_key is None:
            body += 'Looking for a new chat partner...'
        else:
            body += 'Now chatting with a new partner.  Say hello!'
        return body

    @_send_notification
    def notify_already_stopped(self, alice):
        """ """
        body = "You'd already made yourself unavailable for chat."
        return body

    @_send_notification
    def notify_stopped(self, alice):
        """Notify Alice that she's made herself unavailable for chat."""
        body = "You've made yourself unavailable for chat."
        return body

    @_send_notification
    def send_me(self, alice, body):
        """ """
        body = string.replace(body, '/me ', '', 1)
        body = 'Your partner ' + body
        return body

    @_send_notification
    def send_message(self, alice, body):
        """ """
        body = 'Partner: ' + body
        return body

    @_send_notification
    def notify_undeliverable(self, alice):
        """Notify Alice that we couldn't deliver her message to her partner."""
        body = "Couldn't deliver your message to your chat partner.\n\n"
        body += 'Please try to send your message again, '
        body += 'or type /next to chat with someone else.'
        return body

    @_send_notification
    def notify_unknown_command(self, alice):
        """ """
        body = "Unknown command"
        return body

    @_send_notification
    def notify_who(self, alice):
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

    @_send_presence
    def send_status(self, alice, stats):
        """ """
        status = '%s users total, ' % stats['num_users']
        status += '%s available for chat' % stats['num_active_users']
        return status
