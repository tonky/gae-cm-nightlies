var nightlies_branch = [];
var merged = [];
var url_nightlies = "/get_builds/";
var url_changelog = "/changelog/"
var getJsonCnt = 2;

Date.prototype.addHours = function(h){
	this.setHours(this.getHours()+h);
		return this;
}

String.prototype.cap_first = function(){
	return this.charAt(0).toUpperCase() + this.slice(1);
}

if (!Array.prototype.forEach) {
	Array.prototype.forEach = function( callback ) {
		for( var k=0; k<this .length; k++ ) {
			callback( this[ k ], k, this);
		}
	}
}

function pad(n, len) {
   
    s = n.toString();
    if (s.length < len) {
        s = ('0000000000' + s).slice(-len);
    }

    return s;
   
}

function parse_date(date_string) {
	// 2011-03-04 22:16:48.000000000
	var pd = date_string.match(/(\d{4})-(\d{1,2})-(\d{1,2})[\sT](\d{1,2}):(\d{1,2}):(\d{1,2})/);
	return new Date(Date.UTC(pd[1], parseInt(pd[2]-1), pd[3], pd[4], pd[5], pd[6]));
}

function format_date(t, utc) {
	if (typeof t === "string") t = parse_date (t);
	if (!(t instanceof Date)) return "undefined: "+t;
	t = utc ?
		[t.getUTCFullYear(),t.getUTCMonth(),t.getUTCDate(),t.getUTCHours(),t.getUTCMinutes(),t.getUTCSeconds()] :
		[t.getFullYear(),t.getMonth(),t.getDate(),t.getHours(),t.getMinutes(),t.getSeconds()];
	return t[0] + "-" + pad(t[1]+1, 2) + "-" + pad(t[2], 2) + " " + pad(t[3], 2) + ":" + pad(t[4], 2);
}

