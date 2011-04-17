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

from google.appengine.api import xmpp
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import xmpp_handlers
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

from config import DEBUG, HTTP_CODE_TO_TITLE, TEMPLATES
import models
import notifications
import strangers


_log = logging.getLogger(__name__)


class _BaseHandler(object):
    """Methods common to all request handlers."""

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
        path = os.path.join(TEMPLATES, 'error.html')
        debug = DEBUG
        title = HTTP_CODE_TO_TITLE[error_code].lower()
        error_url = self.request.url.split('//', 1)[-1]
        self.error(error_code)
        html = template.render(path, locals(), debug=DEBUG)
        self.response.out.write(html)


class WebHandler(_BaseHandler, strangers.StrangerMixin, webapp.RequestHandler):
    """Abstract base web request handler class."""

    def request_to_account(self):
        """ """
        handle = self.request.get('from')
        key_name = models.Account.key_name(handle)
        alice = models.Account.get_by_key_name(key_name)
        return alice

    @staticmethod
    def send_presence(method):
        """ """
        @functools.wraps(method)
        def wrap(self, *args, **kwds):
            return_value = method(self, *args, **kwds)
            alice = self.request_to_account()
            if alice is not None:
                num = self.num_active_users()
                noun = 'strangers' if num != 1 else 'stranger'
                status = '%s %s available for chat.' % (num, noun)
                xmpp.send_presence(str(alice), status=status)
            return return_value
        return wrap

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


class ChatHandler(_BaseHandler, notifications.NotificationMixin,
                  strangers.StrangerMixin, xmpp_handlers.CommandHandler):
    """Abstract base chat request handler class."""

    def message_to_account(self, message):
        """From an XMPP message, find the user account that sent it."""
        key_name = models.Account.key_name(message.sender)
        alice = models.Account.get_by_key_name(key_name)
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
            alice = self.message_to_account(message)
            if alice is None:
                body = "decorator requirements failed; %s hasn't registered"
                _log.warning(body % message.sender)
                self.notify_requires_account(message.sender)
            else:
                _log.debug('decorator requirements passed; calling method')
                return method(self, message=message)
        return wrap
