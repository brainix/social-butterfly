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
        if alice.online:
            if alice.partner is None:
                message.reply('Looking for a partner...')
            else:
                message.reply("You're already chatting with a partner.")
        else:
            alice.online = True
            alice, bob = self._start_chat(alice)
            if bob is None:
                xmpp.send_message(alice.handle.address,
                                  'Looking for a partner...')
            else:
                xmpp.send_message([alice.handle.address, bob.handle.address],
                                  "You're now chatting with a partner.")

    def next_command(self, message=None):
        """Alice has typed /next."""
        alice = self._message_to_account(message)
        if not alice.online:
            pass
        else:
            alice, bob = self._stop_chat(alice)
            alice, carol = self._start_chat(alice)
            if bob is not None:
                bob, dave = self._start_chat(bob)
            else:
                dave = None

            # Notify Alice.
            body = "You've disconnected from your partner.\n"
            if carol is None:
                body += 'Looking for a new partner...'
            else:
                body += "You're now chatting with a new partner."
            message.reply(body)

            # Notify Bob.
            if bob is not None:
                body = 'Your partner has disconnected.\n'
                if dave is None:
                    body += 'Looking for a new partner...'
                else:
                    body += "You're now chatting with a new partner."
                xmpp.send_message(bob.handle.address, body)

            # Notify Carol and Dave.
            accounts = (carol, dave)
            accounts = [account for account in accounts if account is not None]
            jids = [account.handle.address for account in accounts]
            xmpp.send_message(jids, "You're now chatting with a partner.")

    def stop_command(self, message=None):
        """Alice has typed /stop."""
        alice = self._message_to_account(message)
        if not alice.online:
            pass
        else:
            alice.online = False
            alice, bob = self._stop_chat(alice)
            if bob is not None:
                bob, carol = self._start_chat(bob)
            else:
                carol = None

    def text_message(self, message=None):
        """Alice has typed a message.  Relay it to Bob."""
        alice = self._message_to_account(message)
        if not alice.online:
            pass
        else:
            pass
