#------------------------------------------------------------------------------#
#   config.py                                                                  #
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


import logging
import os


_log = logging.getLogger(__name__)


# Programmatically determine whether to turn on debug mode.  If we're running
# on the SDK, then turn on debug mode.  Otherwise we're running on the cloud,
# so turn off debug mode.
_SERVER_SOFTWARE = os.getenv('SERVER_SOFTWARE', '')
DEBUG = _SERVER_SOFTWARE.split('/', 1)[0] == 'Development'
_log.debug('turning %s debug mode' % ('on' if DEBUG else 'off'))


_CURRENT_PATH = os.path.dirname(__file__)
TEMPLATES = os.path.join(_CURRENT_PATH, 'templates')


AGES = ['teen', '20 something', '30 something', '40 something +']
SEXES = ['male', 'female']


HELP_TEXT = 'Type /start to chat with a random stranger.  Type /next to chat with a different random stranger.  Type /stop to stop chatting with random strangers.'
SEARCHING_TEXT = 'Searching for a random stranger...'
STARTING_TEXT = 'Chatting with %s, %s / %s / %s.'
REJECTING_TEXT = '%s has stopped chatting with you.'
REJECTED_TEXT = "You've stopped chatting with %s."
STOPPING_TEXT = "You've stopped chatting with random strangers.  Type /start at any time to resume."


HTTP_CODE_TO_TITLE = {
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing (WebDAV)',
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi-Status (WebDAV)',
    226: 'IM Used',
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: 'Switch Proxy',
    307: 'Temporary Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    418: "I'm a Teapot",
    422: 'Unprocessable Entity (WebDAV)',
    423: 'Locked (WebDAV)',
    424: 'Failed Dependency (WebDAV)',
    425: 'Unordered Collection',
    426: 'Upgrade Required',
    449: 'Retry With',
    500: 'Internal Server Error',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',
    507: 'Insufficient Storage (WebDAV)',
    509: 'Bandwidth Limit Exceeded',
    510: 'Not Extended',
}
