#------------------------------------------------------------------------------#
#   decorators.py                                                              #
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
"""Decorators to alter the behavior of request handler methods."""


import functools
import logging


_log = logging.getLogger(__name__)


def require_account(online=None):
    """ """
    def wrap1(method):
        @functools.wraps(method)
        def wrap2(self, message=None):
            alice = self._message_to_account(message)
            if alice is None:
                return
            if online is not None and alice.online != online:
                return
            return method(self, message=message)
        return wrap2
    return wrap1
