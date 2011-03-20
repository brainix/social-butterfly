#-----------------------------------------------------------------------------#
#   main.py                                                                   #
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
"""It's time for the dog and pony show..."""


# Let's get the ball rolling.  First things first: let's configure the logger.
import logging
from config import DEBUG
logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.INFO)
_log = logging.getLogger(__name__)


# Now that the logger is configured, before we do anything else, before we even
# import anything else, let's tell Google App Engine which library versions we
# want to use.  We have to do this now, before the rest of our imports, to
# ensure that we import the correct libraries.
#
# For more information, see:
#   http://code.google.com/appengine/docs/python/tools/libraries.html
from google.appengine.dist import use_library
from config import LIBRARIES
for library, version in LIBRARIES.items():
    _log.debug('using library %s %s' % (library, version))
    use_library(library, version)


# Now that Google App Engine is configured to use the correct library versions,
# let's move on with the rest of our imports.
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import handlers


def main():
    """It's time for the dog and pony show...
    
    This is the main entry point into our webapp.  Configure our URL mapping,
    define our WSGI webapp, then run our webapp.
    """
    url_mapping = (
        ('/_ah/xmpp/presence/probe/',           handlers.Probe),        # Probe handler.
        ('/_ah/xmpp/presence/unavailable/',     handlers.Unavailable),  # Unavailable handler.
        ('/_ah/xmpp/presence/available/',       handlers.Available),    # Available handler.
        ('/_ah/xmpp/message/chat/',             handlers.Chat),         # Chat handler.
        ('/_ah/xmpp/subscription/subscribed/',  handlers.Subscribed),   # Subscribed handler.
        ('/',                                   handlers.Home),         # /
        ('(.*)',                                handlers.NotFound),     # 404: Not Found.
    )
    app = webapp.WSGIApplication(url_mapping, debug=DEBUG)
    util.run_wsgi_app(app)


if __name__ == '__main__':
    main()
