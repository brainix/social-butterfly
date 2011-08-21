#-----------------------------------------------------------------------------#
#   appengine_config.py                                                       #
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
"""Appstats configuration.

For more information, see:
    http://code.google.com/appengine/docs/python/tools/appstats.html
"""


import logging

from google.appengine.ext.appstats import recording


_log = logging.getLogger(__name__)


def webapp_add_wsgi_middleware(app):
    """ """
    _log.debug('enabling appstats')
    app = recording.appstats_wsgi_middleware(app)
    return app
