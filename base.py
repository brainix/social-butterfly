#-----------------------------------------------------------------------------#
#   base.py                                                                   #
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
"""Google App Engine request handlers (abstract base classes)."""


import functools
import logging
import os
import traceback

from django.utils import simplejson
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import deferred
from google.appengine.ext import webapp
from google.appengine.ext.webapp import mail_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import xmpp_handlers
from google.appengine.runtime import DeadlineExceededError
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

from config import DEBUG, HTTP_CODE_TO_TITLE, TEMPLATES
from config import NUM_USERS_KEY, NUM_ACTIVE_USERS_KEY, NUM_MESSAGES_KEY, ACTIVE_USERS_KEY
from config import ADMIN_EMAILS
import channels
import models
import notifications
import shards
import strangers


_log = logging.getLogger(__name__)


class BaseHandler(object):
    """Abstract base request handler class.
    
    This abstract base request handler class contains methods common to all
    request handler classes.
    """

    @staticmethod
    def run_in_transaction(method):
        """Decorator to transactionally execute a method."""
        @functools.wraps(method)
        def wrap(*args, **kwds):
            method_name = method.func_name
            _log.debug('transactionally executing %s' % method_name)
            return_value = db.run_in_transaction(method, *args, **kwds)
            _log.debug('transactionally executed %s' % method_name)
            return return_value
        return wrap

    @classmethod
    def memoize(cls, cache_secs):
        """Decorate a method with the memcache pattern.

        Technically, this memoize function isn't a decorator.  It's a function
        that returns a decorator.  We have to jump through these hoops because
        we want to pass an argument to the decorator - how long to cache the
        results.  But a decorator can only accept one argument - the method to
        be decorated.  So instead, we use a closure.  For more information on
        closures, see:
            http://en.wikipedia.org/wiki/Closure_(computer_science)

        memoize is convenient to use on an expensive method that doesn't always
        need to return live results.  Conceptually, we check the memcache for
        the results of a method call.  If those results have already been
        computed and cached, then we simply return them.  Otherwise, we call
        the method to compute the results, cache the results (so that future
        calls will hit the cache), then return the results.  For more
        information on memoization, see:
            http://en.wikipedia.org/wiki/Memoization
        """
        def wrap1(method):
            @functools.wraps(method)
            def wrap2(self, *args, **kwds):
                key = cls._compute_memcache_key(self, method, *args, **kwds)
                _log.debug('trying to retrieve cached results for %s' % key)
                results = memcache.get(key)
                if results is None:
                    _log.info("couldn't retrieve cached results for %s" % key)
                    _log.info('caching results for %s' % key)
                    results = method(self, *args, **kwds)
                    try:
                        success = memcache.set(key, results, time=cache_secs)
                    except MemoryError:
                        success = False
                    if not success:
                        _log.error("couldn't cache results for %s" % key)
                    else:
                        _log.info('cached results for %s' % key)
                else:
                    _log.info('retrieved cached results for %s' % key)
                return results
            return wrap2
        return wrap1

    @staticmethod
    def _compute_memcache_key(self, method, *args, **kwds):
        """Convert a method call into a readable str for use as a memcache key.

        Take into account the module, class, and method names, positional
        argument values, and keyword argument names and values in order to
        eliminate the possibility of a false positive memcache hit.
        """

        def stringify(arg):
            """ """
            quote = "'" if isinstance(arg, str) else ''
            s = quote + str(arg) + quote
            return s

        memcache_key = str(type(self)).split("'")[1] + '.' + method.func_name + '('
        memcache_key += ', '.join([stringify(arg) for arg in args])
        if args and kwds:
            memcache_key += ', '
        memcache_key += ', '.join([str(key) + '=' + stringify(kwds[key])
                                   for key in kwds]) + ')'
        return memcache_key

    @staticmethod
    def defer(countdown=None, queue=None):
        """Decorator to defer the execution of a method."""
        def wrap1(method):
            @functools.wraps(method)
            def wrap2(self, *args, **kwds):
                method_name = method.func_name
                _log.debug('deferring execution of %s' % method_name)
                if countdown is not None:
                    kwds['_countdown'] = countdown
                if queue is not None:
                    kwds['_queue'] = queue
                deferred.defer(method, *args, **kwds)
                _log.debug('deferred execution of %s' % method_name)
            return wrap2
        return wrap1

    def handle_exception(self, exception, debug_mode):
        """Houston, we have a problem...  Handle an uncaught exception.

        This method overrides the webapp.RequestHandler class's
        handle_exception method.  This method gets called whenever there's an
        uncaught exception anywhere in the Social Butterfly code.
        """
        # Get and log the traceback.
        error_message = traceback.format_exc()
        _log.critical(error_message)

        # Determine the error code.
        if isinstance(exception, CapabilityDisabledError):
            # The only time this exception is thrown is when the datastore is
            # in read-only mode for maintenance.  Gracefully degrade - throw a
            # 503 error.  For more information, see:
            #   http://code.google.com/appengine/docs/python/howto/maintenance.html
            error_code = 503
        else:
            error_code = 500

        # Serve the error page.
        self.serve_error(error_code)

    def serve_error(self, error_code):
        """Houston, we have a problem...  Serve an error page."""
        if not error_code in HTTP_CODE_TO_TITLE:
            error_code = 500
        self.error(error_code)
        self._serve_error(error_code)

    def _serve_error(self, error_code):
        """Pure virtual method."""
        raise NotImplementedError


