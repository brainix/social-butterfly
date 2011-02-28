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
import notifications


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
        handle = self._sanitize_handle(handle)
        if not self._validate_handle(handle):
            self.serve_error(400)
        else:
            account = self._create_account(handle)
            xmpp.send_invite(str(account))
            _log.info('%s signed up' % handle)

    def _sanitize_handle(self, handle):
        """ """
        handle = handle.strip()
        handle = handle.lower()

        valid_gmail_domains = ['@' + domain for domain in VALID_GMAIL_DOMAINS]
        valid_gmail_domains = tuple(valid_gmail_domains)
        if not handle.endswith(valid_gmail_domains):
            handle += valid_gmail_domains[0]

        return handle

    def _validate_handle(self, handle):
        """ """
        body = "%s couldn't sign up: " % handle

        try:
            local, domain = handle.split('@')
        except ValueError:
            body += "handle doesn't have exactly one at sign"
            _log.warning(body)
            return False

        if not MIN_GMAIL_ADDR_LEN <= len(local) <= MAX_GMAIL_ADDR_LEN:
            body += "handle's local part doesn't meet length requirements"
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

    def _create_account(self, handle):
        """ """
        handle = db.IM('xmpp', handle)
        key_name = models.Account.key_name(handle.address)
        account = models.Account.get_by_key_name(key_name)
        if account is not None:
            _log.warning('%s account not created: already exists' % handle)
        else:
            account = models.Account(key_name=key_name, handle=handle,
                                     started=False, available=False)
            account.put()
            _log.info('%s account created' % handle)
        return account


class Subscribed(base.WebRequestHandler, notifications.Notifications):
    """ """

    def post(self):
        """ """
        handle = self.request.get('from')
        key_name = models.Account.key_name(handle)
        alice = models.Account.get_by_key_name(key_name)
        _log.debug('%s subscribed' % alice)
        self.send_help(alice)


class Chat(base.ChatRequestHandler, notifications.Notifications):
    """Request handler to respond to XMPP messages."""

    @decorators.require_account
    def help_command(self, message=None):
        """Alice has typed /help."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /help' % alice)
        self.send_help(alice)

    @decorators.require_account
    def start_command(self, message=None):
        """Alice has typed /start."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /start' % alice)
        if alice.started:
            self.notify_already_started(alice)
        else:
            alice.started = True
            alice, bob = self.start_chat(alice, None)

            # Notify Alice and Bob.
            self.notify_started(alice)
            self.notify_chatting(bob)

    @decorators.require_account
    def next_command(self, message=None):
        """Alice has typed /next."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /next' % alice)
        if not alice.started:
            # Alice hasn't yet made herself available for chat.  She must first
            # type /start and start chatting with a partner before she can type
            # /next to chat with a different partner.
            self.notify_not_started(alice)
        elif alice.partner is None:
            # Alice has made herself available for chat, but she isn't
            # currently chatting with a partner.  She must be chatting with a
            # partner in order to type /next to chat with a different partner.
            self.notify_not_chatting(alice)
        else:
            alice, bob = self.stop_chat(alice)
            alice, carol = self.start_chat(alice, bob)
            if bob is None:
                bob, dave = None, None
            elif bob == alice:
                # This should never be the case, because this would mean that
                # Alice was previously chatting with herself.
                bob, dave = alice, carol
            elif bob == carol:
                bob, dave = carol, alice
            else:
                bob, dave = self.start_chat(bob, alice)

            # Notify Alice, Bob, Carol, and Dave.
            self.notify_nexted(alice)
            if bob not in (alice,):
                self.notify_been_nexted(bob)
            if carol not in (alice, bob):
                self.notify_chatting(carol)
            if dave not in (alice, bob, carol):
                self.notify_chatting(dave)

    @decorators.require_account
    def stop_command(self, message=None):
        """Alice has typed /stop."""
        alice = self.message_to_account(message)
        _log.debug('%s typed /stop' % alice)
        if not alice.started:
            self.notify_already_stopped(alice)
        else:
            alice.started = False
            alice, bob = self.stop_chat(alice)
            if bob is None:
                carol = None
            else:
                bob, carol = self.start_chat(bob, alice)

            # Notify Alice, Bob, and Carol.
            self.notify_stopped(alice)
            if bob not in (alice,):
                self.notify_been_nexted(bob)
            if carol not in (alice, bob):
                self.notify_chatting(carol)

    @decorators.require_account
    def text_message(self, message=None):
        """Alice has typed a message.  Relay it to Bob."""
        alice = self.message_to_account(message)
        _log.debug('%s typed IM' % alice)
        if not alice.started:
            self.notify_not_started(alice)
        elif alice.partner is None:
            self.notify_not_chatting(alice)
        else:
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
                self.notify_undeliverable(alice)

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
            _log.error(body % (alice, alice, bob, bob, bob.partner))
            deliverable = False
        else:
            # Nothing else can go wrong.  Alice's message must be deliverable
            # to Bob.
            _log.debug('%s typed IM, OK to deliver to %s' % (alice, bob))
            deliverable = True
        return deliverable


class Available(base.WebRequestHandler, notifications.Notifications):
    """ """

    def post(self):
        """ """
        alice = self.request_to_account()
        _log.debug('%s became available' % alice)

        if alice.available:
            body = '%s became available, but was already marked available'
            _log.error(body % alice)
        else:
            alice.available = True
            db.put(alice)

            if not alice.started:
                _log.info("%s became available, but hasn't /started" % alice)
            elif alice.partner is not None:
                body = '%s became available, but already had partner %s'
                _log.error(body % (alice, alice.partner))
            else:
                alice, bob = self.start_chat(alice, None)
                if bob is None:
                    body = '%s became available; looking for partner'
                    _log.info(body % alice)
                else:
                    body = '%s became available; found partner %s'
                    _log.info(body % (alice, bob))
                    self.notify_chatting(alice)
                    self.notify_chatting(bob)

        self._send_presence(alice)

    def _send_presence(self, alice):
        """ """
        num = self.num_active_users()
        noun = 'strangers' if num != 1 else 'stranger'
        status = '%s %s available for chat.' % (num, noun)
        xmpp.send_presence(str(alice), status=status)


class Unavailable(base.WebRequestHandler, notifications.Notifications):
    """ """

    def post(self):
        """ """
        alice = self.request_to_account()
        _log.debug('%s became unavailable' % alice)

        if not alice.available:
            body = '%s became unavailable, but was already marked unavailable'
            _log.error(body % alice)
        else:
            alice.available = False
            db.put(alice)

            if not alice.started:
                _log.info("%s became unavailable, but hasn't /started" % alice)
            elif alice.partner is None:
                _log.info('%s became unavailable, had no partner' % alice)
            else:
                alice, bob = self.stop_chat(alice)
                body = '%s became unavailable, had partner %s' % (alice, bob)
                _log.info(body)
                bob, carol = self.start_chat(bob, alice)
                if carol is None:
                    _log.info('looking for new partner for %s' % bob)
                else:
                    _log.info('found new partner for %s: %s' % (bob, carol))
                self.notify_been_nexted(bob)
                self.notify_chatting(carol)
