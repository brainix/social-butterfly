#-----------------------------------------------------------------------------#
#   decorators.py                                                             #
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
"""Decorators to alter the behavior of request handler methods."""


import functools
import logging


_log = logging.getLogger(__name__)


def require_account(method):
    """ """
    @functools.wraps(method)
    def wrap(self, message=None):
        body = 'decorated method %s requires registered account'
        _log.debug(body % method.func_name)
        alice = self.message_to_account(message)
        if alice is None:
            body = "decorator requirements failed; %s hasn't registered"
            _log.warning(body % message.sender)
            body = "To chat with strangers on Social Butterfly, you must sign "
            body += 'up here:\n\nhttp://social-butterfly.appspot.com/'
            message.reply(body)
        else:
            _log.debug('decorator requirements passed; calling method')
            return method(self, message=message)
    return wrap


def require_cron(method):
    """ """
    @functools.wraps(method)
    def wrap(self, *args, **kwds):
        if self.request.headers.get('X-AppEngine-Cron') != 'true':
            return self.serve_error(401)
        else:
            return method(self, *args, **kwds)
    return wrap
