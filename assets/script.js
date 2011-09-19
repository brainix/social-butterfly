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

    var comment = $('#content .feedback-form [name="comment"]');
    if (comment.length) {
        comment.focus(focusComment);
        comment.blur(blurComment);
        comment.keydown(keydownComment);
        comment.keyup(changeComment);
        comment.change(changeComment);
        comment.bind('input cut', function(e) {changeComment();});
        comment.bind('input paste', function(e) {changeComment();});

        var feedbackForm = $('#content .feedback-form');
        feedbackForm.submit(submitFeedback);

        var defaultFeedback = comment.prop('defaultValue');
        comment.val(defaultFeedback);
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
 |                               focusComment()                              |
\*---------------------------------------------------------------------------*/

function focusComment() {
    focus('#content .feedback-form [name="comment"]');
}


/*---------------------------------------------------------------------------*\
 |                               blurComment()                               |
\*---------------------------------------------------------------------------*/

function blurComment() {
    blur('#content .feedback-form [name="comment"]');
}


/*---------------------------------------------------------------------------*\
 |                              keydownComment()                             |
\*---------------------------------------------------------------------------*/

function keydownComment(e) {
    if (e.keyCode == ENTER_KEYCODE) {
        var countdown = $('#content .feedback-form .chars-remaining .char-countdown');
        var numLeft = parseInt(countdown.html());
        if (numLeft >= 0) {
            var feedback = $('#content .feedback-form');
            feedback.submit();
        }
        return false;
    }
}


/*---------------------------------------------------------------------------*\
 |                              changeComment()                              |
\*---------------------------------------------------------------------------*/

function changeComment() {
    var comment = $('#content .feedback-form [name="comment"]');
    var numUsed = comment.val().length;
    var numLeft = 140 - numUsed;
    numLeft = numLeft.toString();

    var countdown = $('#content .feedback-form .chars-remaining .char-countdown');
    if (countdown.html() != numLeft) {
        countdown.html(numLeft);
        if (numLeft < 0) {
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
    var comment = $('#content .feedback-form [name="comment"]');
    $.ajax({
        type: 'POST',
        url: '/feedback',
        data: {comment: comment.val()},
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
            comment.val('');
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
            footerCounters.effect('highlight', {color: '#D1D9DC'}, 1000);
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
