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
            account = models.Account(key_name=key_name, handle=handle, online=False)
            account.put()
        xmpp.send_invite(handle.address)


class Chat(base.ChatRequestHandler):
    """Request handler to respond to XMPP messages."""

    @decorators.require_account()
    def help_command(self, message=None):
        """Alice has typed /help."""
        body = 'Type /start to start chatting.\n\n'
        body += 'Type /next to chat with someone else.\n\n'
        body += 'Type /stop to stop chatting.'
        message.reply(body)

    @decorators.require_account(online=False)
    def start_command(self, message=None):
        """Alice has typed /start."""
        alice = self.message_to_account(message)
        alice.online = True
        alice, bob = self.start_chat(alice)
        self.chat_status((alice, bob))

    @decorators.require_account(online=True)
    def next_command(self, message=None):
        """Alice has typed /next."""
        alice = self.message_to_account(message)
        alice, bob = self.stop_chat(alice)
        alice, carol = self.start_chat(alice)
        bob, dave = self.start_chat(bob) if bob is not None else (None, None)
        self.chat_status((alice, carol, bob, dave))

    @decorators.require_account(online=True)
    def stop_command(self, message=None):
        """Alice has typed /stop."""
        alice = self.message_to_account(message)
        alice.online = False
        alice, bob = self.stop_chat(alice)
        bob, carol = self.start_chat(bob) if bob is not None else (None, None)
        self.chat_status((alice, bob, carol))

    @decorators.require_account(online=True)
    def text_message(self, message=None):
        """Alice has typed a message.  Relay it to Bob."""
        alice = self.message_to_account(message)
        bob = alice.partner
        if bob is None:
            return

        _log.debug('%s -> %s : %s' % (alice.handle.address, bob.handle.address,
                                      message.body))
        body = 'Partner: ' + message.body
        xmpp.send_message(bob.handle.address, body)
