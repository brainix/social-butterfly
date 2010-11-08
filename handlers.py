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

from config import DEBUG, TEMPLATES, AGES, SEXES
import base
import models


_log = logging.getLogger(__name__)


class NotFound(base.WebRequestHandler):
    """Request handler to serve a 404: Not Found error page."""

    def get(self, *args, **kwds):
        """Someone has issued a GET request on a nonexistent URL."""
        return self._serve_error(404)

    def post(self, *args, **kwds):
        """Someone has issued a POST request on a nonexistent URL."""
        self.error(404)

    trace = delete = options = head = put = post


class Home(base.WebRequestHandler):
    """Request handler to serve the homepage."""

    def get(self):
        """Serve the homepage."""
        path, debug = os.path.join(TEMPLATES, 'home.html'), DEBUG
        title, ages, sexes = 'chat with strangers', AGES, SEXES
        self.response.out.write(template.render(path, locals(), debug=DEBUG))

    def post(self):
        """ """
        values, kwds = ['handle', 'name', 'age', 'sex', 'location'], {}
        for value in values:
            kwds[value] = self.request.get(value)
        kwds['handle'], kwds['online'] = db.IM('xmpp', kwds['handle']), False

        key_name = models.Account.key_name(kwds['handle'].address)
        account = models.Account.get_by_key_name(key_name)
        if account is None:
            account = models.Account(**kwds)
        else:
            account.__dict__.update(**kwds)
        account.put()

        xmpp.send_invite(account.handle.address)


class Chat(base.ChatRequestHandler):
    """Request handler to respond to XMPP messages."""

    def start_command(self, message=None):
        """ """
        pass

    def next_command(self, message=None):
        """ """
        pass

    def stop_command(self, message=None):
        """ """
        pass

    def text_message(self, message=None):
        """ """
        pass
