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
    handle.focus(focusHandle);
    handle.blur(blurHandle);
    $('#content .sign-up .register').submit(signUp);
    var defaultHandle = handle.prop('defaultValue');
    handle.val(defaultHandle);

    if ($('.flipclock').length > 0) {
        $('.flipclock.num_users').flipclock('init', {digits: 3});
        $('.flipclock.num_active_users').flipclock('init', {digits: 3});
        $('.flipclock.num_messages').flipclock('init', {digits: 3});
        window.setTimeout(updateStats, 3 * 1000);
    }

    if ($('#gravatars').length > 0) {
        slideshow();
    }

    if (typeof(token) != 'undefined' && typeof(socket) != 'undefined') {
        openSocket(token);
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
    if (signUpSubmitted) {
        var message = "You've already submitted a request to sign up.\n";
        message += "Please wait for this request to complete.";
        alert(message);
    } else {
        signUpSubmitted = true;
        var handle = $('#content .sign-up .register [name="handle"]').val();

        $.ajax({
            type: 'POST',
            url: '/',
            data: {handle: handle},
            cache: false,
            success: function(data, textStatus, jqXHR) {
                var signUpForm = $('#content .sign-up');
                signUpForm.fadeOut('slow', function() {
                    var signedUpText = $('#content .signed-up');
                    signedUpText.fadeIn('slow');
                });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                var message = '';
                switch (jqXHR.status) {
                    case 400:
                        message = "Oops, you've entered an invalid Google ";
                        message += 'Talk address.\n\nPlease correct your ';
                        message += 'Google Talk address and sign up again.';
                        break;
                    default:
                        message = 'Oops, something has gone wrong.\n\nPlease ';
                        message += 'try to sign up again.';
                }
                alert(message);
            },
            complete: function(jqXHR, textStatus) {
                signUpSubmitted = false;
            }
        });
    }

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
        var obj = $('.flipclock.' + key);
        if (obj.length) {
            obj.flipclock('set', val);
        }

        var obj = $('#footer .' + key);
        if (obj.length && obj.html() != val) {
            obj.html(val);
            obj.effect('highlight', {color: '#D1D9DC'}, 1000);
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
            success: function(data, textStatus, jqXHR) {
                var snippet =   '<a href="' + gravatar.profile + '">';
                snippet +=          '<img src="' + gravatar.image + '"';
                snippet +=          '     style="display: none;"';
                snippet +=          '     alt="Social Butterfly" />';
                snippet +=      '</a>';
                $('#gravatars').append(snippet);
                slideshowIndex++;
                $('#gravatars a:last-child img').fadeIn('slow', slideshow);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                gravatars.splice(slideshowIndex, 1);
                slideshow();
            }
        });
    }
}


/*---------------------------------------------------------------------------*\
 |                                openSocket()                               |
\*---------------------------------------------------------------------------*/

function openSocket() {
    if (socket) {
        socket.close();
        socket = null;
    }

    $.ajax({
        type: 'GET',
        url: '/get-token',
        cache: false,
        success: function(data, textStatus, jqXHR) {
            token = data;
        },
        error: function(jqXHR, textStatus, errorThrown) {
            token = null;
        }
    });

    if (token) {
        var channel = new goog.appengine.Channel(token);
        socket = channel.open();
        socket.onopen = socketOpened;
        socket.onmessage = socketMessaged;
        socket.onerror = socketErrored;
        socket.onclose = socketClosed;
    }
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
