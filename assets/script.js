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


var _gaq = _gaq || [];
var token = null;
var socket = null;


/*---------------------------------------------------------------------------*\
 |                                    $()                                    |
\*---------------------------------------------------------------------------*/

$(function() {
    // Hooray, a page has been loaded!

    preloadImages(
        '/assets/images/flipclock/0.png',   '/assets/images/flipclock/0-1.png',
        '/assets/images/flipclock/1.png',   '/assets/images/flipclock/1-2.png',
        '/assets/images/flipclock/2.png',   '/assets/images/flipclock/2-3.png',
        '/assets/images/flipclock/3.png',   '/assets/images/flipclock/3-4.png',
        '/assets/images/flipclock/4.png',   '/assets/images/flipclock/4-5.png',
        '/assets/images/flipclock/5.png',   '/assets/images/flipclock/5-6.png',
        '/assets/images/flipclock/6.png',   '/assets/images/flipclock/6-7.png',
        '/assets/images/flipclock/7.png',   '/assets/images/flipclock/7-8.png',
        '/assets/images/flipclock/8.png',   '/assets/images/flipclock/8-9.png',
        '/assets/images/flipclock/9.png',   '/assets/images/flipclock/9-0.png'
    );

    openSocket();
    window.setInterval(openSocket, 1 * HR + 59 * MIN);

    _gaq.push(['_setAccount', 'UA-2153971-5']);
    var ga = document.createElement('script');
    ga.type = 'text/javascript';
    ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(ga, s);

    $(window).bind('hashchange', hashChanged);
    hashChanged();
});


/*---------------------------------------------------------------------------*\
 |                              preloadImages()                              |
\*---------------------------------------------------------------------------*/

function preloadImages() {
    if (document.images) {
        var images = [];
        for (var index = 0; index < preloadImages.arguments.length; index++) {
            images[index] = new Image();
            images[index].src = preloadImages.arguments[index];
        }
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


/*---------------------------------------------------------------------------*\     
 |                               hashChanged()                               |
\*---------------------------------------------------------------------------*/     

function hashChanged() {
    var hashBang = getHashBang();
    if (hashBang) {
        ajaxLoadHashBang(hashBang);
    } else {
        init();
    }
}


/*---------------------------------------------------------------------------*\     
 |                               getHashBang()                               |
\*---------------------------------------------------------------------------*/     

function getHashBang() {
    var hash = location.hash;
    var hashBang = '';
    if (!hash || hash.charAt(1) !== '!') {
        hashBang = 'home';
    } else {
        hashBang = hash.slice(2);
    }
    return hashBang;
}


/*---------------------------------------------------------------------------*\     
 |                             ajaxLoadHashBang()                            |
\*---------------------------------------------------------------------------*/     

var hashBangRequest = null;

function ajaxLoadHashBang(hashBang) {
    if (hashBangRequest) {
        hashBangRequest.abort();
        hashBangRequest = null;
    }

    var url = location.toString();
    var index = url.lastIndexOf('/');
    url = url.slice(0, index + 1);

    hashBangRequest = $.ajax({
        type: 'GET',
        url: url,
        data: {snippet: hashBang},
        cache: false,
        error: function(jqXHR, textStatus, errorThrown) {
            populateHashBang(jqXHR.responseText);
        },
        success: function(data, textStatus, jqXHR) {
            populateHashBang(data);
        },
        complete: function(jqXHR, textStatus) {
            hashBangRequest = null;
            init();
        }
    });
}


/*---------------------------------------------------------------------------*\     
 |                             populateHashBang()                            |
\*---------------------------------------------------------------------------*/     

function populateHashBang(json) {
    var obj = $.parseJSON(json);
    document.title = 'social butterfly - ' + obj.title;
    $('header hgroup h2').html(obj.title);
    $('article').html(obj.snippet);
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
    }

    if ($('#gravatars').length) {
        startSlideshow();
    }

    var url = location.pathname + location.search + location.hash;
    _gaq.push(['_trackPageview', url]);
    _gaq.push(['_trackPageLoadTime']);
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
                var signUpAlreadySubmitted = signUpSubmitted;
                if (signUpSubmitted) {
                    var message = "You've already submitted a request to ";
                    message += "sign up.\n\nPlease wait for that request to ";
                    message += "complete.";
                    alert(message);
                } else {
                    signUpSubmitted = true;
                }
                return !signUpAlreadySubmitted;
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
                        message = "Oops, we've messed something up, and ";
                        message += "we're looking into the problem.\n\n";
                        message += "Please try to sign up again.";
                        break;
                }
                alert(message);
            },
            success: function(data, textStatus, jqXHR) {
                var signUpForm = $('.sign-up');
                signUpForm.hide(0, function() {
                    var signedUpText = $('.signed-up');
                    signedUpText.show(0);
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
 |                                parseJSON()                                |
\*---------------------------------------------------------------------------*/

function parseJSON(json) {
    var obj = $.parseJSON(json);
    $.each(obj, function(key, val) {
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

function startSlideshow() {
    slideshowIndex = 0;
    slideshow();
}

function slideshow() {
    if (slideshowIndex < gravatars.length) {
        var gravatar = gravatars[slideshowIndex];
        $.ajax({
            type: 'GET',
            url: gravatar.image,
            error: function(jqXHR, textStatus, errorThrown) {
                gravatars.splice(slideshowIndex, 1);
            },
            success: function(data, textStatus, jqXHR) {
                snippet =  '<img src="' + gravatar.image + '"';
                snippet += '     alt="Social Butterfly" />';
                $('#gravatars').append(snippet);
                slideshowIndex++;
            },
            complete: function(jqXHR, textStatus) {
                slideshow();
            }
        });
    }
}
