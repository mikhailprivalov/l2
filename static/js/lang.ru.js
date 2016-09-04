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

    table_researches_header: "<h6><b>Исследования:</b></h6>",
    table_researches_not_found: "Ничего не найдено",
    table_researches_click_for_show_all: "{0} {1}. Кликните для разворачивания или сворачивания <i class='glyphicon glyphicon-hand-up'></i>",

    table_researches_preview_header: "<tr><th>Лаборатория</th><th>Виды исследований</th><th>Управление</th></tr>",
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
};

var clients_bases = {poli: "Поликлиника", stat: "Стационар", poli_stom: "Поликлиника-стоматология"};


var fraction_types = {
    "-1": ["Без вариантов"],
    "0": ["Отрицательный", "Положительный"],
    "1": ["Отрицательный", "Положительный", "Сомнительный"],
    "2": ["Отрицательный", "Положительный", "Неопределенный"],
    "3": ["Rh (+) <br/>положительный", "rh (-) <br/>отрицательный", "Rh (+-) <br/>слабополож-ый"],
    "4": ["Проз.", "Сл/мутн.", "Мутн."],
    "5": ["+", "++", "+++"],
    "6": ["5", "6", "7", "8", "9"],
    "7": ["Един.", "1-3", "5-8", "10-15", "20-30", "Больш. к-во"],
    "8": ["Един.", "3-5", "8-10", "Больш. к-во"],
    "9": ["Отсутствует", "Един.", "1-10", "15-20", "Больш. к-во"],
    "10": ["с/желт", "н/желт", "бурый", "розов."],
    "11": ["1000", "1005", "1010", "1015", "1020", "1025", "1030"],
    "12": ["50,0", "100,0"],
    "13": ["Отрицательно"],
    "14": ["Отсутствует"],
    "15": ["S", "R", "I"],
    "16": ["Микрофлора не обнаружена",
        "Шигеллы и сальмонеллы не выделены",
        "St.aureus не обнаружен",
        "Условно-патогенная микрофлора и грибы рода Candida не обнаружены",
        "Corynebacterium diphtheriae не обнаружена",
        "Грам (+) кокки - 10<sup>2</sup> КОЕ/мл. Исключить контаминацию!",
        "Грам (-) палки - 10<sup>2</sup> КОЕ/мл. Исключить контаминацию!",
        "Грам (+) кокки - 10<sup>2</sup> КОЕ/мл",
        "Грам (-) палки - 10<sup>2</sup> КОЕ/мл"
    ],
    "17": ["< 50"]
};

var material_types = {
    "-1": ["Без вариантов"],
    "0": ["Мокрота"],
    "1": ["Зев"],
    "2": ["Нос"],
    "3": ["Желчь"],
    "4": ["Моча"],
    "5": ["Мокрота", "Бронх/см"],
    "6": ["Цервикал", "Влагал"],
    "7": ["С/пуатул", "Язва", "Десн/кар", "Раневое"],
    "8": ["Ухо"],
    "9": ["Кал"],
    "10": ["Кон/глаз"],
    "11": ["Рот"],
    "12": ["Лев/ухо", "Прав/ухо"],
    "13": ["Лев/глаз", "Прав/глаз"]
};
