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


ENTER_KEYCODE = 13;


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

    var feedback = $('#content .feedback-form [name="feedback"]');
    if (feedback.length) {
        feedback.focus(focusFeedback);
        feedback.blur(blurFeedback);
        feedback.keydown(keydownFeedback);
        feedback.keyup(changeFeedback);
        feedback.change(changeFeedback);
        feedback.bind('input cut', function(event) {changeFeedback();});
        feedback.bind('input paste', function(event) {changeFeedback();});
        $('#content .feedback-form').submit(submitFeedback);
        var defaultFeedback = feedback.prop('defaultValue');
        feedback.val(defaultFeedback);
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
 |                                  focus()                                  |
\*---------------------------------------------------------------------------*/

function focus(selector) {
    var element = $(selector);
    var defaultValue = element.prop('defaultValue');
    if (element.val() == defaultValue) {
        element.val('');
    }
}


/*---------------------------------------------------------------------------*\
 |                                   blur()
\*---------------------------------------------------------------------------*/

function blur(selector) {
    var element = $(selector);
    if (element.val() == '') {
        var defaultHandle = element.prop('defaultValue');
        element.val(defaultHandle);
    }
}


/*---------------------------------------------------------------------------*\
 |                               focusHandle()                               |
\*---------------------------------------------------------------------------*/

function focusHandle() {
    focus('#content .sign-up .register [name="handle"]');
}


/*---------------------------------------------------------------------------*\
 |                                blurHandle()                               |
\*---------------------------------------------------------------------------*/

function blurHandle() {
    blur('#content .sign-up .register [name="handle"]');
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
 |                              focusFeedback()                              |
\*---------------------------------------------------------------------------*/

function focusFeedback() {
    focus('#content .feedback-form [name="feedback"]');
}


/*---------------------------------------------------------------------------*\
 |                               blurFeedback()                              |
\*---------------------------------------------------------------------------*/

function blurFeedback() {
    blur('#content .feedback-form [name="feedback"]');
}


/*---------------------------------------------------------------------------*\
 |                             keydownFeedback()                             |
\*---------------------------------------------------------------------------*/

function keydownFeedback(e) {
    if (e.keyCode == ENTER_KEYCODE) {
        var countdown = $('#content .feedback-form .chars-remaining .char-countdown');
        var num_left = parseInt(countdown.html());
        if (num_left >= 0) {
            var feedback = $('#content .feedback-form');
            feedback.submit();
        }
        return false;
    }
}


/*---------------------------------------------------------------------------*\
 |                              changeFeedback()                             |
\*---------------------------------------------------------------------------*/

function changeFeedback() {
    var comment = $('#content .feedback-form [name="feedback"]').val();
    var num = comment.length;
    var num_left = 140 - num;
    num_left = num_left.toString();

    var countdown = $('#content .feedback-form .chars-remaining .char-countdown');
    if (countdown.html() != num_left) {
        countdown.html(num_left);
        if (num_left < 0) {
            countdown.addClass('chars-over-limit');
        } else {
            countdown.removeClass('chars-over-limit');
        }
        countdown.stop(true, true).effect('highlight', {color: '#D1D9DC'}, 1000);
    }
}


/*---------------------------------------------------------------------------*\
 |                              submitFeedback()                             |
\*---------------------------------------------------------------------------*/

var feedbackSubmitted = false;

function submitFeedback() {
    var feedback = $('#content .feedback-form [name="feedback"]');
    var comment = feedback.val();
    $.ajax({
        type: 'POST',
        url: '/feedback',
        data: {comment: comment},
        cache: false,
        beforeSend: function(jqXHR, settings) {
            if (feedbackSubmitted) {
                var message = "You've already submitted a comment.\n";
                message += "Please wait for this request to complete.";
                alert(message);
                return false;
            } else {
                feedbackSubmitted = true;
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            message = 'Oops, something has gone wrong.\n\n';
            message += 'Please try to submit your comment again.';
            alert(message);
        },
        success: function(data, textStatus, jqXHR) {
            feedback.val('');
            var countdown = $('#content .feedback-form .chars-remaining .char-countdown');
            countdown.html('140');
            countdown.removeClass('chars-over-limit');
            countdown.stop(true, true).effect('highlight', {color: '#D1D9DC'}, 1000);
        },
        complete: function(jqXHR, textStatus) {
            feedbackSubmitted = false;
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

        if ($('#' + key).length) {
            $('#' + key).sticky();
        }

        if (key == 'feedback') {
            $('#feedback-comments').prepend(val);
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
