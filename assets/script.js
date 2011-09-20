/*---------------------------------------------------------------------------*\
 |  script.js                                                                |
 |                                                                           |
 |  Copyright (c) 2010-2011, Code A La Mode, original authors.               |
 |                                                                           |
 |      This file is part of Social Butterfly.                               |
 |                                                                           |
 |      Social Butterfly is free software; you can redistribute it and/or    |
 |      modify it under the terms of the GNU General Public License as       |
 |      published by the Free Software Foundation, either version 3 of the   |
 |      License, or (at your option) any later version.                      |
 |                                                                           |
 |      Social Butterfly is distributed in the hope that it will be useful,  |
 |      but WITHOUT ANY WARRANTY; without even the implied warranty of       |
 |      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        |
 |      GNU General Public License for more details.                         |
 |                                                                           |
 |      You should have received a copy of the GNU General Public License    |
 |      along with Social Butterfly.  If not, see:                           |
 |          <http://www.gnu.org/licenses/>.                                  |
\*---------------------------------------------------------------------------*/


var SEC = 1000;
var MIN = 60 * SEC;
var HR = 60 * MIN;


/*---------------------------------------------------------------------------*\
 |                                    $()                                    |
\*---------------------------------------------------------------------------*/

$(function() {
    // Hooray, a page has been loaded!

    var handle = $('#content .sign-up .register [name="handle"]');
    if (handle.length) {
        $('#content .sign-up .register').submit(signUp);
    }

    if ($('.flipclock').length) {
        $('.flipclock.num_users').flipclock('init', {digits: 4});
        $('.flipclock.num_active_users').flipclock('init', {digits: 4});
        $('.flipclock.num_messages').flipclock('init', {digits: 4});
        window.setTimeout(updateStats, 3 * SEC);
    }

    if ($('#gravatars').length) {
        slideshow();
    }

    if (typeof(token) !== 'undefined' && typeof(socket) !== 'undefined') {
        openSocket();
        window.setInterval(openSocket, 1 * HR + 59 * MIN);
    }
});


/*---------------------------------------------------------------------------*\
 |                                  signUp()                                 |
\*---------------------------------------------------------------------------*/

var signUpSubmitted = false;

function signUp() {
    var handle = $('#content .sign-up .register [name="handle"]').val();
    $.ajax({
        type: 'POST',
        url: '/',
        data: {handle: handle},
        cache: false,
        beforeSend: function(jqXHR, settings) {
            if (signUpSubmitted) {
                var message = "You've already submitted a request to sign up.\n";
                message += "Please wait for this request to complete.";
                alert(message);
                return false;
            } else {
                signUpSubmitted = true;
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            var message = '';
            switch (jqXHR.status) {
                case 400:
                    message = "Oops, you've entered an invalid Google Talk ";
                    message += 'address.\n\nPlease correct your Google Talk ';
                    message += 'address and sign up again.';
                    break;
                default:
                    message = 'Oops, something has gone wrong.\n\nPlease try ';
                    message += 'to sign up again.';
            }
            alert(message);
        },
        success: function(data, textStatus, jqXHR) {
            var signUpForm = $('#content .sign-up');
            signUpForm.fadeOut('slow', function() {
                var signedUpText = $('#content .signed-up');
                signedUpText.fadeIn('slow');
            });
        },
        complete: function(jqXHR, textStatus) {
            signUpSubmitted = false;
        }
    });
    return false;
}


/*---------------------------------------------------------------------------*\
 |                               updateStats()                               |
\*---------------------------------------------------------------------------*/

function updateStats() {
    $.ajax({
        type: 'GET',
        url: '/get-stats',
        cache: false,
        success: function(data, textStatus, jqXHR) {
            parseJSON(data);
        }
    });
}


/*---------------------------------------------------------------------------*\
 |                                parseJSON()                                |
\*---------------------------------------------------------------------------*/

function parseJSON(json) {
    json = $.parseJSON(json);
    $.each(json, function(key, val) {
        var flipclocks = $('.flipclock.' + key);
        if (flipclocks.length) {
            flipclocks.flipclock('set', val);
        }

        var footerCounters = $('.' + key).not('.flipclock');
        if (footerCounters.length && footerCounters.html() != val) {
            footerCounters.html(val);
            footerCounters.stop(true, true);
            footerCounters.effect('highlight', {color: '#D1D9DC'}, 1 * SEC);
        }

        var notification = $('#' + key);
        if (notification.length) {
            notification.sticky();
        }

        if (key == 'feedback') {
            var feedbackComments = $('#feedback-comments');
            if (feedbackComments.length) {
                feedbackComments.prepend(val);
                var comment = $('.feedback-comment').filter(':first');
                comment.fadeIn();
            }
        }
    });
}


/*---------------------------------------------------------------------------*\
 |                                slideshow()                                |
\*---------------------------------------------------------------------------*/

var slideshowIndex = 0;

function slideshow() {
    if (slideshowIndex < gravatars.length) {
        var gravatar = gravatars[slideshowIndex];
        $.ajax({
            type: 'GET',
            url: gravatar.image,
            error: function(jqXHR, textStatus, errorThrown) {
                gravatars.splice(slideshowIndex, 1);
                slideshow();
            },
            success: function(data, textStatus, jqXHR) {
                snippet =  '<img src="' + gravatar.image + '"';
                snippet += '     style="display: none;"';
                snippet += '     alt="Social Butterfly" />';

                $('#gravatars').append(snippet);
                slideshowIndex++;

                $('#gravatars img:last-child').fadeIn('slow', slideshow);
            }
        });
    }
}


/*---------------------------------------------------------------------------*\
 |                                openSocket()                               |
\*---------------------------------------------------------------------------*/

function openSocket() {
    $.ajax({
        type: 'GET',
        url: '/get-token',
        cache: false,
        beforeSend: function(jqXHR, settings) {
            if (socket) {
                socket.close();
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            token = null;
            socket = null;
        },
        success: function(data, textStatus, jqXHR) {
            token = data;
            var channel = new goog.appengine.Channel(token);
            socket = channel.open();
            socket.onopen = socketOpened;
            socket.onmessage = socketMessaged;
            socket.onerror = socketErrored;
            socket.onclose = socketClosed;
        }
    });
}


/*---------------------------------------------------------------------------*\
 |                               socketOpened()                              |
\*---------------------------------------------------------------------------*/

function socketOpened() {
}


/*---------------------------------------------------------------------------*\
 |                              socketMessaged()                             |
\*---------------------------------------------------------------------------*/

function socketMessaged(message) {
    parseJSON(message.data);
}


/*---------------------------------------------------------------------------*\
 |                              socketErrored()                              |
\*---------------------------------------------------------------------------*/

function socketErrored(error) {
}


/*---------------------------------------------------------------------------*\
 |                               socketClosed()                              |
\*---------------------------------------------------------------------------*/

function socketClosed() {
}
