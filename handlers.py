#-----------------------------------------------------------------------------#
#   handlers.py                                                               #
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
"""Google App Engine request handlers (concrete implementation classes)."""


import logging
import os

from google.appengine.api import xmpp
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from config import DEBUG, TEMPLATES, MIN_GMAIL_ADDR_LEN, MAX_GMAIL_ADDR_LEN
from config import VALID_GMAIL_CHARS, VALID_GMAIL_DOMAINS
import base
import decorators
import models


_log = logging.getLogger(__name__)


class NotFound(base.WebRequestHandler):
    """Request handler to serve a 404: Not Found error page."""

    def get(self, *args, **kwds):
        """Someone has issued a GET request on a nonexistent URL."""
        return self.serve_error(404)


class Home(base.WebRequestHandler):
    """Request handler to serve the homepage."""

    def get(self):
        """Serve the homepage."""
        path = os.path.join(TEMPLATES, 'home.html')
        debug = DEBUG
        title = 'chat with strangers'
        html = template.render(path, locals(), debug=debug)
        self.response.out.write(html)

    def post(self):
        """A user has signed up.  Create an account, and send a chat invite."""
        handle = self.request.get('handle')
        _log.info('%s signing up' % handle)
        handle = self._sanitize(handle)
        if not self._validate(handle):
            self.serve_error(400)
        else:
            self._create_and_invite(handle)
            _log.info('%s signed up' % handle)

    def _sanitize(self, handle):
        """ """
        handle = handle.strip()
        handle = handle.lower()
        valid_gmail_domains = ['@' + domain for domain in VALID_GMAIL_DOMAINS]
        valid_gmail_domains = tuple(valid_gmail_domains)
        if not handle.endswith(valid_gmail_domains):
            handle += valid_gmail_domains[0]
        local, domain = handle.rsplit('@', 1)
        local = local.replace('.', '')
        handle = local + '@' + domain
        return handle

    def _validate(self, handle):
        """ """
        body = "%s couldn't sign up: " % handle

        try:
            local, domain = handle.split('@')
        except ValueError:
            body += "handle doesn't have exactly one at sign"
            _log.warning(body)
            return False

        if not MIN_GMAIL_ADDR_LEN <= len(local) <= MAX_GMAIL_ADDR_LEN:
            body += "handle's local part doesn't meet length reqs"
            _log.warning(body)
            return False

        for c in local:
            if not c.isalnum() and c not in VALID_GMAIL_CHARS:
                body += "handle's local part has invalid char %s" % c
                _log.warning(body)
                return False

        if domain not in VALID_GMAIL_DOMAINS:
            body += "handle ends with invalid domain %s" % domain
            _log.warning(body)
            return False

        return True

    def _create_and_invite(self, handle):
        """ """
        handle = db.IM('xmpp', handle)
        key_name = models.Account.key_name(handle.address)
        account = models.Account.get_by_key_name(key_name)
        if account is not None:
            _log.info('%s account not created: already exists' % handle)
        else:
            account = models.Account(key_name=key_name, handle=handle,
                                     online=False)
            account.put()
            _log.info('%s account created' % handle)
        xmpp.send_invite(str(account))
        _log.info('%s invited' % handle)


