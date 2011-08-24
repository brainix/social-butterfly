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

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import xmpp_handlers
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

from config import ADMINS, DEBUG, HTTP_CODE_TO_TITLE, TEMPLATES
from config import NUM_MESSAGES_KEY
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
        """Transactionally execute a method."""
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
                if results is not None:
                    _log.info('retrieved cached results for %s' % key)
                else:
                    _log.info("couldn't retrieve cached results for %s" % key)
                    _log.info('caching results for %s' % key)
                    results = method(self, *args, **kwds)
                    try:
                        success = memcache.set(key, results, time=cache_secs)
                    except MemoryError:
                        success = False
                    if success:
                        _log.info('cached results for %s' % key)
                    else:
                        _log.error("couldn't cache results for %s" % key)
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
            # 503 error.  For more info, see:
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

    def get_handle(self):
        """Pure virtual method."""
        raise NotImplementedError

    def get_account(self):
        """Pure virtual method."""
        raise NotImplementedError


class WebHandler(BaseHandler, notifications.NotificationMixin,
                 strangers.StrangerMixin, webapp.RequestHandler):
    """Abstract base web request handler class."""

    def _serve_error(self, error_code):
        """ """
        path = os.path.join(TEMPLATES, 'error.html')
        debug = DEBUG
        title = HTTP_CODE_TO_TITLE[error_code].lower()
        error_url = self.request.url.split('//', 1)[-1]
        html = template.render(path, locals(), debug=DEBUG)
        self.response.out.write(html)

    def get_handle(self):
        """ """
        handle = self.request.get('from', '')
        handle = handle.split('/', 1)[0].lower()
        return handle

    def get_account(self):
        """ """
        try:
            alice = self.request.alice
        except AttributeError:
            handle = self.request.get('from')
            key_name = models.Account.key_name(handle)
            alice = models.Account.get_by_key_name(key_name)
            self.request.alice = alice
        return alice

    def get_stats(self):
        """ """
        stats = {
            'num_users': self.num_users(),
            'num_active_users': self.num_active_users(),
            'num_messages': shards.Shard.get_count(NUM_MESSAGES_KEY),
        }
        if stats['num_messages'] is None:
            stats['num_messages'] = 0
        return stats

    @staticmethod
    def send_presence(method):
        """ """
        @functools.wraps(method)
        def wrap(self, *args, **kwds):
            return_value = method(self, *args, **kwds)
            alice = self.get_account()
            stats = self.get_stats()
            self.send_status(alice, stats)
            return return_value
        return wrap

    @staticmethod
    def require_cron(method):
        """ """
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


class ChatHandler(BaseHandler, notifications.NotificationMixin,
                  strangers.StrangerMixin, xmpp_handlers.CommandHandler):
    """Abstract base chat request handler class."""

    def _serve_error(self, error_code):
        """ """
        pass

    def get_handle(self, message):
        """ """
        handle = message.sender
        handle = handle.split('/', 1)[0].lower()
        return handle

    def get_account(self, message):
        """From an XMPP message, find the user account that sent it."""
        try:
            alice = self.request.alice
        except AttributeError:
            key_name = models.Account.key_name(message.sender)
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
        def wrap(self, message=None):
            _log.debug('decorated %s requires registered account' % method)
            alice = self.get_account(message)
            if alice is None:
                body = "decorator requirements failed; %s hasn't registered"
                _log.warning(body % message.sender)
                self.notify_requires_account(message.sender)
            else:
                _log.debug('decorator requirements passed; calling method')
                return method(self, message=message)
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
            alice = self.get_account(message)
            if str(alice) not in ADMINS:
                body = "decorator requirements failed; %s isn't an admin"
                _log.warning(body % message.sender)
                self.notify_unknown_command(message.sender)
            else:
                _log.debug('decorator requirements passed; calling method')
                return method(self, message=message)
        return wrap
