(function ($) {
    "use strict";
    $.fn.inputClear = function (options) {
        var settings = $.extend({
            'exclude': '.no-clear',
        }, options);
        return this.each(function () {
            // add private event handler to avoid conflict
            $(this).not(settings.exclude)
                .unbind("clear-focus")
                .bind("clear-focus", (
                    function () {
                        if ($(this).data("clear-button")) return;
                        var x = $("<a class='clear-text' style='cursor:pointer;color:#888;'><i class='icon-remove'></i></a>");
                        $(x).data("text-box", this);
                        $(x).mouseover(function () {
                            $(this).addClass("over");
                        }).mouseleave(function () {
                            $(this).removeClass("over");
                        });
                        $(this).data("clear-button", x);
                        $(x).css({
                            "position": "absolute",
                            "left": ($(this).position().right),
                            "top": $(this).position().top,
                            "margin": "3px 0px 0px -20px"
                        });
                        $(this).after(x);
                        //$(this));
                    }))
                .unbind("clear-blur").bind("clear-blur", (
                    function (e) {
                        var x = $(this).data("clear-button");
                        if (x) {
                            if ($(x).hasClass("over")) {
                                $(x).removeClass("over");
                                $(x).hide().remove();
                                $(this).val("");
                                $(this).removeData("clear-button");
                                var txt = this;
                                e.stopPropagation();
                                e.stopImmediatePropagation();
                                setTimeout($.proxy(function () {
                                    $(this).trigger("focus");
                                }, txt), 50);
                                return false;
                            }
                        }
                        if (x && !$(x).hasClass("over")) {
                            $(this).removeData("clear-button");
                            $(x).remove();
                        }
                    }));
            // add private event to the focus/unfocus events as branches
            $(this).on("focus", function () {
                $(this).trigger("clear-focus");
            }).on("blur", function () {
                $(this).trigger("clear-blur");
            });
        });
    };
})(jQuery);