var nums = {};
var groups = {};

/**
 * @return {boolean}
 */
function IsJsonString(str) {
    try {
        JSON.parse(str);
    } catch (e) {
        return false;
    }
    return true;
}

function dready() {
    groups = {};
    $.each($(".row-container"), function (k, v) {
        fpk = $(v).attr("container-pk");
        if (IsJsonString($(`.json-result[data-pk=${fpk}]`).val())) {
            groups[fpk] = JSON.parse($(`.json-result[data-pk=${fpk}]`).val());
        }
        else {
            add_group_v(fpk);

        }
    });
    gui_sync();
}

function add_group_k(fpk, k, title) {
    if (!groups[fpk])
        groups[fpk] = {counter: 0, rows: {}};

    if (!groups[fpk].rows[k])
        groups[fpk].rows[k] = {counter: 0, rows: {}, title: title};
    groups[fpk].counter = Math.max(groups[fpk].counter, k);
}

function add_group_v(fpk) {
    if (!groups[fpk])
        groups[fpk] = {counter: 0, rows: {}};

    groups[fpk].counter++;
    groups[fpk].rows[groups[fpk].counter] = {counter: 0, rows: {}, title: ""};

    $.each(loaded_fractions[fpk].options, function (kk, vv) {
        add_subgroup_v(fpk, groups[fpk].counter, vv, "");
    });
}

function add_group(fpk) {
    restore_values();
    add_group_v(fpk);
    gui_sync();
}

function add_subgroup_k(fpk, group, k, title, value) {
    if (!groups[fpk].rows[group].rows[k])
        groups[fpk].rows[group].rows[k] = {title: title, value: value};
    groups[fpk].rows[group].counter = Math.max(groups[fpk].counter, k);

}
function add_subgroup_v(fpk, group, title, value) {
    groups[fpk].rows[group].counter++;
    groups[fpk].rows[group].rows[groups[fpk].rows[group].counter] = {title: title, value: value};
}
function add_subgroup(fpk, group) {
    restore_values();
    add_subgroup_v(fpk, group, "", "");
    gui_sync();
}

function add_row(btn) {
    fpk = parseInt($(btn).attr("fraction-pk"));

    if (!nums[fpk]) nums[fpk] = 0;

    nums[fpk]++;
    $("[container-pk={0}]".f(fpk)).append(`<tr num="${nums[fpk]}" fpk="${fpk}"><td><input type=\'text\' class=\'form-control\' name=\'dynamic-title-${fpk}\' /></td><td><input type=\'text\' class=\'form-control\' name=\'dynamic-value-${fpk}\' num="${fnum}" /></td><td><button class="btn btn-danger" onclick="remove_row(${fpk},${nums[fpk]});">-</button></td></tr>`);
}

function remove_row(gpk) {
    $(`.group-tr[data-group-key='${gpk}']`).remove();
    restore_values();
}

