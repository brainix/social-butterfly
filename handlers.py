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
"""Request handlers."""


import logging

from google.appengine.api import xmpp

import base


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