class _CommonHandler(BaseHandler, strangers.StrangerMixin):
    """Abstract base request handler class."""

    def _serve_error(self, error_code):
        """Pure virtual method."""
        raise NotImplementedError

    def get_handle(self):
        """Pure virtual method."""
        raise NotImplementedError

    def get_account(self):
        """Pure virtual method."""
        raise NotImplementedError

    def get_stats(self):
        """Return a dict containing all of the statistics that we track.

        We track the total number of users who've signed up for Social
        Butterfly, the number of users currently online and available for chat,
        and the number of instant messages sent today.
        """

        # First, try to get all of the stats from memcache.
        client = memcache.Client()
        stats = [NUM_USERS_KEY, NUM_ACTIVE_USERS_KEY, NUM_MESSAGES_KEY]
        stats = client.get_multi(stats)

        # Next, if any of the stats wasn't memcached, fall back to computing
        # that stat.
        missed = {}
        if not stats.has_key(NUM_USERS_KEY):
            missed[NUM_USERS_KEY] = self.num_users()
        if not stats.has_key(NUM_ACTIVE_USERS_KEY):
            missed[NUM_ACTIVE_USERS_KEY] = self.num_active_users()
        if not stats.has_key(NUM_MESSAGES_KEY):
            # Since this stat is actually a sharding counter, our sharding
            # counter implementation should keep this stat memcached.  So don't
            # update memcache (leave that to our sharding counter
            # implementation).  Only update our dict.
            num_messages = shards.Shard.get_count(NUM_MESSAGES_KEY)
            num_messages = 0 if num_messages is None else num_messages
            stats[NUM_MESSAGES_KEY] = num_messages

        # Finally, if we fell back to computing any of the stats, shove that
        # stat back into memcache and into the dict that we're going to return.
        if missed:
            client.add_multi_async(missed)
            stats.update(missed)
        return stats

    def update_stat(self, memcache_key, change):
        """ """
        assert change in (1, -1)
        func_name = 'incr' if change == 1 else 'decr'
        func = getattr(memcache, func_name)
        value = func(memcache_key)
        if value is None:
            if memcache_key == NUM_USERS_KEY:
                value = self.num_users()
            elif memcache_key == NUM_ACTIVE_USERS_KEY:
                value = self.num_active_users()
            if value is not None:
                memcache.add(memcache_key, value)
        return value

    def update_active_users(self, alice):
        """ """
        client = memcache.Client()
        active_users = client.gets(ACTIVE_USERS_KEY)
        if active_users is not None:
            active = alice.started and alice.available
            method_name = 'add' if active else 'discard'
            method = getattr(active_users, method_name)
            method(str(alice))
            client.cas(ACTIVE_USERS_KEY, active_users)

    def broadcast(self, stats=False, event=None):
        """ """
        d = {}
        if stats:
            stats = self.get_stats()
            d.update(stats)
        if event is not None:
            d[event] = 1
        if d:
            json = simplejson.dumps(d)
            channels.Channel.broadcast(json)

    def send_presence_to_all(self):
        """ """
        _log.info('deferring sending presence to all active users')
        cls = self.__class__
        active_users = memcache.get(ACTIVE_USERS_KEY)
        stats = self.get_stats()
        deferred_sending_presence = False

        if active_users is not None:
            if active_users:
                deferred.defer(cls._send_presence_to_set, active_users, stats)
                deferred_sending_presence = True
        else:
            active_users = self.get_users(started=True, available=True)
            if active_users.count(1):
                deferred.defer(cls._send_presence_to_query, active_users,
                               stats)
                deferred_sending_presence = True
            else:
                active_users = set()
                memcache.add(ACTIVE_USERS_KEY, active_users)

        if deferred_sending_presence:
            _log.info('deferred sending presence to all active users')
        else:
            _log.info('not deferring sending presence (no active users)')

    @classmethod
    def _send_presence_to_set(cls, carols, stats):
        """ """
        _log.info('sending presence to all active users')
        num_carols = 0
        sent_to = set()
        try:
            for carol in carols:
                notifications.Notifications.status(carol, stats)
                num_carols += 1
                sent_to.add(carol)
        except DeadlineExceededError:
            _log.info('sent presence to %s users' % num_carols)
            _log.warning('deadline; deferring presence to remaining users')
            send_to = carols - sent_to
            deferred.defer(cls._send_presence_to_set, send_to, stats)
        else:
            _log.info('sent presence to %s users' % num_carols)
            _log.info('sent presence to all active users')

    @classmethod
    def _send_presence_to_query(cls, carols, stats, cursor=None):
        """ """
        _log.info('sending presence to all active users')
        if cursor is not None:
            carols = carols.with_cursor(cursor)
        num_carols = 0

        client = memcache.Client()
        active_users, memcached = client.gets(ACTIVE_USERS_KEY), True
        if active_users is None:
            active_users, memcached = set(), False

        try:
            for carol in carols:
                carol = carol.name()
                carol = models.Account.key_to_handle(carol)
                notifications.Notifications.status(carol, stats)
                # There's a chance that Google App Engine will throw the
                # DeadlineExceededError exception at this point in the flow of
                # execution.  In this case, carol will have already received
                # our chat status, but cursor will not have been updated.  So
                # on the next go-around, carol will receive our chat status
                # again.  I'm just documenting this possibility, but it
                # shouldn't be a big deal.
                cursor = carols.cursor()
                num_carols += 1
                active_users.add(carol)
        except DeadlineExceededError:
            _log.info('sent presence to %s users' % num_carols)
            _log.warning('deadline; deferring presence to remaining users')
            deferred.defer(cls._send_presence_to_query, carols, stats,
                           cursor=cursor)
        else:
            _log.info('sent presence to %s users' % num_carols)
            _log.info('sent presence to all active users')
        finally:
            method_name = 'cas' if memcached else 'add'
            method = getattr(client, method_name)
            method(ACTIVE_USERS_KEY, active_users)


