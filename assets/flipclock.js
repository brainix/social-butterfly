/*---------------------------------------------------------------------------*\
 |  flipclock.js                                                             |
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


(function($) {

    var settings = {
        path: '/assets/images/',
        digits: 2,
        width: 10,
        delay: 50
    };


    var methods = {
        init: function(options) {
            if (options) {
                $.extend(settings, options);
            }

            var data = this.data('flipClock');
            data = {
                imageCache: [],
                currentState: [],
                currentNum: 0
            };
            this.data('flipClock', data);

            for (var state = 0; state < 10; state += 0.5) {
                var path = stateToPath(state);
                this.flipClock('preload', path);
            }

            data = this.data('flipClock');
            for (var digit = 0; digit < settings.digits; digit++) {
                data.currentState.push(0);
            }
            this.data('flipClock', data);

            this.flipClock('draw');
            return this;
        },

        preload: function(url) {
            // Given a URL to an image, preload that image.
            if (document.images) {
                data = this.data('flipClock');
                var cachedImage = document.createElement("img");
                cachedImage.src = url;
                data.imageCache.push(cachedImage);
                this.data('flipClock', data);
            }
        },

        draw: function() {
            var data = this.data('flipClock');
            var html = '';
            for (var index = 0; index < data.currentState.length; index++) {
                var state = data.currentState[index];
                var path = stateToPath(state);
                var width = settings.width;
                var imageTag = '<img src="' + path + '" width="' + width + '%" />';
                html = imageTag + html;
            }
            this.html(html);
        },

        set: function(num) {
            var max = Math.pow(10, settings.digits) - 1;
            if (num > max) {
                var error = '$.flipclock.set(' + num + ');, ';
                error += 'but max value is ' + max;
                $.error(error);
            }

            var data = this.data('flipClock');
            data.currentNum = num;
            this.data('flipClock', data);
            this.flipClock('flip');
            return this;
        },

        flip: function() {
            flip(this);
            return this;
        }
    };


    $.fn.flipClock = function(method) {
        if (methods[method]) {
            method = methods[method];
            var args = Array.prototype.slice.call(arguments, 1);
            var retVal = method.apply(this, args);
            return retVal;
        } else if (typeof method === 'object' || !method) {
            method = methods.init;
            var retVal = method.apply(this, arguments);
            return retVal;
        } else {
            $.error("$.flipClock." + method + "() method doesn't exist");
        }
    };


    function stateToPath(state) {
        var transition = state != Math.floor(state);
        state = Math.floor(state);
        var file = String(state);
        if (transition) {
            nextState = (state + 1) % 10;
            file += '-' + nextState;
        }
        file += '.png';
        var path = settings.path + file;
        return path;
    }

    function flip(obj) {
        var data = obj.data('flipClock');

        function f() {
            for (var exponent = 0; exponent < settings.digits; exponent++) {
                var digit = data.currentNum % Math.pow(10, exponent + 1);
                digit = Math.floor(digit / Math.pow(10, exponent));
                if (data.currentState[exponent] != digit) {
                    data.currentState[exponent] = (data.currentState[exponent] + 0.5) % 10;
                    obj.flipClock('draw');
                    var timeoutId = window.setTimeout(f, settings.delay);
                    return;
                }
            }
        }
        f();

    }

})(jQuery);
