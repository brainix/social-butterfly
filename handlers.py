#------------------------------------------------------------------------------#
#   handlers.py                                                                #
#                                                                              #
#   Copyright (c) 2010, Code A La Mode, original authors.                      #
#                                                                              #
#       This file is part of social-butterfly.                                 #
#                                                                              #
#       social-butterfly is free software; you can redistribute it and/or      #
#       modify it under the terms of the GNU General Public License as         #
#       published by the Free Software Foundation, either version 3 of the     #
#       License, or (at your option) any later version.                        #
#                                                                              #
#       social-butterfly is distributed in the hope that it will be useful,    #
#       but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#       GNU General Public License for more details.                           #
#                                                                              #
#       You should have received a copy of the GNU General Public License      #
#       along with social-butterfly.  If not, see:                             #
#           <http://www.gnu.org/licenses/>.                                    #
#------------------------------------------------------------------------------#
"""Google App Engine request handlers (concrete implementation classes)."""


import logging
import os

from google.appengine.api import xmpp
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from config import DEBUG, TEMPLATES
import base
import decorators
import models


_log = logging.getLogger(__name__)


class NotFound(base.WebRequestHandler):
    """Request handler to serve a 404: Not Found error page."""

    def get(self, *args, **kwds):
        """Someone has issued a GET request on a nonexistent URL."""
        return self._serve_error(404)


class Home(base.WebRequestHandler):
    """Request handler to serve the homepage."""

    def get(self):
        """Serve the homepage."""
        path, debug = os.path.join(TEMPLATES, 'home.html'), DEBUG
        title = 'chat with strangers'
        self.response.out.write(template.render(path, locals(), debug=DEBUG))

    def post(self):
        """ """
        handle = self.request.get('handle')
        handle = db.IM('xmpp', handle)
        key_name = models.Account.key_name(handle.address)
        account = models.Account.get_by_key_name(key_name)
        if account is None:
            account = models.Account(key_name=key_name, handle=handle,
                                     online=False)
            account.put()
        xmpp.send_invite(handle.address)


class Chat(base.ChatRequestHandler):
    """Request handler to respond to XMPP messages."""

    @decorators.require_account()
    def help_command(self, message=None):
        """Alice has typed /help."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /help' % alice)
        body = 'Type /online to make yourself available for chat.\n\n'
        body += 'Type /next to chat with someone else.\n\n'
        body += 'Type /offline to make yourself unavailable for chat.'
        message.reply(body)

    @decorators.require_account(online=False)
    def online_command(self, message=None):
        """Alice has typed /online."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /online' % alice)
        alice.online = True
        alice, bob = self.start_chat(alice)

        # Notify Alice.
        body = "You've made yourself available for chat.\n\n"
        if bob is None:
            body += 'Looking for a chat partner...'
            message.reply(body)
        else:
            body += 'Now chatting with a partner.  Say hello!'
            message.reply(body)

        # Notify Bob.
        if bob is not None:
            body = 'Now chatting with a partner.  Say hello!'
            xmpp.send_message(str(bob), body)

    @decorators.require_account(online=True)
    def next_command(self, message=None):
        """Alice has typed /next."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /next' % alice)
        alice, bob = self.stop_chat(alice)
        alice, carol = self.start_chat(alice)
        if bob is None:
            dave = None
        elif bob == carol:
            dave = alice
        else:
            bob, dave = self.start_chat(bob)

        # Notify Alice.
        body = "You've disconnected from your current chat partner.\n\n"
        if carol is None:
            body += 'Looking for a new chat partner...'
        else:
            body += 'Now chatting with a new partner.  Say hello!'
        message.reply(body)

        # Notify Bob.
        if bob is not None and bob not in (alice,):
            body = 'Your current chat partner has disconnected.\n\n'
            if dave is None:
                body += 'Looking for a new chat partner...'
            else:
                body += 'Now chatting with a new partner.  Say hello!'
            xmpp.send_message(str(bob), body)

        # Notify Carol.
        if carol is not None and carol not in (alice, bob):
            body = 'Now chatting with a partner.  Say hello!'
            xmpp.send_message(str(carol), body)

        # Notify Dave.
        if dave is not None and dave not in (alice, bob, carol):
            body = 'Now chatting with a partner.  Say hello!'
            xmpp.send_message(str(dave), body)

    @decorators.require_account(online=True)
    def offline_command(self, message=None):
        """Alice has typed /offline."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /offline' % alice)
        alice.online = False
        alice, bob = self.stop_chat(alice)
        if bob is None:
            carol = None
        else:
            bob, carol = self.start_chat(bob)

        # Notify Alice.
        body = "You've made yourself unavailable for chat."
        message.reply(body)

        # Notify Bob.
        if bob is not None and bob not in (alice,):
            body = 'Your current chat partner has disconnected.\n\n'
            if carol is None:
                body += 'Looking for a new chat partner...'
                xmpp.send_message(str(bob), body)
            else:
                body += 'Now chatting with a new partner.  Say hello!'
                message.reply(body)

        # Notify Carol.
        if carol is not None and carol not in (alice, bob):
            body = 'Now chatting with a partner.  Say hello!'
            xmpp.send_message(str(carol), body)

    @decorators.require_account(online=True)
    def text_message(self, message=None):
        """Alice has typed a message.  Relay it to Bob."""
        alice = self.message_to_account(message)
        _log.debug('%s typed IM' % alice)
        bob = alice.partner
        if bob is None:
            _log.warning('%s typed IM, but has no chat partner' % alice)
            return

        _log.info("sending %s's IM to %s" % (alice, bob))
        body = 'Partner: ' + message.body
        status = xmpp.send_message(str(bob), body)

        if status == xmpp.NO_ERROR:
            _log.info("sent %s's IM to %s" % (alice, bob))
        else:
            if status == xmpp.INVALID_JID:
                body = "couldn't send %s's IM to %s (invalid JID)"
                _log.critical(body % (alice, bob))
            elif status == xmpp.OTHER_ERROR:
                body = "couldn't send %s's IM to %s (other error)"
                _log.warning(body % (alice, bob))
