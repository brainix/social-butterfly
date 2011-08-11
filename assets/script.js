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

    if ($('#num-users').flipclock('init', {digits: 3}).length) {
        $('#num-active-users').flipclock('init');
        window.setTimeout(updateStats, 1500);
        window.setInterval(updateStats, 30000);
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
            success: function(data, textStatus, xmlHttpRequest) {
                var signUpForm = $('#content .sign-up');
                signUpForm.fadeOut('slow', function() {
                    var signedUpText = $('#content .signed-up');
                    signedUpText.fadeIn('slow');
                });
            },
            error: function(xmlHttpRequest, textStatus, errorThrown) {
                var message = '';
                switch (xmlHttpRequest.status) {
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
            complete: function(xmlHttpRequest, textStatus) {
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
        success: function(data, textStatus, xmlHttpRequest) {
            data = $.parseJSON(data);
            $.each(data, function(key, val) {
                var obj = $('#' + key);
                obj.flipclock('set', val);
            });
        }
    });
}