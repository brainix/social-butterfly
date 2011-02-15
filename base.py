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


import logging
import os
import traceback

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import xmpp_handlers
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

from config import DEBUG, HTTP_CODE_TO_TITLE, TEMPLATES
import models


_log = logging.getLogger(__name__)


class _BaseRequestHandler(object):
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

    def _only_one(self):
        """ """
        carols = models.Account.all()
        carols = carols.filter('started =', True)
        carols = carols.filter('available =', True)
        only_one = carols.count(2) == 1
        return only_one

    def get_users(self, started=True, available=True, chatting=False):
        """ """
        assert started in (None, False, True)
        assert available in (None, False, True)
        assert chatting in (None, False, True)

        carols = models.Account.all()
        if started is not None:
            carols = carols.filter('started =', started)
        if available is not None:
            carols = carols.filter('available =', available)
        if chatting == False:
            carols = carols.filter('partner =', None)
        elif chatting == True:
            carols = carols.filter('partner !=', None)
            carols.order('partner')
        carols = carols.order('datetime')

        return carols

    def message_to_account(self, message):
        """From an XMPP message, find the user account that sent it."""
        key_name = models.Account.key_name(message.sender)
        alice = models.Account.get_by_key_name(key_name)
        return alice

    def request_to_account(self):
        """ """
        handle = self.request.get('from')
        key_name = models.Account.key_name(handle)
        alice = models.Account.get_by_key_name(key_name)
        return alice

    def _find_partner(self, alice, bob):
        """Alice is looking to chat.  Find her a partner."""
        carols = self.get_users(started=True, available=True, chatting=False)
        only_one = self._only_one()
        for carol in carols:
            if carol != alice:
                if carol != bob or only_one:
                    return carol

    def _link_partners(self, alice, bob):
        """Alice is looking to chat.  Find her a partner, and link them."""
        carol = self._find_partner(alice, bob)
        alice.partner = carol
        if carol is not None:
            carol.partner = alice
        return alice, carol

    def _unlink_partners(self, alice):
        """Alice is not looking to chat.  Unlink her from her partner."""
        bob = alice.partner
        alice.partner = None
        if bob is not None:
            if bob.partner == alice:
                bob.partner = None
            else:
                bob = None
        return alice, bob

    def _start_or_stop_chat(self, alice, bob=None, start=True):
        """ """
        if start:
            alice, carol = self._link_partners(alice, bob)
        else:
            alice, carol = self._unlink_partners(alice)
        accounts = [account for account in (alice, carol)
                    if account is not None]
        db.put(accounts)
        return alice, carol

    def start_chat(self, alice, bob):
        """ """
        return self._start_or_stop_chat(alice, bob=bob, start=True)

    def stop_chat(self, alice):
        """ """
        return self._start_or_stop_chat(alice, start=False)


class WebRequestHandler(_BaseRequestHandler, webapp.RequestHandler):
    """Abstract base web request handler class."""
    pass


class ChatRequestHandler(_BaseRequestHandler, xmpp_handlers.CommandHandler):
    """Abstract base chat request handler class."""
    pass
