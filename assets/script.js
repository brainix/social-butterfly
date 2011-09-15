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


/*---------------------------------------------------------------------------*\
 |                                    $()                                    |
\*---------------------------------------------------------------------------*/

$(function() {
    // Hooray, a page has been loaded!

    var handle = $('#content .sign-up .register [name="handle"]');
    if (handle.length) {
        handle.focus(focusHandle);
        handle.blur(blurHandle);
        $('#content .sign-up .register').submit(signUp);
        var defaultHandle = handle.prop('defaultValue');
        handle.val(defaultHandle);
    }

    if ($('.flipclock').length) {
        $('.flipclock.num_users').flipclock('init', {digits: 4});
        $('.flipclock.num_active_users').flipclock('init', {digits: 4});
        $('.flipclock.num_messages').flipclock('init', {digits: 4});
        window.setTimeout(updateStats, 3 * 1000);
    }

    if ($('#gravatars').length) {
        slideshow();
    }

    if (typeof(token) !== 'undefined' && typeof(socket) !== 'undefined') {
        openSocket();
        window.setInterval(openSocket, 2 * 60 * 60 * 1000);
    }
});


/*---------------------------------------------------------------------------*\
 |                               focusHandle()                               |
\*---------------------------------------------------------------------------*/

function focusHandle() {
    var handle = $('#content .sign-up .register [name="handle"]');
    var defaultHandle = handle.prop('defaultValue');
    if (handle.val() == defaultHandle) {
        handle.val('');
    }
}


/*---------------------------------------------------------------------------*\
 |                                blurHandle()                               |
\*---------------------------------------------------------------------------*/

function blurHandle() {
    var handle = $('#content .sign-up .register [name="handle"]');
    if (handle.val() == '') {
        var defaultHandle = handle.prop('defaultValue');
        handle.val(defaultHandle);
    }
}


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
            setStats(data);
        }
    });
}


/*---------------------------------------------------------------------------*\
 |                                 setStats()                                |
\*---------------------------------------------------------------------------*/

function setStats(json) {
    json = $.parseJSON(json);
    $.each(json, function(key, val) {
        var objs = $('.flipclock.' + key);
        if (objs.length) {
            objs.flipclock('set', val);
        }

        var objs = $('.' + key).not('.flipclock');
        if (objs.length && objs.html() != val) {
            objs.html(val);
            objs.stop(true, true).effect('highlight', {color: '#D1D9DC'}, 1000);
        }

        var growl = '';
        switch (key) {
            case 'homepage_event':      growl = 'someone is viewing the homepage';          break;
            case 'sign_up_event':       growl = 'a new user has signed up';                 break;
            case 'stats_page_event':    growl = 'someone is viewing the stats page';        break;
            case 'album_page_event':    growl = 'someone is viewing the album page';        break;
            case 'tech_page_event':     growl = 'someone is viewing the tech page';         break;
            case 'help_event':          growl = 'a user has typed /help';                   break;
            case 'start_event':         growl = 'a user has typed /start';                  break;
            case 'next_event':          growl = 'a user has typed /next';                   break;
            case 'stop_event':          growl = 'a user has typed /stop';                   break;
            case 'me_event':            growl = 'a user has typed a /me command';           break;
            case 'text_message_event':  growl = 'a user has sent a text message';           break;
            case 'available_event':     growl = 'a user has become available for chat';     break;
            case 'unavailable_event':   growl = 'a user has become unavailable for chat';   break;
        }
        if (growl) {
            $.jGrowl(growl);
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

                // var snippet =   '<a href="' + gravatar.profile + '">';
                // snippet +=          '<img src="' + gravatar.image + '"';
                // snippet +=          '     style="display: none;"';
                // snippet +=          '     alt="Social Butterfly" />';
                // snippet +=      '</a>';
                snippet =          '<img src="' + gravatar.image + '"';
                snippet +=         '     style="display: none;"';
                snippet +=         '     alt="Social Butterfly" />';

                $('#gravatars').append(snippet);
                slideshowIndex++;

                // $('#gravatars a:last-child img').fadeIn('slow', slideshow);
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
    setStats(message.data);
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
