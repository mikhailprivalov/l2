let k = -1;
let group = -1;
const groups = {0: "Oαβ (I)", 1: "A₁ (II)", 2: "A₂β (II)", 3: " Bα (III)", 4: "AB (IV)", 5: "A₂B₀ (IV)"};
function genresult(th){
    k = pk = $(th).attr("pk");
    $("#res-modal h4").text($(th).attr("ftitle"));
    $("#res-modal #res-modal-dir").text($("#dir_num a").text());
    $("#hiddenresmodal-1, #hiddenresmodal-2").hide();
    $("#hiddenresmodal").hide();
    $("[name='groupb']:checked").prop("checked", false);
    $("[name='subgroup1']:checked").prop("checked", false);
    $("[name='subgroup2']:checked").prop("checked", false);
    $("#res-modal").modal();
}

function updateresmodal(th){
    val = $(th).val();
    if($(th).attr("name") == "groupb") {
        $("#hiddenresmodal-1, #hiddenresmodal-2").hide();
        $("[name='subgroup1']:checked").prop("checked", false);
        $("[name='subgroup2']:checked").prop("checked", false);
        if (val == "-2") {
            $("#hiddenresmodal-1").show();
        }else if(val == "-3"){
            $("#hiddenresmodal-2").show();
        }
    }
    group = parseInt(val);
}

function saveresmodal(){
    if(group >= 0){
        $("[data-pk="+k+"]").val(groups[group]);
    }
}