function main() {
	var disableNightly = false;
	var nightly;
	var nd;
	var nightlies;
	
	if (nightlies_branch && nightlies_branch[branch]) {
		nightlies = nightlies_branch[branch];
	} else {
		$('#info_text').html("<h4 class='error'>Download server is down or there are no builds for your device and/or branch ("+ device +", "+ branch +")</h4>");
		$('#info_text').css("visibility", "visible");
	}
	
	if (!disableNightly && nightlies && nightlies.length > 0) {
		nightly = nightlies.shift();
		nd = parse_date(nightly[3]);
	} else if (disableNightly) {
		$('#info_text').html("There are no builds for your device and or branch ("+ device +", "+ branch +")");
		$('#info_text').css("visibility", "visible");
	} else {
		disableNightly = true;
	}
	$('#merged_changes').empty();
	if (merged && (!nightly || (nd && merged[0] && merged[0].project != 'KANG' && (parse_date(merged[0].last_updated_offset) > nd)))) {
		$('#merged_changes').append("<h3>to be included in next nightly:</h3>");
	}
	
	var prevKang = '';
	var new_table = true;
	merged.forEach(function(e, i, a) {
		var cd = parse_date(e.last_updated_offset);
		var cd_utc = parse_date(e.last_updated_utc);
		var build_no = e.subject.match(/^(?:build|milestone) (\d+)$/);
		
		if (!disableNightly && nightly) {
			while ((custom_rom == 'aokp' && build_no && nightly[0].indexOf('-'+build_no[1]+'.zip') != -1) 
			  || cd < nd) {
				nightly_link = "<a href='"+ build_url + device +"' name='"+ nightly[0] +"' onclick='return gaOutLink(this, \"Download build\", this.href);'>" + nightly[0] + "</a> ("+ nightly[2] +")"+
				  " <span class='nightly_date' title='UTC: "+ nightly[3].replace("T", " ") +"'>["+ nd.toString() +"]</span>";
				
				$('#merged_changes').append("<h4 class='"+ nightly[2].toLowerCase() +"'>" + nightly_link + "</h4>");
				new_table = true;
				
				if (nightlies.length > 0) {
					nightly = nightlies.shift();
					nd = parse_date(nightly[3]);
				} else {
					nightly = null;
					break;
				}
			}
		}
		
		var kangId = e.subject.replace(/(.*)#dev:.*/,"$1");
		if (!(e.project=='KANG' && prevKang==('KANG' + kangId))) {
			if (e.project=='KANG') {
				var fileName = "update-"+ custom_rom +"-"+ branch +"-UNOFFICIAL-"+ device +"-signed.zip"
				$('#merged_changes').append("<h4 class='unofficial'><a href='http://www.weik-net.com/"+ custom_rom +"/"+ fileName +"' onclick='return gaOutLink(this, \"Download build (unofficial)\", this.href);'>" + fileName +
				  "</a> ("+ e.project + ") <span class='nightly_date' title='"+ e.last_updated_utc.substring(0, 16) +"'>["+ cd_utc.toString() +"]</span></h4>");
				new_table = true;
				prevKang = 'KANG' + kangId;
			} else {
				prevKang = '';
				if (new_table) {
					$('#merged_changes').append("<table class='tMerge' cellspacing='0' cellpadding='0'></table>");
					new_table = false;
				}
				$('#merged_changes > table:last').append("<tr><td class='tDate' title='UTC: "+ e.last_updated_utc.substring(0, 16) +"'>" + format_date(cd_utc) +
				  "</td><td class='tDesc'>" + e.subject.link(gerrit_url + e.id) + 
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
	types.forEach(function(t, i, a) {
		var type = t.toLowerCase();
		trans_visibility(type);
	});
	
	var loc = document.location.toString();
	if (loc.match('#')) {
		var anchor = '#' + loc.split('#')[1];
		location.href = anchor;
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
	var transCookie  = type ? custom_rom+"-nightlies-"+type : custom_rom+"-nightlies";
	if ($(transObjName).attr("checked")) {
		$(transClass).addClass("hidden");
		$.cookie(transCookie, 1);
	} else {
		$(transClass).removeClass("hidden");
		$.cookie(transCookie, null);
	}
}

function load_data(new_branch) {
	branch = new_branch;
	merged = [];
	getJsonCnt = 2;
	$('#info_text').empty();
	$('#info_text').css("visibility", "hidden");
	$('#merged_changes').html("Please wait, while loading changesets and nightlies...");
	$('#rss_ref').attr("href", "/rss/"+ device +"/"+ branch);
	
	$.get(url_changelog, {device: device, branch: branch}, parse_changelog);
	$.get(url_nightlies, {device: device, type: ''}, parse_nightlies_json);
}

var nav_active_prev;
$(document).ready(function () {
	qs_branch = get_qs("branch");
	qs_device = get_qs("device");
	
	if (qs_branch) {
		branch = qs_branch;
		$.cookie(custom_rom+'-nightlies_branch', branch);
	} else if ($.cookie(custom_rom+'-nightlies_branch')) {
		branch = $.cookie(custom_rom+'-nightlies_branch');
	}
	
	if (qs_device) {
		device = qs_device;
	}
	if ($.cookie(custom_rom+'-nightlies')        ) { $("#hide_them").attr("checked", true); }
	if ($.cookie(custom_rom+'-nightlies-kang')   ) { $("#hide_type_kang").attr("checked", true); }
	if ($.cookie(custom_rom+'-nightlies-nightly')) { $("#hide_type_nightly").attr("checked", true); }
	if ($.cookie(custom_rom+'-nightlies-rc')     ) { $("#hide_type_rc").attr("checked", true); }
	if ($.cookie(custom_rom+'-nightlies-stable') ) { $("#hide_type_stabel").attr("checked", true); }
	
	load_data(branch);
	
	$(".select_branch").click(function() { load_data(this.value); });
	$(("#branch_"+branch)).attr('checked', true);
	
	$("#hide_them"        ).click(function() { trans_visibility(); });
	types.forEach(function(t, i, a) {
		var type = t.toLowerCase();
		$("#hide_type_"+type).click(function() { trans_visibility(type); });
	});
	
	$("#announcement_header").click(function() { $("#announcement_text").toggleClass("hidden") ; });
	
	$(".manufacturer").click(function() {
		var nav_item = $(this);
		var nav_menu = $(this).next('ul');
		if (nav_active_prev) {
			nav_active_prev.toggleClass("nav_active");
			nav_active_prev.next('ul').toggleClass("hidden");
			if (nav_active_prev.attr('id') == nav_item.attr('id')) {
				nav_active_prev = null;
				return;
			}
		}
		
		var height = nav_item.outerHeight();
		var pos = nav_item.position();
		nav_item.toggleClass("nav_active");
		nav_menu.toggleClass("hidden");
		nav_menu.css({
				left: pos.left + "px",
				top: (pos.top + height) + "px"
			});
		nav_active_prev = nav_item;
	});
});
