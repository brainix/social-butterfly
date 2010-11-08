#------------------------------------------------------------------------------#
#   models.py                                                                  #
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
"""Google App Engine datastore models."""


from google.appengine.ext import db

from config import AGES, SEXES


class Account(db.Model):
    """ """
    handle = db.IMProperty(indexed=False, required=True)
    name = db.StringProperty(indexed=False, required=True)
    age = db.StringProperty(choices=set(AGES), indexed=False, required=True)
    sex = db.StringProperty(choices=set(SEXES), indexed=False, required=True)
    location = db.StringProperty(indexed=False, required=True)

    online = db.BooleanProperty(required=True)
    partner = db.SelfReferenceProperty(indexed=False)

    @staticmethod
    def key_name(handle):
        """Convert an IM handle into an account key."""
        return 'account_' + handle
