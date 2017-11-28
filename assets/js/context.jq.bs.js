(function ($) {

    $.contextMenu = function (settings) {
        $("body").on("contextmenu", settings.elementSelector, function (e) {
                // return native menu if pressing control
                if (e.ctrlKey) return;

                //open menu
                var $menu = $(settings.menuSelector)
                    .data("invokedOn", $(e.target))
                    .show()
                    .css({
                        position: "absolute",
                        left: getMenuPosition(e.clientX, 'width', 'scrollLeft'),
                        top: getMenuPosition(e.clientY, 'height', 'scrollTop')
                    })
                    .off('click')
                    .on('click', 'a:not(.noclick)', function (e) {
                        $menu.hide();

                        var $invokedOn = $menu.data("invokedOn");
                        var $selectedMenu = $(e.target);

                        settings.menuSelected.call(this, $invokedOn, $selectedMenu);
                    });

                return false;
            });
        $('body').click(function (e) {
            if(!$(e.target).hasClass("noclick") && !$(e.target).parents().hasClass("noclick"))
            $(settings.menuSelector).hide();
        });

        function getMenuPosition(mouse, direction, scrollDir) {
            var win = $(window)[direction](),
                scroll = $(window)[scrollDir](),
                menu = $(settings.menuSelector)[direction](),
                position = mouse + scroll;

            // opening menu would pass the side of the page
            if (mouse + menu > win && menu < mouse)
                position -= menu;

            return position;
        }

    };


    $.contextMenu2 = function (settings) {
        $("body").on("contextmenu", settings.elementSelector, function (e) {
            // return native menu if pressing control
            if (e.ctrlKey) return;

            var $menu = $(settings.menuSelector)
                .data("invokedOn", $(e.target))
                .show()
                .css({
                    position: "absolute",
                    left: getMenuPosition(e.clientX, 'width', 'scrollLeft'),
                    top: getMenuPosition(e.clientY, 'height', 'scrollTop')
                })
                .off('click')
                .on('click', 'a:not(.noclick)', function (e) {
                    $menu.hide();

                    var $invokedOn = $menu.data("invokedOn");
                    var $selectedMenu = $(e.target);

                    settings.menuSelected.call(this, $invokedOn, $selectedMenu);
                });

                settings.onopen.call(this, $menu.data("invokedOn"), $menu);
                return false;
            });
        $('body').click(function (e) {
            if(!$(e.target).hasClass("noclick") && !$(e.target).parents().hasClass("noclick"))
            $(settings.menuSelector).hide();
        });

        function getMenuPosition(mouse, direction, scrollDir) {
            var win = $(window)[direction](),
                scroll = $(window)[scrollDir](),
                menu = $(settings.menuSelector)[direction](),
                position = mouse + scroll;

            // opening menu would pass the side of the page
            if (mouse + menu > win && menu < mouse)
                position -= menu;

            return position;
        }

    };
})(jQuery);