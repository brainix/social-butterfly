#-----------------------------------------------------------------------------#
#   handlers.py                                                               #
#                                                                             #
#   Copyright (c) 2010-2012, Code A La Mode, original authors.                #
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


import datetime
import logging

from google.appengine.api import memcache
from google.appengine.ext import db

from config import DEBUG
from config import NUM_ACTIVE_USERS_KEY, NUM_MESSAGES_KEY
from config import HELP_EVENT, START_EVENT, NEXT_EVENT, STOP_EVENT, ME_EVENT, TEXT_MESSAGE_EVENT, AVAILABLE_EVENT, UNAVAILABLE_EVENT
import availability
import base
import channels
import notifications
import shards
import strangers


_log = logging.getLogger(__name__)


class NotFound(base.WebHandler):
    """Request handler to serve a 404: Not Found error page."""

    def get(self, *args, **kwds):
        """Someone has issued a GET request on a nonexistent URL."""
        self.serve_error(404)


class Token(base.WebHandler):
    """Request handler to create a channel and return its token."""

    def get(self):
        """Create a channel and return its token."""
        _log.info('someone has requested token to open channel')
        if DEBUG:
            _log.info('running on SDK; not opening channel (too much CPU)')
            self.serve_error(503)
        else:
            _log.info('running on cloud; creating channel, returning token')
            token = channels.Channel.create()
            self.response.out.write(token)
            _log.info('created channel, returned token')


class CronDispatch(base.WebHandler):
    """Request handler to run cron jobs."""

    @base.WebHandler.require_cron
    def get(self, method_name):
        """ """
        method_name = '_' + method_name.replace('-', '_')
        try:
            method = getattr(self, method_name)
        except AttributeError:
            self.serve_error(404)
        else:
            method()

    def _reset_stats(self):
        """Reset the interesting statistics."""
        _log.info('cron resetting num messages sharding counter')
        shards.Shard.reset(NUM_MESSAGES_KEY)
        _log.info('cron reset num messages sharding counter')

    def _flush_channels(self):
        """Flush stale channels.
        
        Google App Engine implements the real-time web using a technology
        called channels (similar to Comet or WebSockets), for server initiated
        communication to the browser.
        
        The problem is that these channels only have a lifespan of 2 hours
        (after which, they're expired and can no longer transport messages).
        And sometimes, these channels expire uncleanly without sending
        disconnect messages.

        So periodically, cron sends a request to call this method to delete all
        of the expired channels.  Just some housekeeping.
        """
        _log.info('cron flushing stale channels')
        channels.Channel.flush()
        _log.info('cron flushed stale channels')

    def _flush_memcache(self):
        """Flush memcache.

        Social Butterfly uses memcache all over the place in order to improve
        performance.  However, a memcached item can be evicted or become
        inconsistent at any moment.  Therefore, cron periodically flushes all
        memcached items in order to:

            1.  Test our code and ensure that it continues to function properly
                even if nothing is memcached.  (After a flush, our code should
                recompute and re-memcache everything.)

            2.  Resolve inconsistencies between memcached and datastored values
                by forcing recomputation of all memcached items.
        """
        _log.info('cron flushing memcache')
        success = memcache.flush_all()
        if success:
            _log.info('cron flushed memcache')
        else:
            _log.error("cron couldn't flush memcache (RPC or server error)")

    def _send_presence(self):
        """Send our Google Talk presence to all active users.
        
        For some reason, there's a problem in the Google Talk widget in Gmail.
        If Social Butterfly doesn't send you its presence for a while (maybe an
        hour or more), it appears offline in your buddy list.  You can still
        use it like normal - it just appears offline.  So this method is a
        workaround - periodically, send Social Butterfly's presence to all
        active users, so it always appears online.
        """
        _log.info('cron sending presence to all active users')
        self.send_presence_to_all()


class Connected(base.WebHandler):
    """Request handler to deal with channels that have connected."""

    def post(self):
        """A channel has connected and can receive messages."""
        client_id = self.request.get('from')
        _log.info('channel %s has connected' % client_id)


class Disconnected(base.WebHandler):
    """Request handler to deal with channels that have disconnected."""

    def post(self):
        """A channel has disconnected and can no longer receive messages."""
        client_id = self.request.get('from')
        _log.info('channel %s has disconnected' % client_id)
        channels.Channel.destroy(client_id)


class Subscribe(base.WebHandler):
    """Request handler to listen for XMPP subscribe requests.
    
    XXX:  I'm not exactly sure when this request handler is called.  I should
    probably find out at some point.
    """

    def post(self):
        """ """
        handle = self.get_handle()
        if not handle:
            handle = 'an unknown user'
        _log.info("%s wishes to subscribe to our presence" % handle)


