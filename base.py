#------------------------------------------------------------------------------#
#   base.py                                                                    #
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
"""Google App Engine request handlers (abstract base classes)."""


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


_log = logging.getLogger(__name__)


class _CommonRequestHandler(object):
    """Methods common to all request handlers."""

    def handle_exception(self, exception, debug_mode):
        """Houston, we have a problem...  Handle an uncaught exception.

        This method overrides the webapp.RequestHandler class's
        handle_exception method.  This method gets called whenever there's an
        uncaught exception anywhere in the social-butterfly code.
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
        self._serve_error(error_code)

    def _serve_error(self, error_code):
        """Houston, we have a problem...  Serve an error page."""
        if not error_code in HTTP_CODE_TO_TITLE:
            error_code = 500
        path, debug = os.path.join(TEMPLATES, 'error.html'), DEBUG
        title = HTTP_CODE_TO_TITLE[error_code].lower()
        error_url = self.request.url.split('//', 1)[-1]
        self.error(error_code)
        self.response.out.write(template.render(path, locals(), debug=DEBUG))


class _BaseRequestHandler(_CommonRequestHandler):
    """Abstract base request handler class."""

    def get(*args, **kwds):
        """Abstract method to handle requests."""
        raise NotImplementedError

    trace = delete = options = head = put = post = get


class WebRequestHandler(_BaseRequestHandler, webapp.RequestHandler):
    """Abstract base web request handler class."""
    pass


class ChatRequestHandler(_BaseRequestHandler, xmpp_handlers.CommandHandler):
    """Abstract base chat request handler class."""

    def message_to_account(self, message):
        """ """
        key_name = models.Account.key_name(message.sender)
        alice = models.Account.get_by_key_name(key_name)
        return alice

    def _find_partner(self, alice):
        """ """
        bobs = models.Account.all()
        bobs = bobs.filter('online =', True)
        bobs = bobs.filter('partner =', None)
        bobs = bobs.order('datetime')
        for bob in bobs:
            if bob != alice and xmpp.get_presence(bob.address):
                return bob
        return None

    def _link(self, alice):
        """ """
        bob = self._find_partner(alice)
        alice.partner = bob
        if bob is not None:
            bob.partner = alice
        return alice, bob

    def _unlink(self, alice):
        """ """
        bob = alice.partner
        alice.partner = None
        if bob is not None:
            if bob.partner == alice:
                bob.partner = None
            else:
                bob = None
        return alice, bob

    def _start_or_stop(self, alice, start=True):
        """ """
        alice, bob = self._link(alice) if start else self._unlink(alice)
        accounts = [account for account in (alice, bob) if account is not None]
        db.put(accounts)
        return alice, bob

    def start(self, alice):
        """ """
        return self._start_or_stop(alice, start=True)

    def stop(self, alice):
        """ """
        return self._start_or_stop(alice, start=False)

    def notify(self, accounts):
        """ """
        accounts = [account for account in accounts if account is not None]
        for account in accounts:
            body = 'Now chatting.' if account.partner else 'No longer chatting.'
            xmpp.send_message(account.handle.address, body)
