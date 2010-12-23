#-----------------------------------------------------------------------------#
#   models.py                                                                 #
#                                                                             #
#   Copyright (c) 2010, Code A La Mode, original authors.                     #
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
"""Google App Engine datastore models."""


from google.appengine.ext import db


class Account(db.Model):
    """ """
    handle = db.IMProperty(indexed=False, required=True)

    online = db.BooleanProperty(required=True)
    partner = db.SelfReferenceProperty()
    datetime = db.DateTimeProperty(auto_now=True, required=True)

    @staticmethod
    def key_name(handle):
        """Convert an IM handle into an account key."""
        return 'account_' + handle.split('/', 1)[0].lower()

    def __str__(self):
        """ """
        return self.handle.address

    def __eq__(self, other):
        """ """
        return self.handle.address == other.handle.address

    def __ne__(self, other):
        """ """
        return self.handle.address != other.handle.address
