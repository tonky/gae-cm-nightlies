var nightlies_branch = [];
var merged = [];
var branch = "gingerbread";
var device = "ace";
var url_nightlies = "/get_builds/"; //"http://download.cyanogenmod.com/"
var url_changelog = "/changelog/"
var getJsonCnt = 2;

Date.prototype.addHours = function(h){
    this.setHours(this.getHours()+h);
        return this;
}

String.prototype.cap_first = function(){
    return this.charAt(0).toUpperCase() + this.slice(1);
}

function parse_date(date_string) {
    // 2011-03-04 22:16:48.000000000
    if (!date_string) { return; };
    var pd = date_string.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/);

    return new Date(Date.UTC(pd[1], parseInt(pd[2]-1), pd[3], pd[4], pd[5], pd[6]));
}

function main() {
    var disableNightly = false;
    var nightly;
    var nd;
    var nightlies = nightlies_branch[branch];
    
    if (!disableNightly && nightlies && nightlies.length > 0) {
        nightly = nightlies.shift();
        nd = parse_date(nightly[1]);
    } else {
        disableNightly = true;
    }
    $('#merged_changes').empty();
    
    if (merged && (!nightly || (nd && merged[0] && (parse_date(merged[0].last_updated) > nd)))) {
        $('#merged_changes').append("<h3>to be included in next official nightly:</h3>");
    }

    //$('#merged_changes').append("<table class='tMerge' cellspacing='0' cellpadding='0'></table>");
    var prevKang = '';
    var new_table = true;
    merged.forEach(function(e, i, a) {
        var cd = parse_date(e.last_updated);
        
        if (!disableNightly && nightly) {
            while (cd < nd && (nightlies.length > 0)) {
                nightly_link = "<a href='http://download.cyanogenmod.com/?device="+ device +"&type=' name='"+ nightly[0] +"'>" + nightly[0] + "</a> ("+ nightly[2] +")"+
                    " <span class='nightly_date'>["+ nd +"]</span>";
                
                $('#merged_changes').append("<h4 class='"+ nightly[2].toLowerCase() +"'>" + nightly_link + "</h4>");
                new_table = true;
                
                nightly = nightlies.shift();
                nd = parse_date(nightly[1]);
            }
        }
        
        var kangId = e.subject.replace(/(.*)#dev:.*/,"$1");
        if (e.project=='KANG' && prevKang==('KANG' + kangId)) {
            // ignore
        } else {
            if (e.project=='KANG') {
                var fileName = "update-cm-"+ branch +"-UNOFFICIAL-"+ device +"-signed.zip"
                $('#merged_changes').append("<h4 class='"+ e.project.toLowerCase() +"'><a href='http://www.weik-net.com/cm7/"+ fileName +"'>" + fileName + "</a> ("+ e.project + ") <span class='nightly_date'>["+ cd +"]</span></h4>");
                new_table = true;
                prevKang = 'KANG' + kangId;
            } else {
                prevKang = '';
                if (new_table) {
                    $('#merged_changes').append("<table class='tMerge' cellspacing='0' cellpadding='0'></table>");
                    new_table = false;
                }
                $('#merged_changes > table:last').append("<tr><td class='tDate'>" + e.last_updated.substring(0, 16) +
                                            "</td><td class='tDesc'>" + e.subject.link("http://review.cyanogenmod.com/" + e.id) + 
                                            " - [" + e.project + "]</td></tr>");
            }
        }
    });

    $("tr:contains('ranslat')").addClass("translation");
    $("tr:contains('ocaliz')").addClass("translation");
    $("tr:contains('ussian')").addClass("translation");
    $("tr:contains('hinese')").addClass("translation");
    $("tr:contains('ortug')").addClass("translation");
    $("tr:contains('erman')").addClass("translation");
    $("tr:contains('wedish')").addClass("translation");
    $("tr:contains('typo')").addClass("translation");
    $("tr:contains('_" + device + "')").addClass("device");
    $("tr:contains('" + device + ":')").addClass("device");
    $("tr:contains('" + device.cap_first() + ":')").addClass("device");

    $("#device_links a[href$='"+device+"']").addClass("highlight");

    trans_visibility();
    trans_visibility('kang');
    trans_visibility('nightly');
    trans_visibility('rc');
    trans_visibility('stable');

    var loc = document.location.toString();

    if (loc.match('#')) {
      var anchor = '#' + loc.split('#')[1];
      location.href = anchor;
    }
    
    //alert("page loaded");
    //$('#info_text').append("Page loaded!");
}

function parse_nightlies (data) {
    if (data.results.length == 0) {
        //console.dir(data);
        $('#info_text').append("<h4 class='error'>Yahoo API is down, please try about five minutes later.</h4>");
    } else {
        nightlies_branch = [];
        nightlies_branch['ics'] = [];
        nightlies_branch['gingerbread'] = [];
        nightlies_branch['-unknown-'] = [];
        
        var nightly_html = data.replace(/[\r\n\t]+/mg, "");
        var re = new RegExp("^.*?Browse Files.*?<tbody>(.*)</tbody>.*$", "i");
        nightly_html = nightly_html.replace(re, "$1");
        re = new RegExp("<tr>.*?device="+ device +"(.*?)<\/tr>", "g");
        var nightlies_raw  = nightly_html.match(re);
        
        if (!nightlies_raw) {
            $('#info_text').append("<h4 class='error'>Device not found. Maybe you misspelled the device name in the url, or device isn't supported yet. This is still WIP, i'll add all CM supported devices eventually. Please click a link in the header.</h1>");
        } else {
            parsed_row = 0;
            nightlies_raw.forEach(function(e, i, a) {
                var parsed;
                parsed = e.match(/\b((?:nightly)|(?:RC)|(?:stable))\b.*?\b((update-cm-(\d)|cm_ace_full)[^<>\/]+?.zip)\b.*?\b(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\b/);
                /*
                  0: "..."
                  1: "RC"
                  2: "update-cm-7.2.0-RC1-ace-signed.zip"
                  3: "update-cm-7"
                  4: "7"
                  5: "2012-03-14 14:19:01"
                */
                
                if (parsed) {
                    //console.dir(parsed)
                    if (parsed[5]) {
                        parsed_row++;
                        if (parsed[4] == '9') {
                            nightlies_branch['ics'].push([parsed[2], parsed[5], parsed[1]]);
                        } else if (parsed[4] == '7' || parsed[3] == 'cm_ace_full') {
                            nightlies_branch['gingerbread'].push([parsed[2], parsed[5], parsed[1]]);
                        } else {
                            nightlies_branch['-unknown-'].push([parsed[2], parsed[5], parsed[1]]);
                        }
                    } else {
                        alert ("missing timestamp for '"+ parsed[2] +"' ("+ parsed[1] +") in: " + e);
                    }
                } else {
                    console.dir(e);
                    //alert ('nothing in: ' + e);
                }
            });
            
            if(parsed_row == 0) {
                $('#info_text').append("<h4 class='error'>Unable to parse nightlies, maybe cyanogenmod mirror is down. Please try a bit later.</h4>");
            }
        }
    }
    
	if (--getJsonCnt == 0) {
		main();
	}
}

function parse_nightlies_json (data) {
	nightlies_branch = data;
	if (--getJsonCnt == 0) {
		main();
	}
}

function parse_changelog(data) {
    merged = data;
	if (--getJsonCnt == 0) {
		main();
	}
}

function get_qs(key, default_) {
  if (default_==null) default_=""; 
  key = key.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
  var regex = new RegExp("[\\?&]"+key+"=([^&#]*)");
  var qs = regex.exec(window.location.href);
  if(qs == null)
    return default_;
  else
    return qs[1];
}

function trans_visibility(type) {
    var transObjName = type ? "#hide_type_"+type : "#hide_them";
    var transClass   = type ? "."+type : ".translation";
    var transCookie  = type ? "cm-nightlies-"+type : "cm-nightlies";
    if ($(transObjName).attr("checked")) {
        $(transClass).addClass("hidden");
        $.cookie(transCookie, 1);
    } else {
        $(transClass).removeClass("hidden");
        $.cookie(transCookie, null);
    }
}

function switch_branch(new_branch) {
    //alert ('switching to branch: '+new_branch);
    branch = new_branch;
    merged = [];
    getJsonCnt = 2;
    $('#info_text').empty();
    $('#merged_changes').html("Please wait, while loading changesets and nightlies...");
    $('#rss_ref').attr("href", "/rss?device="+device+"&branch="+branch);
    
    //$('#info_text').html("Loading builds from cyanogenmod server, please wait...");
    //$.get(url_nightlies, {device: device, type: ''}).success(parse_nightlies);
    $.get(url_changelog, {device: device, branch: branch}, parse_changelog);
    $.get(url_nightlies, {device: device, type: ''}, parse_nightlies_json);
}

$(document).ready(function () {
    qs_branch = get_qs("branch");
    qs_device = get_qs("device");
    
    if (qs_branch) {
        branch = qs_branch;
        $.cookie('cm-nightlies_branch', branch);
    } else if ($.cookie('cm-nightlies_branch')) {
        branch = $.cookie('cm-nightlies_branch');
    }
    
    if (qs_device) {
        device = qs_device;
    }
    if ($.cookie('cm-nightlies')        ) { $("#hide_them").attr("checked", true); }
    if ($.cookie('cm-nightlies-kang')   ) { $("#hide_type_kang").attr("checked", true); }
    if ($.cookie('cm-nightlies-nightly')) { $("#hide_type_nightly").attr("checked", true); }
    if ($.cookie('cm-nightlies-rc')     ) { $("#hide_type_rc").attr("checked", true); }
    if ($.cookie('cm-nightlies-stable') ) { $("#hide_type_stabel").attr("checked", true); }
    
    switch_branch(branch);
    
    $("#current_device").html(device);
    
    $(".select_branch").click(function() { switch_branch(this.value); });
    $(("#branch_"+branch)).attr('checked', true);
    
    $("#hide_them"        ).click(function() { trans_visibility(); });
    $("#hide_type_kang"   ).click(function() { trans_visibility('kang'); });
    $("#hide_type_nightly").click(function() { trans_visibility('nightly'); });
    $("#hide_type_rc"     ).click(function() { trans_visibility('rc'); });
    $("#hide_type_stable" ).click(function() { trans_visibility('stable'); });
    
    $("#announcement_header").click(function() { $("#announcement_text").toggleClass("hidden") ; });

    $(".manufacturer").click(function() {
        var was_hidden = $(this).next('ul').hasClass("hidden");
        $('ul').addClass("hidden");
        if (was_hidden) { $(this).next('ul').toggleClass("hidden"); }
    });
});