class WebHandler(_CommonHandler, webapp.RequestHandler):
    """Abstract base web request handler class."""

    def _serve_error(self, error_code):
        """ """
        path = os.path.join(TEMPLATES, 'error.html')
        snippet = getattr(self.request, 'snippet', False)
        title = HTTP_CODE_TO_TITLE[error_code].lower()
        description = 'Social Butterfly allows you to anonymously chat with random strangers through Google Talk.'
        error_url = self.request.url.split('//', 1)[-1]
        html = template.render(path, locals(), debug=DEBUG)
        if snippet:
            d = {'title': title, 'description': description, 'snippet': html}
            json = simplejson.dumps(d)
            self.response.out.write(json)
        else:
            self.response.out.write(html)

    def get_handle(self):
        """ """
        handle = self.request.get('from', '')
        handle = handle.split('/', 1)[0].lower()
        return handle

    def get_account(self, cache=True):
        """ """
        alice = self.request.get('alice') if cache else None
        if alice is None:
            handle = self.request.get('from')
            key_name = models.Account.handle_to_key(handle)
            alice = models.Account.get_by_key_name(key_name)
            self.request.alice = alice
        return alice

    @staticmethod
    def send_presence(method):
        """ """
        @functools.wraps(method)
        def wrap(self, *args, **kwds):
            return_value = method(self, *args, **kwds)
            alice = self.get_account()
            stats = self.get_stats()
            notifications.Notifications.status(alice, stats)
            return return_value
        return wrap

    @staticmethod
    def require_cron(method):
        """Ensure that only cron can call a request handler method.
        
        We do this by checking for a special request header, X-AppEngine-Cron,
        that Google App Engine sets on a request if and only if the request was
        initiated by cron.
        """
        @functools.wraps(method)
        def wrap(self, *args, **kwds):
            _log.debug('decorated %s can only be called by cron' % method)
            if self.request.headers.get('X-AppEngine-Cron') != 'true':
                body = 'decorator requirements failed; %s not called by cron'
                _log.warning(body % method)
                self.serve_error(401)
            else:
                _log.debug('decorator requirements passed; calling method')
                return method(self, *args, **kwds)
        return wrap


