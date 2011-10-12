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
        path: '/assets/images/flipclock/',
        digits: 2,
        width: 10,
        delay: 75
    };


    var methods = {
        init: function(opts) {
            var data = $.extend(true, {}, settings);
            data.state = [];
            data.num = 0;
            if (opts) {
                $.extend(data, opts);
            }
            for (var index = 0; index < data.digits; index++) {
                data.state.push(0);
            }
            this.data('flipclock', data);

            var paths = [];
            for (var state = 0; state < 10; state += 0.5) {
                var path = stateToPath(this, state);
                paths[paths.length] = path;
            }

            var initStr = this.html();
            var initNum = parseInt(initStr, 10);
            var error = '';
            if (isNaN(initNum)) {
                error = '$.flipclock.init();, ';
                error += 'but HTML value ' + initStr + ' is NaN';
                $.error(error);
            }
            if (initStr.length > data.digits) {
                error = '$.flipclock.init();, ' + data.digits + 'digits, ';
                error += 'but HTML value ' + initStr + ' requires more digits';
                $.error(error);
            }

            draw(this);
            set(this, initNum);
            return this;
        },

        set: function(num) {
            set(this, num);
            return this;
        }
    };


    $.fn.flipclock = function(method) {
        if (methods[method]) {
            method = methods[method];
            var args = Array.prototype.slice.call(arguments, 1);
            var retVal = method.apply(this, args);
            return retVal;
        } else {
            $.error("$.flipclock." + method + "() method doesn't exist");
            return undefined;
        }
    };


    function stateToPath(obj, state) {
        var transition = state != Math.floor(state);
        state = Math.floor(state);
        var file = String(state);
        if (transition) {
            nextState = (state + 1) % 10;
            file += '-' + nextState;
        }
        file += '.png';

        var data = obj.data('flipclock');
        var path = data.path + file;
        return path;
    }

    function draw(obj) {
        var data = obj.data('flipclock');
        var html = '';
        for (var index = 0; index < data.state.length; index++) {
            var state = data.state[index];
            var path = stateToPath(obj, state);
            var width = data.width;
            var imageTag = '<img src="' + path + '" width="' + width + '%" />';
            html = imageTag + html;
        }
        obj.html(html);
    }

    function redraw(obj) {
        var data = obj.data('flipclock');
        var images = obj.children().get().reverse();
        for (var index = 0; index < data.state.length; index++) {
            var state = data.state[index];
            var path = stateToPath(obj, state);
            $(images[index]).attr('src', path);
        }
    }

    function flip(obj) {
        var data = obj.data('flipclock');

        function f() {
            for (var exponent = 0; exponent < data.digits; exponent++) {
                var digit = data.num % Math.pow(10, exponent + 1);
                digit = Math.floor(digit / Math.pow(10, exponent));
                if (data.state[exponent] != digit) {
                    data.state[exponent] = (data.state[exponent] + 0.5) % 10;
                    redraw(obj);
                    var timeoutId = window.setTimeout(f, data.delay);
                    return;
                }
            }
        }

        f();
    }

    function set(obj, num) {
        var data = obj.data('flipclock');
        var max = Math.pow(10, data.digits) - 1;
        if (num > max) {
            var error = '$.flipclock.set(' + num + ');, ';
            error += 'but max value is ' + max;
            $.error(error);
        }

        data.num = num;
        flip(obj);
    }

})(jQuery);