class Subscribed(base.WebHandler):
    """Request handler to listen for XMPP subscribed notifications."""

    @base.BaseHandler.run_in_transaction
    def post(self):
        """Alice has subscribed to Social Butterfly.  Send the help text.

        In order to get here, Alice must've browsed to the Social Butterfly
        homepage, entered her email address, and accepted Social Butterfly's
        invitation to chat.  Send Alice a message with the help text, so that
        she can begin chatting with strangers.
        """
        alice = self.get_account(cache=False)
        if alice is None:
            body = 'an unknown user has allowed us to receive his/her presence'
            _log.info(body)
        else:
            _log.info('%s has allowed us to receive his/her presence' % alice)
            now = datetime.datetime.now()
            diff = datetime.timedelta(days=1)
            if alice.subscribed is not None and now - alice.subscribed <= diff:
                _log.info('not sending /help text; already sent in last day')
            else:
                _log.info('sending /help text')
                alice.subscribed = now
                db.put_async(alice)
                notifications.Notifications.help(alice)


class Unsubscribe(base.WebHandler):
    """Request handler to listen for XMPP unsubscribe requests.
    
    XXX:  I'm not exactly sure when this request handler is called.  I should
    probably find out at some point.
    """

    def post(self):
        """ """
        handle = self.get_handle()
        if not handle:
            handle = 'an unknown user'
        _log.info('%s is unsubscribing from our presence' % handle)


class Unsubscribed(base.WebHandler):
    """Request handler to listen for XMPP unsubscribed notifications.
    
    XXX:  I'm not exactly sure when this request handler is called.  I should
    probably find out at some point.
    """

    def post(self):
        """ """
        handle = self.get_handle()
        if not handle:
            handle = 'an unknown user'
        _log.info('%s has denied/cancelled our subscription request' % handle)


class Chat(base.ChatHandler):
    """Request handler to respond to XMPP messages."""

    @base.ChatHandler.require_account
    def help_command(self, message=None):
        """Alice has typed /help.  Send her the help text."""
        alice = self.get_account(message)
        _log.info('%s typed /help' % alice)
        notifications.Notifications.help(alice)
        self.broadcast(stats=False, event=HELP_EVENT)

    @base.ChatHandler.require_account
    def start_command(self, message=None):
        """Alice has typed /start.  Make her available for chat."""
        alice = self.get_account(message)
        _log.info('%s typed /start' % alice)
        if alice.started:
            notifications.Notifications.already_started(alice)
        else:
            alice.started = True
            alice.available = True
            alice.partners = []
            alice, bob, async = strangers.Strangers.start_chat(alice)

            # Notify Alice and Bob.
            notifications.Notifications.started(alice)
            notifications.Notifications.chatting(bob)
            self.update_stat(NUM_ACTIVE_USERS_KEY, 1)
            async.get_result()
            self.broadcast(stats=True, event=START_EVENT)
            self.update_active_users(alice)
            self.send_presence_to_all()

    @base.ChatHandler.require_account
    def next_command(self, message=None):
        """Alice has typed /next.  Pair her with a different partner."""
        alice = self.get_account(message)
        _log.info('%s typed /next' % alice)
        if not alice.started:
            # Alice hasn't yet made herself available for chat.  She must first
            # type /start and start chatting with a partner before she can type
            # /next to chat with a different partner.
            notifications.Notifications.not_started(alice)
        elif alice.partner is None:
            # Alice has made herself available for chat, but she isn't
            # currently chatting with a partner.  She must be chatting with a
            # partner in order to type /next to chat with a different partner.
            notifications.Notifications.not_chatting(alice)
        else:
            alice, bob, async = strangers.Strangers.stop_chat(alice)
            alice, carol, async = strangers.Strangers.start_chat(alice)
            if bob is None:
                bob, dave = None, None
            elif bob == alice:
                # This should never be the case, because this would mean that
                # Alice was previously chatting with herself.
                bob, dave = alice, carol
            elif bob == carol:
                bob, dave = carol, alice
            else:
                async.get_result()
                bob, dave, async = strangers.Strangers.start_chat(bob)

            # Notify Alice, Bob, Carol, and Dave.
            notifications.Notifications.nexted(alice)
            if bob not in (alice,):
                notifications.Notifications.been_nexted(bob)
            if carol not in (alice, bob):
                notifications.Notifications.chatting(carol)
            if dave not in (alice, bob, carol):
                notifications.Notifications.chatting(dave)
            self.broadcast(stats=False, event=NEXT_EVENT)

    @base.ChatHandler.require_account
    def stop_command(self, message=None):
        """Alice has typed /stop.  Make her unavailable for chat."""
        alice = self.get_account(message)
        _log.info('%s typed /stop' % alice)
        if not alice.started:
            notifications.Notifications.already_stopped(alice)
        else:
            alice.started = False
            alice, bob, async1 = strangers.Strangers.stop_chat(alice)
            if bob is None:
                carol = None
            else:
                bob, carol, async2 = strangers.Strangers.start_chat(bob)

            # Notify Alice, Bob, and Carol.
            notifications.Notifications.stopped(alice)
            if bob not in (alice,):
                notifications.Notifications.been_nexted(bob)
            if carol not in (alice, bob):
                notifications.Notifications.chatting(carol)
            self.update_stat(NUM_ACTIVE_USERS_KEY, -1)
            async1.get_result()
            self.broadcast(stats=True, event=STOP_EVENT)
            self.update_active_users(alice)
            self.send_presence_to_all()

    @base.ChatHandler.require_account
    @base.ChatHandler.require_admin
    def who_command(self, message=None):
        """Alice has typed /who.  Tell her who she's chatting with."""
        alice = self.get_account(message)
        _log.info('%s typed /who' % alice)
        notifications.Notifications.who(alice)

    def me_command(self, message=None):
        """Alice has typed /me.  Relay her /me action to her chat partner."""
        self._common_message(message=message, me=True)

    def text_message(self, message=None):
        """Alice has typed a message.  Relay it to her chat partner, Bob."""
        self._common_message(message=message, me=False)

    @base.ChatHandler.require_account
    def _common_message(self, message=None, me=True):
        """Alice has typed a /me command or a message to her partner.

        Relay Alice's /me command or message to her chat partner, Bob.
        """
        alice = self.get_account(message)
        verb = '/me' if me else 'IM'
        _log.info('%s typed %s' % (alice, verb))
        if not alice.started:
            notifications.Notifications.not_started(alice)
        else:
            bob = alice.partner
            if bob is None:
                notifications.Notifications.not_chatting(alice)
            else:
                deliverable = strangers.Strangers.is_deliverable(alice)
                if not deliverable:
                    _log.info("can't send %s's %s to %s" % (alice, verb, bob))
                    notifications.Notifications.undeliverable(alice)
                else:
                    _log.info("sending %s's %s to %s" % (alice, verb, bob))
                    method_name = 'me' if me else 'message'
                    method = getattr(notifications.Notifications, method_name)
                    method(bob, message.body)
                    shards.Shard.increment(NUM_MESSAGES_KEY, defer=True)
                    event = ME_EVENT if me else TEXT_MESSAGE_EVENT
                    self.broadcast(stats=True, event=event)
                    _log.info("sent %s's %s to %s" % (alice, verb, bob))


