#-----------------------------------------------------------------------------#
#   appengine_config.py                                                       #
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
"""Appstats configuration.

For more information, see:
    http://code.google.com/appengine/docs/python/tools/appstats.html
"""


# Apparently, we have to import coldstart at the top of this module as well as
# at the top of the main.py module.  Otherwise, we get tracebacks like this:
#
#   <class 'google.appengine.dist._library.UnacceptableVersionError'>: django 1.2 was requested, but 0.96.4.None is already in use
#   Traceback (most recent call last):
#     File "/base/data/home/apps/social-butterfly/1.353755632328827004/main.py", line 25, in <module>
#       import coldstart
#     File "/base/data/home/apps/social-butterfly/1.353755632328827004/coldstart.py", line 50, in <module>
#       use_library(library, version)
#     File "/base/python_runtime/python_lib/versions/1/google/appengine/dist/_library.py", line 414, in use_library
#       InstallLibrary(name, version, explicit=True)
#     File "/base/python_runtime/python_lib/versions/1/google/appengine/dist/_library.py", line 367, in InstallLibrary
#       CheckInstalledVersion(name, version, explicit=True)
#     File "/base/python_runtime/python_lib/versions/1/google/appengine/dist/_library.py", line 300, in CheckInstalledVersion
#       (name, desired_version, installed_version))
#
# google.appengine.ext.appstats.recording must be importing some Django module.
# So if we import google.appengine.ext.appstats.recording before we import
# coldstart, Google App Engine will pick the wrong (default) Django version.
#
# For more information, see:
#   http://stackoverflow.com/questions/4994913/app-engine-default-django-version-change

import coldstart

import logging

from google.appengine.ext.appstats import recording


_log = logging.getLogger(__name__)


def webapp_add_wsgi_middleware(app):
    """ """
    _log.debug('enabling appstats')
    app = recording.appstats_wsgi_middleware(app)
    return app
