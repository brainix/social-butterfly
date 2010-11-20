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
import models


_log = logging.getLogger(__name__)


class NotFound(base.WebRequestHandler):
    """Request handler to serve a 404: Not Found error page."""

    def get(self, *args, **kwds):
        """Someone has issued a GET request on a nonexistent URL."""
        return self._serve_error(404)

    def post(self, *args, **kwds):
        """Someone has issued a POST request on a nonexistent URL."""
        self.error(404)

    trace = delete = options = head = put = post


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
            account = models.Account(handle=handle)
            account.put()
        xmpp.send_invite(handle.address)


class Chat(base.ChatRequestHandler):
    """Request handler to respond to XMPP messages."""

    def help_command(self, message=None):
        """Alice has typed /help."""
        body = 'Type /start to start chatting.\n'
        body += 'Type /next to chat with someone else.\n'
        body += 'Type /stop to stop chatting.'
        message.reply(body)

    def start_command(self, message=None):
        """Alice has typed /start."""
        alice = self._message_to_account(message)
        if alice is None or alice.online:
            return

        alice.online = True
        alice, bob = self._start(alice)

        # Notify Alice and Bob.
        if bob is not None:
            xmpp.send_message([alice.handle.address, bob.handle.address],
                              'Now chatting.')

    def next_command(self, message=None):
        """Alice has typed /next."""
        alice = self._message_to_account(message)
        if alice is None or not alice.online:
            return

        alice, bob = self._stop(alice)
        alice, carol = self._start(alice)
        bob, dave = self._start(bob) if bob is not None else (None, None)

        # Notify Alice and Carol.
        if carol is None:
            message.reply('No longer chatting.')
        else:
            message.reply('Now chatting.')
            xmpp.send_message([alice.handle.address, carol.handle.address],
                              'Now chatting.')

        # Notify Bob and Dave.
        if bob is not None:
            if dave is None:
                xmpp.send_message(bob.handle.address, 'No longer chatting.')
            else:
                xmpp.send_message([bob.handle.address, dave.handle.address],
                                  'Now chatting.')

    def stop_command(self, message=None):
        """Alice has typed /stop."""
        alice = self._message_to_account(message)
        if alice is None or not alice.online:
            return

        alice.online = False
        alice, bob = self._stop(alice)
        bob, carol = self._start(bob) if bob is not None else (None, None)

        # Notify Alice.
        if bob is not None:
            message.reply('No longer chatting.')

        # Notify Bob and Carol.
        if bob is not None:
            if carol is None:
                xmpp.send_message(bob.handle.address, 'No longer chatting.')
            else:
                xmpp.send_message([bob.handle.address, carol.handle.address],
                                  'Now chatting.')

    def text_message(self, message=None):
        """Alice has typed a message.  Relay it to Bob."""
        alice = self._message_to_account(message)
        if alice is None or not alice.online:
            return
        bob = alice.partner
        if bob is None:
            return
        body = 'Partner: ' + message.body
        xmpp.send_message(bob.handle.address, body)
