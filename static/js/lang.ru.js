$.assocArraySize = function (obj) {
    // http://stackoverflow.com/a/6700/11236
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};

var lang;
lang = {
    fraction: ['фркация', 'фракции', 'фракций'],

    client_not_found: "Данные введены неверно",

    table_researches_header: "<h4>Исследования:</h4>",
    table_researches_not_found: "Ничего не найдено",
    table_researches_click_for_show_all: "{0} {1}. Кликните для разворачивания или сворачивания <i class='glyphicon glyphicon-hand-up'></i>",

    table_researches_preview_header: "<tr><th>Лаборатория</th><th>Виды исследования</th><th>Управление</th></tr>",
    table_researches_preview_none: "<tr><td>Ничего не добавлено</td><td></td><td></td></tr>",
    table_researches_preview_realy_delete: "Удалить исследования в лаборатории {0} из направления?",
    clear_direction: "Очистить направление?"

};
var ref_types = {'a': {'show': false, 's': "Все"}, 'pmp': {'show': true, 's': "любой ключ"}}
var loading_tpl = '<span class="isloading-wrapper %wrapper%">%text% <i class="%class% glyphicon glyphicon-refresh"></i></span>';

var normal_keys = {"a": "Все", "pmp": "Постменопауза"}
var g = {"м": "m", "ж": "f"}
function age_range(str) {
    this.downer = str.split("-")[0];
    this.upper = str.split("-")[1];
    this.getkey = function () {
        return this.downer + "-" + this.upper;
    }
}

var getN = function (key) {
    console.log(key)
    if (normal_keys[key]) {
        return normal_keys[key];
    }
    return key + " лет";
}

var getNorms = function (sex, age, ref, units) {
    html_ret = "<table class='table table-bordered'>";
    age_ref = {};
    $.each(ref[g[sex.toLowerCase()]], function (k, v) {
        if (normal_keys[k]) {
            age_ref[normal_keys[k]] = ref[g[sex.toLowerCase()]][k];
        }
    });
    max = new age_range("0-0");
    if ($.assocArraySize(age_ref) > 0) {
        $.each(age_ref, function (k, v) {
            html_ret += "<tr><td class='col-md-7'>{0}</td><td>{1}</td></tr>".f(k, v);
        });
    }
    if (ref[g[sex.toLowerCase()]].length > $.assocArraySize(age_ref) || $.assocArraySize(age_ref) == 0) {
        maxage = "";
        $.each(ref[g[sex.toLowerCase()]], function (k, v) {
            range = new age_range(k);
            if (age >= range.downer && age <= range.upper) {
                maxage = "<tr><td class='col-md-7'>{0}</td><td>{1}</td></tr>".f(getN(k), v);
            }
            if (max.downer < range.downer && max.upper < range.upper)
                max = range;
        });
        if (max.upper < age && maxage == "") {
            maxage = "<tr><td class='col-md-7'>{0}</td><td>{1}</td></tr>".f(max.getkey(), ref[g[sex.toLowerCase()]][max.getkey()]);
        }
        html_ret += maxage;
    }
    html_ret += "</table>";
    return html_ret;
}
