#-----------------------------------------------------------------------------#
#   hashbang.py                                                               #
#                                                                             #
#   Copyright (c) 2010-2012, Code A La Mode, original authors.                #
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
from config import HOMEPAGE_EVENT, SIGN_UP_EVENT, STATS_PAGE_EVENT, ALBUM_PAGE_EVENT, TECH_PAGE_EVENT, RAJ_PAGE_EVENT
import base
import models


_log = logging.getLogger(__name__)


class _HashBangHandler(base.WebHandler):
    """Abstract base hash-bang request handler class."""

    def _respond(self, d, event=None):
        """Formulate an HTTP response, and possibly broadcast an event."""
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
        self._respond(locals())


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
        self._respond(locals(), event=HOMEPAGE_EVENT)

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
        description = 'Social Butterfly allows you to anonymously chat with random strangers.  These are Social Butterfly&rsquo;s real-time capabilities.'
        ajax_without_hash = False
        stats = self.get_stats()
        self._respond(locals(), event=STATS_PAGE_EVENT)


class _Album(_HashBangHandler):
    """Request handler to serve the album page."""

    def get(self):
        """Serve the album page."""
        path = os.path.join(TEMPLATES, 'album.html')
        snippet = self.request.snippet
        title = 'photo album'
        description = 'Social Butterfly allows you to anonymously chat with random strangers.  These are all of the Gravatars of Social Butterfly&rsquo;s users.'
        ajax_without_hash = False
        album_javascript = self._render_album_javascript()
        if not snippet:
            stats = self.get_stats()
        self._respond(locals(), event=ALBUM_PAGE_EVENT)

    @base.BaseHandler.memoize(24 * 60 * 60)
    def _render_album_javascript(self):
        """ """
        path = os.path.join(TEMPLATES, 'album_javascript.html')
        users = models.Account.get_users(order=False)
        html = template.render(path, locals(), debug=DEBUG)
        return html


class _Tech(_HashBangHandler):
    """Request handler to serve the tech page."""

    def get(self):
        """Serve the tech page."""
        path = os.path.join(TEMPLATES, 'tech.html')
        snippet = self.request.snippet
        title = 'our technologies'
        description = 'Social Butterfly allows you to anonymously chat with random strangers.  These are the technologies that we use to make Social Butterfly.'
        ajax_without_hash = False
        stats = self.get_stats()
        self._respond(locals(), event=TECH_PAGE_EVENT)


class _Raj(_HashBangHandler):
    """Request handler to serve the Raj page."""

    def get(self):
        """Serve the Raj page."""
        path = os.path.join(TEMPLATES, 'raj.html')
        snippet = self.request.snippet
        title = 'raj shah'
        description = 'Social Butterfly allows you to anonymously chat with random strangers.  I made Social Butterfly.'
        ajax_without_hash = False
        stats = self.get_stats()
        self._respond(locals(), event=RAJ_PAGE_EVENT)


class HashBangDispatch(_Chrome, _Home, _Stats, _Album, _Tech, _Raj):
    """Request handler to serve an HTML page or snippet.
    
    We have to inherit from all of the classes that we dispatch to, because in
    our GET and POST request handler dispatch methods, we pass self to the
    classes that we dispatch to.  If we didn't inherit from the classes that we
    dispatch to, passing self like that would cause some sort of type error.
    """

    def get(self):
        """Someone has requested an HTML page or snippet.  Serve it."""
        args = self.request.arguments()
        if '_escaped_fragment_' in args:
            # Googlebot is crawling us.  Figure out which page Googlebot wants
            # to see, then serve that full page (not just an HTML snippet).
            # For more info, see:
            #   http://code.google.com/web/ajaxcrawling/docs/getting-started.html
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

        base_classes = self._base_classes()
        try:
            cls = base_classes[class_name]
        except KeyError:
            self.serve_error(404)
        else:
            cls.get(self)

    def post(self):
        """ """
        _Home.post(self)

    def _base_classes(self):
        """Compute a name/class map of an instance's class's base classes."""
        cls = type(self)
        bases = cls.__bases__
        d = {}
        for cls in bases:
            name = self._class_name(cls)
            d[name] = cls
        return d

    def _class_name(self, cls):
        """Compute the given class's name.

        Assume the following class definition:

            >>> class C(object):
            ...     pass
            ...
            >>>

        If this method were called on the class definition C, see the inline
        comments for how we would determine the class name.
        """
        name = str(cls)             # <class '__main__.C'>
        name = name.split("'")[1]   # __main__.C
        name = name.split('.')[1]   # C
        return name