class ChatHandler(_CommonHandler, xmpp_handlers.CommandHandler):
    """Abstract base chat request handler class."""

    def _serve_error(self, error_code):
        """ """
        pass

    def get_handle(self, message):
        """From an XMPP message, determine the handle that sent it."""
        handle = message.sender
        handle = handle.split('/', 1)[0].lower()
        return handle

    def get_account(self, message):
        """From an XMPP message, find the user account that sent it."""
        try:
            alice = self.request.alice
        except AttributeError:
            key_name = models.Account.handle_to_key(message.sender)
            alice = models.Account.get_by_key_name(key_name)
            self.request.alice = alice
        return alice

    @staticmethod
    def require_account(method):
        """Require that the user has signed up to access the request handler.

        Google App Engine provides similar functionality:
            from google.appengine.ext.webapp.util import login_required

        But Google App Engine's provided decorator is meant for GET webapp
        request handlers that the user interacts with through his/her browser.
        We need to decorate GET XMPP request handlers that the user interacts
        with through Google Talk.
        
        So, on authentication failure, instead of redirecting to a login page,
        we need to reply with an XMPP instant message instructing the user how
        to sign up.
        """
        @functools.wraps(method)
        def wrap(self, message=None, **kwds):
            _log.debug('decorated %s requires registered account' % method)
            alice = self.get_account(message)
            if alice is None:
                body = "decorator requirements failed; %s hasn't registered"
                _log.warning(body % message.sender)
                notifications.Notifications.requires_account(message.sender)
            else:
                _log.debug('decorator requirements passed; calling method')
                return method(self, message=message, **kwds)
        return wrap

    @staticmethod
    def require_admin(method):
        """Require that the user is an admin to access the request handler.

        If the user issuing the command isn't an admin, she shouldn't know that
        the command exists.  So in this case, mimic Google App Engine's
        xmpp_handlers.CommandHandler's "unknown command" behavior.
        """
        @functools.wraps(method)
        def wrap(self, message=None):
            _log.debug('decorated %s requires admin account' % method)
            handle = self.get_handle(message)
            if handle not in ADMIN_EMAILS:
                body = "decorator requirements failed; %s isn't an admin"
                _log.warning(body % handle)
                notifications.Notifications.unknown_command(handle)
            else:
                _log.debug('decorator requirements passed; calling method')
                return method(self, message=message)
        return wrap


class MailHandler(_CommonHandler, mail_handlers.InboundMailHandler):
    """Abstract base inbound email request handler class."""

    def _serve_error(self, error_code):
        """ """
        pass

    def get_handle(self):
        """ """
        raise NotImplementedError

    def get_account(self):
        """ """
        raise NotImplementedError
