let k = -1;
let dgroup = -1;
const dgroups = {0: "Oαβ (I)", 1: "A<sub>β</sub> (II)", 2: "A₂β (II)", 3: " Bα (III)", 4: "AB₀ (IV)", 5: "A₂B₀ (IV)"};
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
            $("[name='subgroup1']").first().prop("checked", true);
            val = $("[name='subgroup1']").first().val();
        }else if(val == "-3"){
            $("#hiddenresmodal-2").show();
            $("[name='subgroup2']").first().prop("checked", true);
            val = $("[name='subgroup2']").first().val();
        }
    }
    dgroup = parseInt(val);
}

function saveresmodal(){
    if(dgroup >= 0){
        $("[data-div-pk="+k+"]").html(dgroups[dgroup]);
        $("[data-pk="+k+"]").val(dgroups[dgroup]);
    }
}