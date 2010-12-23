/*---------------------------------------------------------------------------*\
 |  script.js                                                                |
 |                                                                           |
 |  Copyright (c) 2010, Code A La Mode, original authors.                    |
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

    var handle = $('#content .sign_up .register [name="handle"]');
    handle.focus(focusHandle);
    handle.blur(blurHandle);

    $('#content .sign_up .register').submit(signUp);

    var defaultHandle = handle.attr('defaultValue');
    handle.val(defaultHandle);
});


/*---------------------------------------------------------------------------*\
 |                               focusHandle()                               |
\*---------------------------------------------------------------------------*/

function focusHandle() {
    var handle = $('#content .sign_up .register [name="handle"]');
    var defaultHandle = handle.attr('defaultValue');
    if (handle.val() == defaultHandle) {
        handle.val('');
    }
}


/*---------------------------------------------------------------------------*\
 |                                blurHandle()                               |
\*---------------------------------------------------------------------------*/

function blurHandle() {
    var handle = $('#content .sign_up .register [name="handle"]');
    if (handle.val() == '') {
        var defaultHandle = handle.attr('defaultValue');
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
        var handle = $('#content .sign_up .register [name="handle"]').val();

        $.ajax({
            type: 'POST',
            url: '/',
            data: {handle: handle},
            cache: false,
            success: function(data, textStatus, xmlHttpRequest) {
                var signUpForm = $('#content .sign_up');
                signUpForm.fadeOut('slow', function() {
                    var signedUpText = $('#content .signed_up');
                    signedUpText.fadeIn('slow');
                });
            },
            error: function(xmlHttpRequest, textStatus, errorThrown) {
                var message = 'Oops, something has gone wrong.\n';
                message += 'Please try to sign up again in a bit.';
                alert(message);
            },
            complete: function(xmlHttpRequest, textStatus) {
                signUpSubmitted = false;
            }
        });
    }

    return false;
}
