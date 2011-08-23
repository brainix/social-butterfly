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

from django.utils import simplejson
from google.appengine.api import memcache
from google.appengine.api import xmpp
from google.appengine.ext.webapp import template

from config import DEBUG, TEMPLATES
from config import NUM_USERS_KEY, NUM_ACTIVE_USERS_KEY, NUM_MESSAGES_KEY
import availability
import base
import models
import shards


_log = logging.getLogger(__name__)


class NotFound(base.WebHandler):
    """Request handler to serve a 404: Not Found error page."""

    def get(self, *args, **kwds):
        """Someone has issued a GET request on a nonexistent URL."""
        return self.serve_error(404)


class Home(base.WebHandler):
    """Request handler to serve the homepage."""

    def get(self):
        """Serve the homepage."""
        path = os.path.join(TEMPLATES, 'home.html')
        debug = DEBUG
        title = 'chat with strangers'
        stats = self.get_stats()
        html = template.render(path, locals(), debug=debug)
        self.response.out.write(html)

    def post(self):
        """A user has signed up.  Create an account, and send a chat invite."""
        handle = self.request.get('handle')
        _log.info('%s signing up' % handle)
        try:
            account, created = models.Account.factory(handle)
        except ValueError:
            _log.warning("%s couldn't sign up" % handle)
            self.serve_error(400)
        else:
            xmpp.send_invite(str(account))
            _log.info('%s signed up' % handle)
            if created:
                memcache.incr(NUM_USERS_KEY)


class GetStats(base.WebHandler):
    """Request handler to update the interesting statistics."""

    def get(self):
        """Return a JSON object containing updated interesting statistics."""
        stats = self.get_stats()
        json = simplejson.dumps(stats)
        self.response.out.write(json)


class ResetStats(base.WebHandler):
    """Request handler to reset the interesting statistics."""

    @base.WebHandler.require_cron
    def get(self):
        """ """
        shards.Shard.reset_count(NUM_MESSAGES_KEY)
        _log.info('cron reset num messages sharding counter')


class Stats(base.WebHandler):
    """Request handler to serve the interesting statistics page."""

    def get(self):
        """Serve the interesting statistics page."""
        path = os.path.join(TEMPLATES, 'stats.html')
        debug = DEBUG
        title = 'interesting statistics'
        stats = self.get_stats()
        html = template.render(path, locals(), debug=debug)
        self.response.out.write(html)


class Album(base.WebHandler):
    """ """

    def get(self):
        """ """
        html = self._render_album()
        self.response.out.write(html)

    @base.BaseHandler.memoize(3600)
    def _render_album(self):
        """ """
        path = os.path.join(TEMPLATES, 'album.html')
        debug = DEBUG
        title = 'who uses social butterfly?'
        users = self.get_users(started=None, available=None, chatting=None, order=False)
        stats = self.get_stats()
        html = template.render(path, locals(), debug=debug)
        return html


class Subscribe(base.WebHandler):
    """ """

    def post(self):
        """ """
        pass


class Subscribed(base.WebHandler):
    """Request handler to listen for XMPP subscription notifications."""

    def post(self):
        """Alice has subscribed to Social Butterfly.  Send the help text.

        In order to get here, Alice must've browsed to the Social Butterfly
        homepage, entered her email address, and accepted Social Butterfly's
        invitation to chat.  Send Alice a message with the help text, so that
        she can begin chatting with strangers.
        """
        alice = self.get_account()
        _log.debug('%s subscribed' % alice)
        self.send_help(alice)


class Unsubscribe(base.WebHandler):
    """ """

    def post(self):
        """ """
        pass


class Unsubscribed(base.WebHandler):
    """ """

    def post(self):
        """ """
        pass


class Chat(base.ChatHandler):
    """Request handler to respond to XMPP messages."""

    @base.ChatHandler.require_account
    def help_command(self, message=None):
        """Alice has typed /help."""
        alice = self.get_account(message)
        _log.debug('%s typed /help' % alice)
        self.send_help(alice)

    @base.ChatHandler.require_account
    def start_command(self, message=None):
        """Alice has typed /start."""
        alice = self.get_account(message)
        _log.debug('%s typed /start' % alice)
        if alice.started:
            self.notify_already_started(alice)
        else:
            alice.started = True
            alice.available = True
            alice, bob = self.start_chat(alice, None)

            # Notify Alice and Bob.
            self.notify_started(alice)
            self.notify_chatting(bob)

    @base.ChatHandler.require_account
    def next_command(self, message=None):
        """Alice has typed /next."""
        alice = self.get_account(message)
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

    @base.ChatHandler.require_account
    def stop_command(self, message=None):
        """Alice has typed /stop."""
        alice = self.get_account(message)
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

    @base.ChatHandler.require_account
    @base.ChatHandler.require_admin
    def who_command(self, message=None):
        """Alice has typed /who."""
        alice = self.get_account(message)
        _log.debug('%s typed /who' % alice)
        self.notify_who(alice)

    @base.ChatHandler.require_account
    def text_message(self, message=None):
        """Alice has typed a message.  Relay it to her chat partner, Bob."""
        alice = self.get_account(message)
        _log.debug('%s typed IM' % alice)
        if not alice.started:
            self.notify_not_started(alice)
        elif alice.partner is None:
            self.notify_not_chatting(alice)
        else:
            bob = alice.partner
            deliverable = self.is_deliverable(alice)
            if deliverable:
                _log.info("sending %s's IM to %s" % (alice, bob))
                self.send_message(bob, message.body)
                shards.Shard.increment_count(NUM_MESSAGES_KEY)
                _log.info("sent %s's IM to %s" % (alice, bob))
            else:
                _log.info("can't send %s's IM to %s" % (alice, bob))
                self.notify_undeliverable(alice)


class Error(base.WebHandler):
    """ """

    def post(self):
        """ """
        pass


class Available(availability.AvailabilityHandler):
    """Request handler to listen for when users become available for chat."""

    @base.WebHandler.send_presence
    def post(self):
        """Alice has become available for chat.
        
        Mark her available, and if possible, pair her with a chat partner, Bob.
        """
        alice, made_available = self.make_available()
        if made_available:
            alice, bob = self.start_chat(alice, None)
            if bob is None:
                _log.info('%s became available; looking for partner' % alice)
            else:
                body = '%s became available; found partner %s' % (alice, bob)
                _log.info(body)
                self.notify_chatting(alice)
                self.notify_chatting(bob)
            memcache.incr(NUM_ACTIVE_USERS_KEY)


class Unavailable(availability.AvailabilityHandler):
    """Request handler to listen for when users become unavailable for chat."""

    def post(self):
        """Alice has become unavailable for chat.
        
        Mark her unavailable.  If she had a chat partner, Bob, pair him with a
        new partner, Carol.
        """
        alice, made_unavailable = self.make_unavailable()
        if made_unavailable:
            alice, bob = self.stop_chat(alice)
            if bob is None:
                _log.info('%s became unavailable; had no partner' % alice)
            else:
                body = '%s became unavailable; had partner %s' % (alice, bob)
                _log.info(body)
                bob, carol = self.start_chat(bob, alice)
                if carol is None:
                    _log.info('looking for new partner for %s' % bob)
                else:
                    _log.info('found new partner for %s: %s' % (bob, carol))
                self.notify_been_nexted(bob)
                self.notify_chatting(carol)
            memcache.decr(NUM_ACTIVE_USERS_KEY)


class Probe(base.WebHandler):
    """Request handler to listen for when users probe for chat status."""

    @base.WebHandler.send_presence
    def post(self):
        """ """
        alice = self.get_account()
        _log.debug('%s probed' % alice)
