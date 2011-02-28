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

from google.appengine.api import xmpp


_log = logging.getLogger(__name__)


def require_account(method):
    """Require that the user has signed up to access the request handler.

    Google App Engine provides similar functionality:
        from google.appengine.ext.webapp.util import login_required

    But Google App Engine's provided decorator is meant for GET webapp request
    handlers that the user interacts with through his/her browser.  We need to
    decorate GET XMPP request handlers that the user interacts with through
    Google Talk.
    
    So, on authentication failure, instead of redirecting to a login page, we
    need to reply with an XMPP instant message instructing the user how to sign
    up.
    """
    @functools.wraps(method)
    def wrap(self, message=None):
        _log.debug('decorated %s requires registered account' % method)
        alice = self.message_to_account(message)
        if alice is None:
            body = "decorator requirements failed; %s hasn't registered"
            _log.warning(body % message.sender)
            body = 'To chat with strangers, sign up here:\n\n'
            body += 'http://social-butterfly.appspot.com/\n\n'
            body += 'It takes 5 seconds!'
            message.reply(body)
        else:
            _log.debug('decorator requirements passed; calling method')
            return method(self, message=message)
    return wrap


def send_notification(method):
    """ """
    @functools.wraps(method)
    def wrap(self, alice):
        if alice is not None:
            body = method(self, alice)
            status = xmpp.send_message(str(alice), body)
            assert status in (xmpp.NO_ERROR, xmpp.INVALID_JID,
                              xmpp.OTHER_ERROR)
    return wrap


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