var hidden_gpk = [];
function gui_sync() {
    if (Object.keys(groups).length == 0) return;
    $('.result-enter').typeahead('destroy');

    $.each(groups, function (k, v) {
        tps = fraction_types[loaded_fractions[k].type + ""];
        t = Math.max(Math.floor(12 / (tps.length + 1)), 1);
        tmp_radios = `<div class='col-md-${t} rd-cont'><input type="radio" value="null" class="subval defval" checked /><label>нич.</label></div>`;
        $.each(tps, function (k, v) {
            tmp_radios += `<div class='col-md-${t} rd-cont'><input type="radio" class="subval" value="${v}" /><label>${v}</label></div>`;
        });
        tmp_radios = `<div class="row rd-row">${tmp_radios}</div>`;

        cont = $(`[container-pk='${k}'] tbody`);
        var ft = $.map(fraction_types[loaded_fractions[k].unit], function (item) {
            return {value: item};
        });
        var typeVals = new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            identify: function (obj) {
                return obj.value;
            },
            local: ft
        });

        function typeValsDefaults(q, sync) {
            if (q === '') {
                sync(typeVals.get(fraction_types[loaded_fractions[k].unit]));
            }
            else {
                typeVals.search(q, sync);
            }
        }

        cont.html("");
        vvi = 0;
        $.each(v.rows, function (kk, vv) {
            cont.append(`<tr class="group-tr" data-group-key="${kk}"><td><input class="form-control typeahead result-enter group-title" value="${vv.title}" type="text" maxlength="63"/><br/><button style="margin: 3px;float: right;padding: 2px" class="btn btn-sm btn-blue-nb hide-vals-btn" onclick="hide_vals(${kk}, this); return false;">Свернуть значения</button><button style="margin: 3px;padding: 2px" class="btn btn-sm btn-primary-rm" onclick="remove_row(${kk}); return false;">Удалить</button></td><td><table class="group-rows table table-responsive"></table></td></tr>`);

            $.each(vv.rows, function (kkk, vvv) {
                vvi++;
                //$(`[data-group-key="${kk}"] .group-rows`, cont).append(`<tr class="subgroup-tr" data-subgroup-key="${kkk}"><td class="col-md-6"><input class="form-control subgroup-title" type="text" value="${vvv.title}" maxlength="63"/></td><td class="col-md-6"><input class="form-control typeahead result-enter subgroup-value" value="${vvv.value}" type="text" maxlength="63"/></td></tr>`)

                if (vvv.value == "") vvv.value = "null";
                $(`[data-group-key="${kk}"] .group-rows`, cont).append(`<tr class="subgroup-tr" data-subgroup-key="${kkk}"><td class="col-md-5"><input class="form-control subgroup-title" type="text" value="${vvv.title}" maxlength="63"/><input class="form-control subgroup-value" value="${vvv.value}" type="hidden" maxlength="63"/></td><td class="col-md-7 radio-cont">${tmp_radios}</td></tr>`);

                $(`[data-group-key="${kk}"] [data-subgroup-key="${kkk}"] .radio-cont input[type=radio]`, cont).attr("name", `val-${k}-${kk}-${kkk}-${vvi}`);
                vi = 0;
                $.each($(`[data-group-key="${kk}"] [data-subgroup-key="${kkk}"] .radio-cont .rd-cont`), function (ku, vu) {
                    nid = `val-${k}-${kk}-${kkk}-${vvi}_${vi}`;
                    $("input[type=radio]", vu).attr("id", nid);
                    $("label", vu).attr("for", nid);
                    vi++;
                });

                $(`[data-group-key="${kk}"] [name='val-${k}-${kk}-${kkk}-${vvi}']`).removeAttr("checked");
                $(`[data-group-key="${kk}"] [name='val-${k}-${kk}-${kkk}-${vvi}']`).prop("checked", false);
                $(`[data-group-key="${kk}"] [name='val-${k}-${kk}-${kkk}-${vvi}'][type=radio][value='${vvv.value}']`, cont).prop("checked", true);

            });
            $(`[data-group-key="${kk}"] .group-rows`, cont).append(`<tr class="reset-subgroup-tr"><td colspan="2" style="text-align: right"><button class="btn btn-default btn-blue2-nb" onclick="reset_v(${kk}); return false;">Сброс</button></td></tr>`);
            $d = $(`[data-group-key="${kk}"] .group-title`);
            $val = $d.val();
            $d.typeahead({
                minLength: 0,
                highlight: true,
                limit: 40
            }, {
                name: 'typeval',
                display: 'value',
                limit: 40,
                source: typeValsDefaults
            });
            $d.typeahead('val', $val);
            //$(`[data-group-key="${kk}"] .group-rows`, cont).append(`<tr><td colspan="2"><button class="btn btn-default btn-blue2-nb" onclick="add_subgroup(${k}, ${kk}); return false;">Добавить</button></td></tr>`)

            var lci = hidden_gpk.indexOf(parseInt(kk));
            if (lci >= 0) {
                $(`[data-group-key="${kk}"] .hide-vals-btn`).click();
            }
            remove_fa(hidden_gpk, kk);
        });
        cont.append(`<tr><td colspan="2"><button class="btn btn-default btn-blue2-nb" onclick="add_group(${k}); return false;">Добавить</button></td></tr>`);
    });
}

function reset_v(kk) {
    $(`[data-group-key="${kk}"] input[type=radio]`).prop("checked", false);
    $(`[data-group-key="${kk}"] .defval`).prop("checked", true);
}

function restore_values() {
    groups = {};
    $.each($(".row-container"), function (k, v) {
        fpk = parseInt($(v).attr("container-pk"));
        $.each($('.group-tr', v), function (kk, vv) {
            gpk = parseInt($(vv).attr("data-group-key"));
            add_group_k(fpk, gpk, $(".group-title:not(.tt-hint)", vv).val());
            $.each($(".subgroup-tr", vv), function (kkk, vvv) {
                spk = parseInt($(vvv).attr("data-subgroup-key"));
                add_subgroup_k(fpk, gpk, spk, $(".subgroup-title:not(.tt-hint)", vvv).val(), $(".subval:checked", vvv).val());
            });
        });
        $(`[data-pk=${fpk}]`).val(JSON.stringify(groups[fpk]));
    });
}

function hide_vals(gpk, th) {
    $s = $(`[data-group-key='${gpk}'] .group-rows`);
    $s.toggle();
    if (!$s.is(":visible")) {
        $(th).text("Показать значения");
        remove_fa(hidden_gpk, gpk);
        hidden_gpk.push(gpk);
    }
    else {
        $(th).text("Свернуть значения");
        remove_fa(hidden_gpk, gpk);
    }
    console.log(hidden_gpk);
}

