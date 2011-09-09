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


import coldstart

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

from config import DEBUG
import handlers


_log = logging.getLogger(__name__)


def main():
    """It's time for the dog and pony show...
    
    This is the main entry point into our webapp.  Configure our URL mapping,
    define our WSGI webapp, then run our webapp.
    """

    template.register_template_library('filters')

    url_mapping = (
        ('/_ah/xmpp/presence/probe/',               handlers.Probe),            # XMPP probe handler.
        ('/_ah/xmpp/presence/unavailable/',         handlers.Unavailable),      # XMPP unavailable handler.
        ('/_ah/xmpp/presence/available/',           handlers.Available),        # XMPP available handler.
        ('/_ah/xmpp/message/error/',                handlers.Error),            # XMPP error handler.
        ('/_ah/xmpp/message/chat/',                 handlers.Chat),             # XMPP chat handler.
        ('/_ah/xmpp/subscription/unsubscribed/',    handlers.Unsubscribed),     # XMPP unsubscribed handler.
        ('/_ah/xmpp/subscription/unsubscribe/',     handlers.Unsubscribe),      # XMPP unsubscribe handler.
        ('/_ah/xmpp/subscription/subscribed/',      handlers.Subscribed),       # XMPP subscribed handler.
        ('/_ah/xmpp/subscription/subscribe/',       handlers.Subscribe),        # XMPP subscribe handler.
        ('/_ah/channel/disconnected/',              handlers.Disconnected),     # Channel disconnected handler.
        ('/_ah/channel/connected/',                 handlers.Connected),        # Channel connected handler.
        ('/flush-channels',                         handlers.FlushChannels),    # Web flush stale channels cron handler.
        ('/reset-stats',                            handlers.ResetStats),       # Web reset stats cron handler.
        ('/get-stats',                              handlers.GetStats),         # Web stats AJAX handler.
        ('/get-token',                              handlers.GetToken),         # Web channel token AJAX handler.
        ('/about',                                  handlers.About),            # Web about page handler.
        ('/album',                                  handlers.Album),            # Web album page handler.
        ('/stats',                                  handlers.Stats),            # Web stats page handler.
        ('/',                                       handlers.Home),             # Web homepage handler.
        ('(.*)',                                    handlers.NotFound),         # Web 404: Not Found handler.
    )
    app = webapp.WSGIApplication(url_mapping, debug=DEBUG)
    util.run_wsgi_app(app)


if __name__ == '__main__':
    main()
