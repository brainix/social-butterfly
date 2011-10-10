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

    if (typeof(token) !== 'undefined' && typeof(socket) !== 'undefined') {
        openSocket();
        window.setInterval(openSocket, 1 * HR + 59 * MIN);
    }

    var hashBang = getHashBang();
    if (hashBang) {
        ajaxLoadHashBang(hashBang);
    } else {
        init();
    }
});


/*---------------------------------------------------------------------------*\     
 |                               getHashBang()                               |
\*---------------------------------------------------------------------------*/     

function getHashBang() {
    var hashBang = '';
    var hash = window.location.hash;
    if (hash.charAt(1) == '!') {
        hashBang = hash.slice(2);
    }
    return hashBang;
}


/*---------------------------------------------------------------------------*\     
 |                             ajaxLoadHashBang()                            |
\*---------------------------------------------------------------------------*/     

function ajaxLoadHashBang(hashBang) {
    alert('loading ' + hashBang);
}


/*---------------------------------------------------------------------------*\     
 |                                   init()                                  |
\*---------------------------------------------------------------------------*/     

function init() {
    var form = $('.register');
    if (form.length) {
        form.submit(signUp);

        var handle = form.children('[name="handle"]');
        handle.focus(focusHandle);
        handle.blur(blurHandle);
        var defaultHandle = handle.prop('defaultValue');
        handle.val(defaultHandle);
    }

    var flipclocks = $('.flipclock');
    if (flipclocks.length) {
        flipclocks.filter('.num_users').flipclock('init', {digits: 4});
        flipclocks.filter('.num_active_users').flipclock('init', {digits: 4});
        flipclocks.filter('.num_messages').flipclock('init', {digits: 4});
        window.setTimeout(updateStats, 3 * SEC);
    }

    if ($('#gravatars').length) {
        slideshow();
    }
}


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
    if (element.val() === '') {
        var defaultValue = element.prop('defaultValue');       
        element.val(defaultValue);     
    }       
}       
        
        
/*---------------------------------------------------------------------------*\     
 |                               focusHandle()                               |      
\*---------------------------------------------------------------------------*/     
        
function focusHandle() {        
    focus('.register [name="handle"]');       
}       
        
        
/*---------------------------------------------------------------------------*\     
 |                                blurHandle()                               |      
\*---------------------------------------------------------------------------*/     
        
function blurHandle() {     
    blur('.register [name="handle"]');        
}


/*---------------------------------------------------------------------------*\
 |                                  signUp()                                 |
\*---------------------------------------------------------------------------*/

var signUpSubmitted = false;

function signUp() {
    var handle = $('.register [name="handle"]').val();
    if (handle === '') {
        var message = "You haven't entered your Gmail address.\n\nPlease ";
        message += "enter your Gmail address and sign up again.";
        alert(message);
    } else {
        $.ajax({
            type: 'POST',
            url: '/',
            data: {handle: handle},
            cache: false,
            beforeSend: function(jqXHR, settings) {
                if (signUpSubmitted) {
                    var message = "You've already submitted a request to ";
                    message += "sign up.\n\nPlease wait for that request to ";
                    message += "complete.";
                    alert(message);
                    return false;
                } else {
                    signUpSubmitted = true;
                    return true;
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                var message = '';
                switch (jqXHR.status) {
                    case 400:
                        message = "You've entered an invalid Gmail ";
                        message += "address.\n\nPlease correct your Gmail ";
                        message += "address and sign up again.";
                        break;
                    default:
                        message = "Oops, something has gone wrong.\n\nPlease ";
                        message += "try to sign up again.";
                        break;
                }
                alert(message);
            },
            success: function(data, textStatus, jqXHR) {
                var signUpForm = $('.sign-up');
                signUpForm.fadeOut('slow', function() {
                    var signedUpText = $('.signed-up');
                    signedUpText.fadeIn('slow');
                });
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