class Error(base.WebHandler):
    """

    XXX:  I'm not exactly sure when this request handler is called.  I should
    probably find out at some point.
    """

    def post(self):
        """ """
        handle = self.get_handle()
        if not handle:
            handle = 'an unknown user'
        _log.info('%s errored' % handle)


class Available(availability.AvailabilityHandler):
    """Request handler to listen for when users become available for chat."""

    @base.WebHandler.send_presence
    def post(self):
        """Alice has become available for chat.

        Mark her available, and if possible, pair her with a chat partner, Bob.
        """
        alice, made_available = self.make_available(True)
        if made_available:
            alice.partners = []
            alice, bob, async = strangers.Strangers.start_chat(alice)
            if bob is None:
                _log.info('%s became available; looking for partner' % alice)
            else:
                body = '%s became available; found partner %s' % (alice, bob)
                _log.info(body)
                notifications.Notifications.chatting(alice)
                notifications.Notifications.chatting(bob)
            self.update_stat(NUM_ACTIVE_USERS_KEY, 1)
            self.broadcast(stats=True, event=AVAILABLE_EVENT)
            self.update_active_users(alice)
            self.send_presence_to_all()


class Unavailable(availability.AvailabilityHandler):
    """Request handler to listen for when users become unavailable for chat."""

    def post(self):
        """Alice has become unavailable for chat.

        Mark her unavailable.  If she had a chat partner, Bob, pair him with a
        new partner, Carol.
        """
        alice, made_unavailable = self.make_available(False)
        if made_unavailable:
            alice, bob, async = strangers.Strangers.stop_chat(alice)
            if bob is None:
                _log.info('%s became unavailable; had no partner' % alice)
            else:
                body = '%s became unavailable; had partner %s' % (alice, bob)
                _log.info(body)
                bob, carol, async = strangers.Strangers.start_chat(bob)
                if carol is None:
                    _log.info('looking for new partner for %s' % bob)
                else:
                    _log.info('found new partner for %s: %s' % (bob, carol))
                notifications.Notifications.been_nexted(bob)
                notifications.Notifications.chatting(carol)
            self.update_stat(NUM_ACTIVE_USERS_KEY, -1)
            self.broadcast(stats=True, event=UNAVAILABLE_EVENT)
            self.update_active_users(alice)
            self.send_presence_to_all()


class Probe(base.WebHandler):
    """Request handler to listen for when users probe for chat status."""

    @base.WebHandler.send_presence
    def post(self):
        """A user is probing for our chat status.  Send it to them.
        
        We send our chat status in the @base.WebHandler.send_presence
        decorator, so there's nothing else for us to do here expect log the
        request.
        """
        handle = self.get_handle()
        if handle is None:
            handle = 'an unknown user'
        _log.info('%s is probing for our current presence' % handle)


class Mail(base.MailHandler):
    """Request handler to receive incoming emails."""

    def receive(self, email_message):
        """Someone has sent us an email message."""
        _log.info('%s has sent us an email message' % email_message.sender)
