var k = -1;
function genresult(th){
    k = pk = $(th).attr("pk");
    $("#res-modal h4").text($(th).attr("ftitle"));
    $("#res-modal #res-modal-dir").text($("#dir_num a").text());
    $("#hiddenresmodal").hide();
    $("[name='result-v']:checked").prop("checked", false);
    $("[name=kpol]").val("");
    $("[name=kkor]").val("");
    $("#res-modal").modal();
}

function updateresmodal(th){
    val = $(th).val();
    $("#hiddenresmodal").hide();
    if(val == "1"){
        $("#hiddenresmodal").show();
    }
}
var types_directory = {"0": "Отриц.", "1": "Пол.", "2": "Сомнит."};
function saveresmodal(){
    checked = $("[name='result-v']:checked");
    result = types_directory[checked.val()];
    if(checked.val() == "1"){
        result += " (Кпол {0}; Ккор {1})".f($("[name=kpol]").val(),$("[name=kkor]").val());
    }
    $("[data-pk="+k+"]").val(result);
}