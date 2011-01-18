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


import logging

from google.appengine.api import xmpp


_log = logging.getLogger(__name__)


class Notifications(object):
    """ """

    def notify_already_started(self, alice):
        """ """
        body = "You'd already made yourself available for chat.\n\n"
        if alice.partner is None:
            body += 'Looking for a chat partner...'
        else:
            body += "And you're already chatting with a partner!"
        status = xmpp.send_message(str(alice), body)

    def notify_started(self, alice):
        """Notify Alice that she's made herself available for chat."""
        body = "You've made yourself available for chat.\n\n"
        if alice.partner is None:
            body += 'Looking for a chat partner...'
        else:
            body += 'Now chatting with a partner.  Say hello!'
        status = xmpp.send_message(str(alice), body)

    def notify_chatting(self, alice):
        """Notify Alice that she's now chatting with a partner."""
        body = 'Now chatting with a partner.  Say hello!'
        status = xmpp.send_message(str(alice), body)

    def notify_not_started(self, alice):
        """ """
        body = "You're not currently chatting with a partner, and you're "
        body += 'unavailable for chat.\n\nType /start to make yourself '
        body += 'available for chat.'
        status = xmpp.send_message(str(alice), body)

    def notify_not_chatting(self, alice):
        """ """
        body = "You're not currently chatting with a partner, but you're "
        body += 'available for chat.\n\nLooking for a chat partner...'
        status = xmpp.send_message(str(alice), body)

    def notify_nexted(self, alice):
        """Notify Alice that she's /nexted her partner."""
        body = "You've disconnected from your current chat partner.\n\n"
        if alice.partner is None:
            body += 'Looking for a new chat partner...'
        else:
            body += 'Now chatting with a new partner.  Say hello!'
        status = xmpp.send_message(str(alice), body)

    def notify_been_nexted(self, alice):
        """Notify Alice that her partner has /nexted her."""
        body = 'Your current chat partner has disconnected.\n\n'
        if alice.partner is None:
            body += 'Looking for a new chat partner...'
        else:
            body += 'Now chatting with a new partner.  Say hello!'
        status = xmpp.send_message(str(alice), body)

    def notify_already_stopped(self, alice):
        """ """
        body = "You'd already made yourself unavailable for chat."
        status = xmpp.send_message(str(alice), body)

    def notify_stopped(self, alice):
        """Notify Alice that she's made herself unavailable for chat."""
        body = "You've made yourself unavailable for chat."
        status = xmpp.send_message(str(alice), body)

    def notify_undeliverable(self, alice):
        """Notify Alice that we couldn't deliver her message to her partner."""
        body = "Couldn't deliver your message to your chat partner.\n\n"
        body += 'Please try to send your message again, '
        body += 'or type /next to chat with someone else.'
        status = xmpp.send_message(str(alice), body)