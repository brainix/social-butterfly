#-----------------------------------------------------------------------------#
#   hashbang.py                                                               #
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
"""Google App Engine request handlers (concrete implementation classes)."""


import logging
import os

from django.utils import simplejson
from google.appengine.api import xmpp
from google.appengine.ext.webapp import template

from config import DEBUG, TEMPLATES
from config import NUM_USERS_KEY
from config import HOMEPAGE_EVENT, SIGN_UP_EVENT, STATS_PAGE_EVENT, ALBUM_PAGE_EVENT, TECH_PAGE_EVENT
import base
import models


_log = logging.getLogger(__name__)


class _HashBangHandler(base.WebHandler):
    """Abstract base hash-bang request handler class."""

    def _class_name(self, cls):
        """ """
        name = str(cls)
        name = name.split("'")[1]
        name = name.split('.')[1]
        return name

    def _write_response(self, d, event=None):
        """ """
        html = template.render(d['path'], d, debug=DEBUG)

        if d['snippet']:
            d = {
                'title': d['title'],
                'description': d['description'],
                'snippet': html,
            }
            json = simplejson.dumps(d)
            self.response.out.write(json)
        else:
            self.response.out.write(html)

        if event is not None:
            self.broadcast(stats=False, event=event)


class _Chrome(_HashBangHandler):
    """Request handler to serve the user interface chrome."""

    def get(self):
        """Serve the user interface chrome."""
        path = os.path.join(TEMPLATES, 'base.html')
        snippet = self.request.snippet
        title = 'loading&hellip;'
        description = 'Social Butterfly allows you to anonymously chat with random strangers through Google Talk.'
        ajax_without_hash = True
        stats = self.get_stats()
        self._write_response(locals(), event=None)


class _Home(_HashBangHandler):
    """Request handler to serve the homepage."""

    def get(self):
        """Serve the homepage."""
        path = os.path.join(TEMPLATES, 'home.html')
        snippet = self.request.snippet
        title = 'chat with strangers'
        description = 'Social Butterfly allows you to anonymously chat with random strangers through Google Talk.'
        ajax_without_hash = False
        if not snippet:
            stats = self.get_stats()
        self._write_response(locals(), event=HOMEPAGE_EVENT)

    def post(self):
        """A user has signed up.  Create an account, and send a chat invite."""
        handle = self.request.get('handle')
        _log.info('%s signing up' % handle)
        if not handle:
            _log.warning("%s couldn't sign up (didn't supply handle)" % handle)
            self.serve_error(400)
        else:
            try:
                account, created = models.Account.factory(handle)
            except ValueError:
                body = "%s couldn't sign up (error creating account)" % handle
                _log.warning(body)
                self.serve_error(400)
            else:
                xmpp.send_invite(str(account))
                _log.info('%s signed up' % handle)
                if created:
                    self.update_stat(NUM_USERS_KEY, 1)
                    self.broadcast(stats=True, event=SIGN_UP_EVENT)
                    self.send_presence_to_all()


class _Stats(_HashBangHandler):
    """Request handler to serve the stats page."""

    def get(self):
        """Serve the stats page."""
        path = os.path.join(TEMPLATES, 'stats.html')
        snippet = self.request.snippet
        title = 'interesting statistics'
        description = 'Social Butterfly&rsquo;s real-time capabilities.'
        ajax_without_hash = False
        stats = self.get_stats()
        self._write_response(locals(), event=STATS_PAGE_EVENT)


class _Album(_HashBangHandler):
    """Request handler to serve the album page."""

    def get(self):
        """Serve the album page."""
        path = os.path.join(TEMPLATES, 'album.html')
        snippet = self.request.snippet
        title = 'photo album'
        description = 'All of the Gravatars of Social Butterfly&rsquo;s users.'
        ajax_without_hash = False
        album_javascript = self._render_album_javascript()
        if not snippet:
            stats = self.get_stats()
        self._write_response(locals(), event=ALBUM_PAGE_EVENT)

    @base.BaseHandler.memoize(24 * 60 * 60)
    def _render_album_javascript(self):
        """ """
        path = os.path.join(TEMPLATES, 'album_javascript.html')
        users = self.get_users(order=False)
        html = template.render(path, locals(), debug=DEBUG)
        return html


class _Tech(_HashBangHandler):
    """Request handler to serve the tech page."""

    def get(self):
        """Serve the tech page."""
        path = os.path.join(TEMPLATES, 'tech.html')
        snippet = self.request.snippet
        title = 'our technologies'
        description = 'The technologies we use to make Social Butterfly.'
        ajax_without_hash = False
        stats = self.get_stats()
        self._write_response(locals(), event=TECH_PAGE_EVENT)


class HashBangDispatcher(_Chrome, _Home, _Stats, _Album, _Tech):
    """ """

    def get(self):
        """ """
        bases = {}
        for cls in self.__class__.__bases__:
            class_name = self._class_name(cls)
            bases[class_name] = cls

        args = self.request.arguments()
        if '_escaped_fragment_' in args:
            class_name = self.request.get('_escaped_fragment_').title()
            if not class_name:
                class_name = 'Home'
            self.request.snippet = False
        elif 'snippet' in args:
            class_name = self.request.get('snippet').title()
            self.request.snippet = True
        else:
            class_name = 'Chrome'
            self.request.snippet = False

        class_name = '_' + class_name
        try:
            cls = bases[class_name]
        except KeyError:
            self.serve_error(404)
        else:
            cls.get(self)

    def post(self):
        """ """
        _Home.post(self)
