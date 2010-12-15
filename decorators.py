#------------------------------------------------------------------------------#
#   decorators.py                                                              #
#                                                                              #
#   Copyright (c) 2010, Code A La Mode, original authors.                      #
#                                                                              #
#       This file is part of Social Butterfly.                                 #
#                                                                              #
#       Social Butterfly is free software; you can redistribute it and/or      #
#       modify it under the terms of the GNU General Public License as         #
#       published by the Free Software Foundation, either version 3 of the     #
#       License, or (at your option) any later version.                        #
#                                                                              #
#       Social Butterfly is distributed in the hope that it will be useful,    #
#       but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#       GNU General Public License for more details.                           #
#                                                                              #
#       You should have received a copy of the GNU General Public License      #
#       along with Social Butterfly.  If not, see:                             #
#           <http://www.gnu.org/licenses/>.                                    #
#------------------------------------------------------------------------------#
"""Decorators to alter the behavior of request handler methods."""


import functools
import logging


_log = logging.getLogger(__name__)


def require_account(online=None):
    """ """
    def wrap1(method):
        @functools.wraps(method)
        def wrap2(self, message=None):
            assert online in (None, False, True)
            if online is None:
                log = 'decorated method %s requires registered account'
            elif not online:
                log = 'decorated method %s requires offline user'
            else:
                log = 'decorated method %s requires online user'
            _log.debug(log % method.func_name)

            alice = self.message_to_account(message)
            log = 'decorator requirements failed; '
            if alice is None:
                _log.warning(log + "user %s hasn't registered" % message.sender)
            elif online is not None and alice.online != online:
                if not online:
                    _log.warning(log + "user %s isn't offline" % message.sender)
                else:
                    _log.warning(log + "user %s isn't online" % message.sender)
            else:
                _log.debug('decorator requirements passed; calling method')
                return method(self, message=message)
        return wrap2
    return wrap1
