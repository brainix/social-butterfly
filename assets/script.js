/*----------------------------------------------------------------------------*\
 |  script.js                                                                 |
 |                                                                            |
 |  Copyright (c) 2010, Code A La Mode, original authors.                     |
 |                                                                            |
 |      This file is part of social-butterfly.                                |
 |                                                                            |
 |      social-butterfly is free software; you can redistribute it and/or     |
 |      modify it under the terms of the GNU General Public License as        |
 |      published by the Free Software Foundation, either version 3 of the    |
 |      License, or (at your option) any later version.                       |
 |                                                                            |
 |      social-butterfly is distributed in the hope that it will be useful,   |
 |      but WITHOUT ANY WARRANTY; without even the implied warranty of        |
 |      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         |
 |      GNU General Public License for more details.                          |
 |                                                                            |
 |      You should have received a copy of the GNU General Public License     |
 |      along with social-butterfly.  If not, see:                            |
 |          <http://www.gnu.org/licenses/>.                                   |
\*----------------------------------------------------------------------------*/


/*----------------------------------------------------------------------------*\
 |                                    $()                                     |
\*----------------------------------------------------------------------------*/

$(function() {
    // Hooray, a page has been loaded!

    var handle = $('#content .signup [name="handle"]');
    handle.focus(focusHandle);
    handle.blur(blurHandle);

    $('#content .signup').submit(signup);

    var defaultHandle = handle.attr('defaultValue');
    handle.val(defaultHandle);
});


/*----------------------------------------------------------------------------*\
 |                               focusHandle()                                |
\*----------------------------------------------------------------------------*/

function focusHandle() {
    var handle = $('#content .signup [name="handle"]');
    var defaultHandle = handle.attr('defaultValue');
    if (handle.val() == defaultHandle) {
        handle.val('');
    }
}


/*----------------------------------------------------------------------------*\
 |                                blurHandle()                                |
\*----------------------------------------------------------------------------*/

function blurHandle() {
    var handle = $('#content .signup [name="handle"]');
    if (handle.val() == '') {
        var defaultHandle = handle.attr('defaultValue');
        handle.val(defaultHandle);
    }
}


/*----------------------------------------------------------------------------*\
 |                                  signup()                                  |
\*----------------------------------------------------------------------------*/

var signupSubmitted = false;

function signup() {
    if (signupSubmitted) {
        var message = "You've already submitted a request to chat.\n";
        message += "Please wait for this request to complete.";
        alert(message);
    } else {
        signupSubmitted = true;
        var handle = $('#content .signup [name="handle"]');
        var throbber = $('#content .signup .throbber');
        var button = $('#content .signup :submit');

        handle.addClass('handle_with_throbber_shown');
        throbber.show();
        button.hide();

        $.ajax({
            type: 'POST',
            url: '/',
            data: {handle: handle.val()},
            cache: false,
            success: function(data, textStatus, xmlHttpRequest) {
            },
            complete: function(xmlHttpRequest, textStatus) {
                button.show();
                throbber.hide();
                handle.removeClass('handle_with_throbber_shown');
                signupSubmitted = false;
            }
        });
    }

    return false;
}