class Chat(base.ChatRequestHandler):
    """Request handler to respond to XMPP messages."""

    @decorators.require_account()
    def help_command(self, message=None):
        """Alice has typed /help."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /help' % alice)
        body = 'Type /start to make yourself available for chat.\n\n'
        body += 'Type /next to chat with someone else.\n\n'
        body += 'Type /stop to make yourself unavailable for chat.'
        message.reply(body)

    @decorators.require_account(online=False)
    def start_command(self, message=None):
        """Alice has typed /start."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /start' % alice)
        alice.online = True
        alice, bob = self.start_chat(alice, None)

        # Notify Alice and Bob.
        self._notify_started(alice)
        if bob is not None:
            self._notify_chatting(bob)

    @decorators.require_account(online=True)
    def next_command(self, message=None):
        """Alice has typed /next."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /next' % alice)
        alice, bob = self.stop_chat(alice)
        alice, carol = self.start_chat(alice, bob)
        if bob is None:
            bob, dave = None, None
        elif bob == alice:
            # This should never be the case, because this would mean that Alice
            # was previously chatting with herself.
            bob, dave = alice, carol
        elif bob == carol:
            bob, dave = carol, alice
        else:
            bob, dave = self.start_chat(bob, alice)

        # Notify Alice, Bob, Carol, and Dave.
        self._notify_nexted(alice)
        if bob is not None and bob not in (alice,):
            self._notify_been_nexted(bob)
        if carol is not None and carol not in (alice, bob):
            self._notify_chatting(carol)
        if dave is not None and dave not in (alice, bob, carol):
            self._notify_chatting(dave)

    @decorators.require_account(online=True)
    def stop_command(self, message=None):
        """Alice has typed /stop."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /stop' % alice)
        alice.online = False
        alice, bob = self.stop_chat(alice)
        if bob is None:
            carol = None
        else:
            bob, carol = self.start_chat(bob, alice)

        # Notify Alice, Bob, and Carol.
        self._notify_stopped(alice)
        if bob is not None and bob not in (alice,):
            self._notify_been_nexted(bob)
        if carol is not None and carol not in (alice, bob):
            self._notify_chatting(carol)

    @decorators.require_account(online=True)
    def text_message(self, message=None):
        """Alice has typed a message.  Relay it to Bob."""
        alice = self.message_to_account(message)
        _log.debug('%s typed IM' % alice)
        bob = alice.partner
        deliverable = self._is_deliverable(alice)

        if deliverable:
            _log.info("sending %s's IM to %s" % (alice, bob))
            body = 'Partner: ' + message.body
            status = xmpp.send_message(str(bob), body)

            assert status in (xmpp.NO_ERROR, xmpp.INVALID_JID,
                              xmpp.OTHER_ERROR)

            if status == xmpp.NO_ERROR:
                _log.info("sent %s's IM to %s" % (alice, bob))
            else:
                if status == xmpp.INVALID_JID:
                    body = "couldn't send %s's IM to %s (invalid JID)"
                    _log.critical(body % (alice, bob))
                elif status == xmpp.OTHER_ERROR:
                    body = "couldn't send %s's IM to %s (other error)"
                    _log.warning(body % (alice, bob))
                deliverable = False

        if not deliverable:
            self._notify_undeliverable(alice)

    def _is_deliverable(self, alice):
        """Alice has typed an IM.  Determine if it can be delivered to Bob."""
        bob = alice.partner
        if bob is None:
            # Oops.  Alice doesn't have a chat partner.
            _log.warning('%s typed IM, but has no chat partner' % alice)
            deliverable = False
        elif bob.partner != alice:
            # Oops.  Alice thinks that her chat partner is Bob, but Bob doesn't
            # think that his chat partner is Alice.  This can happen because we
            # don't link/unlink chat partners transactionally, so we have to
            # check for this case every time anyone types a message.
            body = "%s typed IM, but %s's partner is %s and %s's partner is %s"
            body %= (alice, alice, bob, bob, bob.partner)
            _log.warning(body)
            deliverable = False
        else:
            # Nothing else can go wrong.  Alice's message must be deliverable
            # to Bob.
            _log.debug('%s typed IM, OK to deliver to %s' % (alice, bob))
            deliverable = True
        return deliverable

    def _notify_started(self, alice):
        """Notify Alice that she's made herself available for chat."""
        body = "You've made yourself available for chat.\n\n"
        if alice.partner is None:
            body += 'Looking for a chat partner...'
        else:
            body += 'Now chatting with a partner.  Say hello!'
        status = xmpp.send_message(str(alice), body)

    def _notify_chatting(self, alice):
        """Notify Alice that she's now chatting with a partner."""
        body = 'Now chatting with a partner.  Say hello!'
        status = xmpp.send_message(str(alice), body)

    def _notify_nexted(self, alice):
        """Notify Alice that she's /nexted her partner."""
        body = "You've disconnected from your current chat partner.\n\n"
        if alice.partner is None:
            body += 'Looking for a new chat partner...'
        else:
            body += 'Now chatting with a new partner.  Say hello!'
        status = xmpp.send_message(str(alice), body)

    def _notify_been_nexted(self, alice):
        """Notify Alice that her partner has /nexted her."""
        body = 'Your current chat partner has disconnected.\n\n'
        if alice.partner is None:
            body += 'Looking for a new chat partner...'
        else:
            body += 'Now chatting with a new partner.  Say hello!'
        status = xmpp.send_message(str(alice), body)

    def _notify_stopped(self, alice):
        """Notify Alice that she's made herself unavailable for chat."""
        body = "You've made yourself unavailable for chat."
        status = xmpp.send_message(str(alice), body)

    def _notify_undeliverable(self, alice):
        """Notify Alice that we couldn't deliver her message to her partner."""
        body = "Couldn't deliver your message to your chat partner.\n\n"
        body += 'Please try to send your message again, '
        body += 'or type /next to chat with someone else.'
        status = xmpp.send_message(str(alice), body)