function remove_fa(arr, item) {
    for (var i = arr.length; i--;) {
        if (arr[i] === item) {
            arr.splice(i, 1);
        }
    }
}

function exec_formula(th) {
    formula = {fraction: parseInt($(th).attr("pk"))};
    formula.body = $(`input[data-pk=${formula.fraction}]`).attr("data-formula");
    formula.necessary = formula.body.match(/\{(\d{1,})\}/g);
    formula.necessary_complex = formula.body.match(/\{\d{1,}\|\d{1,}\}/g);
    formula.tmp = formula.body;
    formula.str = formula.body;

    if (formula.necessary != null) {
        for (i = 0; i < formula.necessary.length; i++) {
            formula.necessary[i] = formula.necessary[i].replace(/\{|\}/g, "");
            fval = 0;
            try {
                fval = parseFloat($(`[data-pk="${formula.necessary[i]}"]`).val().trim().replace(",", "."));
            }
            catch (e) {
            }
            if (!fval) {
                fval = 0;
            }
            formula.tmp = formula.tmp.replace(`{${formula.necessary[i]}}`, fval);
        }
    }

    sl();
    function perform_complex(k) {
        formula.necessary_complex[k] = formula.necessary_complex[k].split("|");

        formula.necessary_complex[k][0] = parseInt(formula.necessary_complex[k][0].replace(/\{|\}/g, ""));
        formula.necessary_complex[k][1] = parseInt(formula.necessary_complex[k][1].replace(/\{|\}/g, ""));

        fval = 0;
        iss_obj = $.grep(dir_data.issledovaniya, function (e) {
            return e.research_pk == formula.necessary_complex[k][0];
        })[0];
        if (iss_obj) {
            formula.str = formula.str.replace(`{${formula.necessary_complex[k][0]}|${formula.necessary_complex[k][1]}}`, iss_obj.title);
            fraction = formula.necessary_complex[k][1];
            $.ajax({url: "/results/get", data: {iss_id: iss_obj.pk}}).done(function (data) {
                fval = "0";
                if (fraction in data.results) {
                    g = data.results[fraction] + "";
                    fval = g.replace(",", ".").trim();
                    if (!is_lnum(fval)) {
                        fval = "0";
                    }
                }
                formula.tmp = formula.tmp.replace(`{${iss_obj.research_pk}|${fraction}}`, fval);
                if (k == formula.necessary_complex.length - 1) {
                    ready_formula(formula);
                }
                else {
                    perform_complex(k + 1);
                }
            });
        }
        else {
            formula.tmp = formula.tmp.replace(`{${formula.necessary_complex[k][0]}|${formula.necessary_complex[k][1]}}`, fval);
            if (k == formula.necessary_complex.length - 1) {
                ready_formula(formula);
            }
            else {
                perform_complex(k + 1);
            }
        }
    }

    if (formula.necessary_complex != null) {
        perform_complex(0);
    } else {
        ready_formula(formula);
    }

}

function ready_formula(formula) {
    v = new Function("return " + formula.tmp + ";")();
    if (is_float(v)) {
        v = Math.round(parseFloat(v) * 10) / 10;
    }
    console.log(v);
    if(!isNaN(v) && isFinite(v)) {
        $(`input[data-pk=${formula.fraction}]`).val(v);
        hl();
        $.amaran({
            'theme': 'awesome ok',
            'content': {
                title: 'Результат посчитан',
                message: "Формула:<br/>" + formula.str + "<br/>Процесс подсчета:<br/>" + formula.tmp,
                info: '',
                icon: 'fa fa-exclamation'
            },
            'position': 'bottom right',
            delay: 10000
        });
    } else if (!isFinite(v) && !isNaN(v)) {
        hl();
        $.amaran({
            'theme': 'awesome wrn',
            closeButton: true,
            sticky: true,
            'content': {
                title: 'Ошибка',
                message: "Произошло деление на ноль.<br/>Формула:<br/>" + formula.str + "<br/>Процесс подсчета:<br/>" + formula.tmp,
                info: '',
                icon: 'fa fa-exclamation'
            },
            'position': 'bottom right'
        });
    }
    else {
        $(`input[data-pk=${formula.fraction}]`).val("Ошибка");
        hl();
        $.amaran({
            'theme': 'awesome wrn',
            closeButton: true,
            sticky: true,
            'content': {
                title: 'Ошибка',
                message: "Возможно, не все необходимые исследования были назначены",
                info: '',
                icon: 'fa fa-exclamation'
            },
            'position': 'bottom right'
        });
    }
}

function is_float(str) {
    return /^\-?\d+\.\d+$/.test(str);
}

function is_n(str) {
    return /^\-?\d+$/.test(str);
}

function is_lnum(str) {
    return /^\-?\d+(\.\d+)?$/.test(str);
}