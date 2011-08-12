#-----------------------------------------------------------------------------#
#   filters.py                                                                #
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
"""Custom Django page template filters."""


import hashlib
import logging
import urllib

from google.appengine.ext.webapp.template import create_template_register


_log = logging.getLogger(__name__)
register = create_template_register()


@register.filter
def user_to_gravatar(user, size=256):
    """Convert a user object into a Gravatar (globally recognized avatar) URL.

    For more information, see:
        http://en.gravatar.com/site/implement/url
    """
    email = str(user)
    hash = hashlib.md5(email).hexdigest()
    query = {
        'size': size,
        'default': 404,
        'rating': 'g',
    }
    query = urllib.urlencode(query)

    gravatar = 'http://www.gravatar.com/avatar/%s.jpg?%s'
    gravatar %= hash, query
    return gravatar
