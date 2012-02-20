#-----------------------------------------------------------------------------#
#   models.py                                                                 #
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
"""Google App Engine datastore models."""


import logging

from google.appengine.ext import db

from config import MIN_GMAIL_ADDR_LEN, MAX_GMAIL_ADDR_LEN
from config import VALID_GMAIL_CHARS, VALID_GMAIL_DOMAINS


_log = logging.getLogger(__name__)


class Account(db.Model):
    """ """

    handle = db.IMProperty(required=True, indexed=False)
    started = db.BooleanProperty(required=True)
    available = db.BooleanProperty(required=True)
    partner = db.SelfReferenceProperty()
    partners = db.ListProperty(db.Key, default=[], required=True, indexed=False)
    datetime = db.DateTimeProperty(required=True, auto_now=True)
    subscribed = db.DateTimeProperty()

    def __str__(self):
        """ """
        return self.handle.address

    def __eq__(self, other):
        """ """
        return str(self) == str(other)

    def __ne__(self, other):
        """ """
        return str(self) != str(other)

    @staticmethod
    def handle_to_key(handle):
        """Convert an IM handle address into an account key name."""
        key_name = 'account_' + handle.split('/', 1)[0].lower()
        return key_name

    @staticmethod
    def key_to_handle(key_name):
        """Convert an account key name into an IM handle address."""
        handle = key_name[len('_account'):]
        return handle

    @classmethod
    def factory(cls, handle):
        """A user has signed up.  Create his/her Social Butterfly account."""
        handle = cls._sanitize_handle(handle)
        _log.debug('creating account %s' % handle)
        cls._validate_handle(handle)

        handle = db.IM('xmpp', handle)
        key_name = cls.handle_to_key(handle.address)

        def txn():
            account = cls.get_by_key_name(key_name)
            if account is not None:
                created = False
                body = "couldn't create account %s: already exists" % account
                _log.warning(body)
            else:
                account = cls(key_name=key_name, handle=handle, started=False,
                              available=False)
                account.put()
                created = True
                _log.info('created account %s' % account)
            return account, created

        account, created = db.run_in_transaction(txn)
        return account, created

    @staticmethod
    def _sanitize_handle(handle):
        """A user has signed up.  Clean up his/her chat handle."""
        handle = handle.strip().lower()

        if not '@' in handle:
            valid_domains = ['@' + domain for domain in VALID_GMAIL_DOMAINS]
            valid_domains = tuple(valid_domains)
            if not handle.endswith(valid_domains):
                handle += valid_domains[0]

        return handle

    @staticmethod
    def _validate_handle(handle):
        """A user has signed up.  Validate his/her chat handle."""

        def log_and_raise(body):
            head = "couldn't create account %s: " % handle
            _log.warning(head + body)
            raise ValueError(body)

        try:
            local, domain = handle.split('@')
        except ValueError:
            body = "handle doesn't have exactly one at (@) sign"
            log_and_raise(body)

        if not MIN_GMAIL_ADDR_LEN <= len(local) <= MAX_GMAIL_ADDR_LEN:
            body = "handle's local part doesn't meet length requirements"
            log_and_raise(body)

        invalid_chars = set(local).difference(VALID_GMAIL_CHARS)
        if invalid_chars:
            body = "handle's local part has invalid characters"
            log_and_raise(body)

        if domain not in VALID_GMAIL_DOMAINS:
            body = 'handle ends with invalid domain'
            log_and_raise(body)

    @classmethod
    def get_users(cls, keys_only=True, started=None, available=None,
                  chatting=None, order=None):
        """ """
        assert keys_only in (False, True)
        assert started in (None, False, True)
        assert available in (None, False, True)
        assert chatting in (None, False, True)
        assert order in (None, False, True)

        carols = cls.all(keys_only=keys_only)
        if started is not None:
            carols = carols.filter('started =', started)
        if available is not None:
            carols = carols.filter('available =', available)
        if chatting == False:
            carols = carols.filter('partner =', None)
        elif chatting == True:
            carols = carols.filter('partner !=', None)
            carols.order('partner')
        if order is not None:
            carols = carols.order('datetime' if order else '-datetime')
        return carols

    @classmethod
    def _count_users(cls, started=None, available=None, chatting=None):
        """ """
        num_carols = 0
        carols = cls.get_users(started=started, available=available,
                               chatting=chatting)
        num_batch = carols.count()
        while num_batch > 0:
            num_carols += num_batch
            cursor = carols.cursor()
            carols = carols.with_cursor(cursor)
            num_batch = carols.count()
        return num_carols

    @classmethod
    def num_users(cls):
        """Return the total number of users."""
        return cls._count_users()

    @classmethod
    def num_active_users(cls):
        """Return the number of started and available users."""
        return cls._count_users(started=True, available=True)
