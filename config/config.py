from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import db

class Project(db.Model):
    branch = db.StringProperty()
    project = db.StringProperty()
    type = db.StringProperty()

class Change(db.Model):
    id = db.IntegerProperty()
    project = db.StringProperty()
    subject = db.StringProperty()
    last_updated = db.StringProperty()
    branch = db.StringProperty()
    
class User(db.Model):
    id    = db.IntegerProperty()
    email = db.StringProperty()
    url   = db.StringProperty()
    role  = db.IntegerProperty()


def qs_branch(rh, branch="gingerbread"):
    qd = rh.request.get('branch')
    if qd and qd in branch_device.keys():
        branch = qd
    return branch

def qs_device(rh, device="ace"):
    qd = rh.request.get('device')
    if qd:
        device = qd
    return device

def qs_kang_name(rh, kang="ace-awalon"):
    kang = rh.request.get('kang')
    return kang

def qs_kang_id(rh, kangId=""):
    kangId = rh.request.get('kangId')
    return kangId

# max query size
query_max = 450

# custom_rom = [aokp|cm]
custom_rom = 'aokp'
ga_tracking_id = ''
keywords = ''
if custom_rom == 'aokp':
    keywords = "Android Open Kang Project"
    gerrit_time_offset = 2
    ga_tracking_id = ''
    build_url = 'http://goo.im/devs/aokp/'
    build_dev_list_regex = r'^.*?<table.*?id.*?browse-tbl.*?>.*?File Name(.*?)</table>.*$'
    build_dev_regex = r'<a.*?href=["\'].*?/devs/aokp/([^"\']+)["\'].*?>'
    build_list_regex = r'^.*?<table.*?id.*?browse-tbl.*?>.*?File Name(.*?)</table>.*$'
    build_regex = r'<tr>(.*?)<\/tr>'
    gerrit_url = 'http://gerrit.sudoservers.com:8080/'
    branches = ['ics']
    types = ['unofficial', 'build', 'milestone']
elif custom_rom == 'cm':
    keywords = "Cyanogen, CyanogenMod, cyanogen mod"
    gerrit_time_offset = -2
    ga_tracking_id = ''
    build_url = 'http://download.cyanogenmod.com/?device='
    build_dev_list_regex = r'^.*?<ul.*?class.*?nav.*?>(.*)</ul>.*$'
    build_dev_regex = r'<li.*?id=["\']device_([^"\']+)["\'].*?>'
    build_list_regex = r'^.*?Browse Files.*?<tbody>(.*)</tbody>.*?$'
    build_regex = r'<tr>(.*?device=.*?)<\/tr>'
    gerrit_url = 'http://review.cyanogenmod.com/'
    branches = ['ics', 'gingerbread']
    types = ['unofficial', 'nightly', 'RC', 'stable']

use_kang_extension = True
#use_kang_extension = False

allow_db_clear = False

cache_device_timeout = 10800 # 3 hours
cache_build_timeout = 900 # 15 minutes
cache_rss_merge_timeout = 3600 # 1 hour

branch_device = {
    "gingerbread": ["ace", "galaxys2att"],
    "ics": ["tf101", "tf201", "galaxys2", "i777", "galaxysmtd", "toro"]
}

# http://de.wikipedia.org/wiki/CyanogenMod
# http://forum.aokp.co/page/supported_devices
device_title = {
    "a500": "Iconia Tab A500 (deprecated)",
    "ace": "Desire HD",
    "anzu": "Xperia Arc",
    "bravo": "Desire",
    "bravoc": "Desire (CDMA)",
    "buzz": "Wildfire",
    "c660": "Optimus Pro",
    "captivatemtd": "Captivate - AT&T",
    "cdma_droid2": "Droid 2 (CDMA)",
    "cdma_droid2we": "Droid 2 (CDMA) Global",
    "cdma_shadow": "Droid X (CDMA)",
    "chacha": "Status",
    "click": "Tattoo",
    "coconut": "Walkman",
    "cooper": "Galaxy Ace",
    "crespo": "Nexus S",
    "crespo4g": "Nexus S 4G",
    "desirec": "Eris",
    "doubleshot": "myTouch 4G Slide",
    "dream_sapphire": "Dream / Magic",
    "droid2": "Droid 2",
    "droid2we": "Droid 2 Global",
    "e510": "Optimus Hub",
    "e720": "Optimus Chic",
    "e730": "Optimus Sol",
    "e739": "myTouch",
    "encore": "Nook Color",
    "epicmtd": "Epic 4G (SPH-D700)",
    "es209ra": "Xperia X10",
    "espresso": "myTouch 3G Slide",
    "fascinatemtd": "Fascinate - Verizon",
    "galaxys2": "Galaxy S II",
    "galaxys2att": "Galaxy S II - AT&T",
    "galaxysbmtd": "Galaxy S (i9000B)",
    "galaxysmtd": "Galaxy S (i9000)",
    "galaxytab7c": "Galaxy Tab 7\" - Verizon",
    "glacier": "myTouch 4G / Panache",
    "harmony": "Viewsonic G Tablet (deprecated)",
    "hallon": "Xperia Neo",
    "heroc": "Hero (CDMA)",
    "i5500": "Galaxy 5",
    "i777": "Galaxy S II AT&T (SGH-I777)",
    "inc": "Incredible",
    "iyokan": "Xperia Pro",
    "liberty": "Aria",
    "jordan": "Defy",
    "maguro": "GSM Galaxy Nexus",
    "mango": "Xperia Mini Pro",
    "marvel": "Wildfire S",
    "mesmerizemtd": "Mesmerize",
    "mimmi": "Xperia X10 Mini Pro",
    "motus": "Backflip",
    "morrison": "Cliq",
    "olympus": "Atrix 4G",
    "otter": "Kindle Fire",
    "p1": "Galaxy Tab 7\"",
    "p1c": "Galaxy Tab 7\" (CDMA)",
    "p3": "Galaxy Tab 10.1v\" - 3G (P7100)",
    "p4": "Galaxy Tab 10.1\" - 3G (P7500)",
    "p4tmo": "Galaxy Tab 10.1\" - T-Mobile",
    "p4vzw": "Galaxy Tab 10.1\" - Verizon",
    "p4wifi": "Galaxy Tab 10.1\" - Wi-Fi",
    "p5": "Galaxy Tab 8.9\"",
    "p5wifi": "Galaxy Tab 8.9\" WiFi",
    "p500": "Optimus One",
    "p509": "Optimus T",
    "p920": "Optimus 3D",
    "p925": "Thrill 4G",
    "p930": "Optimus LTE",
    "p970": "Optimus Black",
    "p990": "Optimus 2X",
    "p999": "G2x",
    "passion": "Nexus One",
    "picasso": "Iconia Tab A500",
    "pyramid": "Sensation",
    "robyn": "Xperia X10 Mini",
    "saga": "Desire S",
    "satsuma": "Xperia Active",
    "shadow": "Droid X",
    "shakira": "Xperia X8",
    "sholes": "Droid",
    "showcasemtd": "Showcase",
    "smb_a1002": "Viewsonic G Tablet",
    "smultron": "Xperia Mini",
    "speedy": "Evo Shift 4G",
    "stingray": "Xoom - Verizon",
    "sunfire": "Photon",
    "supersonic": "EVO 4G",
    "tass": "Galaxy Mini",
    "tenderloin": "Touchpad",
    "tf101": "Eee Pad Transformer TF101",
    "tf201": "Eee Pad Transformer Prime TF201",
    "toro": "Galaxy Nexus (LTE)",
    "toroplus": "Galaxy Nexus - Sprint",
    "u8150": "Ideos",
    "u8220": "Pulse - T-Mobile",
    "urushi": "Xperia Ray",
    "vibrantmtd": "Vibrant - T-Mobile",
    "ville": "One S",
    "vision": "Desire Z",
    "vivo": "Incredible S",
    "vivow": "Incredible 2",
    "vzwtab": "Galaxy Tab 7\" - Verizon (deprecated)",
    "wingray": "Xoom - Wi-Fi",
    "zeppelin": "Cliq XT",
    "zeus": "Xperia Play R800i",
    "zeusc": "Xperia Play (CDMA) R800x",
}

# make sure "android_device_" repo goes first, as it's used in fronted to
# generate manufacturer categories
device_specific = {
    "a500": ["android_device_acer_a500", "android_device_acer_t20-common"],
    "picasso": ["android_device_acer_picasso", "android_device_acer_a500", "android_device_acer_t20-common"],
    "ace": ["android_device_htc_ace", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "anzu": ["android_device_semc_anzu", "android_device_semc_mogami-common", 
               "android_device_semc_msm7x30-common"],
    "blade": ["android_device_zte_blade", "zte-kernel-msm7x27"],
    "bravo": ["android_device_htc_bravo", "cm-kernel"],
    "bravoc": ["android_device_htc_bravoc", "cm-kernel"],
    "buzz": ["android_device_htc_buzz"],
    "c660": ["android_device_lge_c660"],
    "captivatemtd": ["android_device_samsung_captivatemtd", "android_device_samsung_aries-common",
                     "android_kernel_samsung_aries"],
    "cdma_shadow": ["android_device_motorola_shadow", "android_device_motorola_common"],
    "cdma_droid2": ["android_device_motorola_droid2", "android_device_motorola_common"],
    "cdma_droid2we": ["android_device_motorola_droid2we", "android_device_motorola_droid2", "android_device_motorola_common"],
    "chacha": ["android_device_htc_chacha"],
    "click": ["android_device_htc_click"],
    "cooper": ["android_device_samsung_cooper"],
    "coconut": ["android_device_semc_coconut"],
    "crespo": ["android_device_samsung_crespo", "samsung-kernel-crespo"],
    "crespo4g": ["android_device_samsung_crespo4g", "samsung-kernel-crespo"],
    "desirec": ["android_device_htc_desirec"],
    "doubleshot": ["android_device_htc_doubleshot"],
    "dream_sapphire": ["android_device_htc_dream_sapphire"],
    "droid2": ["android_device_motorola_droid2", "android_device_motorola_common"],
    "droid2we": ["android_device_motorola_droid2we", "android_device_motorola_droid2", "android_device_motorola_common"],
    "e510": ["android_device_lge_e510"],
    "e720": ["android_device_lge_e720"],
    "e730": ["android_device_lge_e730", "android_device_lge_victor-common", "lge-kernel-msm7x30"],
    "e739": ["android_device_lge_e739", "android_device_lge_victor-common", "lge-kernel-msm7x30"],
    "encore": ["android_device_bn_encore", "android_hardware_alsa_sound", "android_external_alsa-utils",
               "android_external_alsa-lib"],
    "epicmtd": ["android_device_samsung_epicmtd", "android_kernel_samsung_victory"],
    "es209ra": ["android_device_semc_es209ra", "android_device_semc_msm7x27-common"],
    "espresso": ["android_device_htc_espresso", "htc-kernel-msm7227"],
    "fascinatemtd": ["android_device_samsung_fascinatemtd", "android_device_samsung_aries-common",
                     "android_kernel_samsung_aries"],
    "galaxys2": ["android_device_samsung_galaxys2", "android_device_samsung_c1-common"],
    "galaxys2att": ["android_device_samsung_galaxys2att", "android_device_samsung_c1-common", "android_device_samsung_i777", "android_device_samsung_galaxys2"],
    "galaxysbmtd": ["android_device_samsung_galaxysbmtd", "android_device_samsung_aries-common"
                   "android_kernel_samsung_aries"],
    "galaxysmtd": ["android_device_samsung_galaxysmtd", "android_device_samsung_aries-common"
                   "android_kernel_samsung_aries"],
    "galaxytab7c": ["android_device_samsung_galaxytab7c"],
    "vzwtab": ["android_device_samsung_vzwtab"],
    "glacier": ["android_device_htc_glacier", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "harmony": ["android_device_malata_smb_harmony", "android_device_malata_smb_a1002"],
    "hallon": ["android_device_semc_hallon", "android_device_semc_mogami-common", 
               "android_device_semc_msm7x30-common"],
    "hero": ["android_device_htc_hero"],
    "heroc": ["android_device_htc_heroc"],
    "i5500": ["android_device_samsung_i5500"],
    "i777": ["android_device_samsung_galaxys2att", "android_device_samsung_c1-common", "android_device_samsung_i777", "android_device_samsung_galaxys2"],
    "iyokan": ["android_device_semc_iyokan"],
    "inc": ["android_device_htc_inc", "cm-kernel", "htc-kernel-incrediblec"],
    "legend": ["android_device_htc_legend", "htc-kernel-msm7227"],
    "liberty": ["android_device_htc_liberty", "htc-kernel-msm7227"],
    "maguro": ["android_device_samsung_maguro", "android_device_samsung_tuna"],
    "mango": ["android_device_semc_mango", "android_device_semc_mogami-common", 
               "android_device_semc_msm7x30-common"],
    "marvel": ["android_device_htc_marvel"],
    "mesmerizemtd": ["android_device_samsung_mesmerizemtd"],
    "mimmi": ["android_device_semc_mimmi", "android_device_semc_msm7x27-common"],
    "morrison": ["android_device_motorola_morrison"],
    "motus": ["android_device_motorola_motus"],
    "one": ["android_device_geeksphone_one"],
    "olympus": ["android_device_motorola_olympus"],
    "otter": ["android_device_amazon_otter"],
    "p1": ["android_device_samsung_p1", "android_device_samsung_p1-common", "android_kernel_samsung_p1"],
    "p1c": ["android_device_samsung_p1c", "android_device_samsung_p1-common", "android_kernel_samsung_galaxytab-cdma"],
    "p4": ["android_device_samsung_p4"],
    "p4tmo": ["android_device_samsung_p4tmo"],
    "p4vzw": ["android_device_samsung_p4vzw"],
    "p4wifi": ["android_device_samsung_p4wifi"],
    "p5": ["android_device_samsung_p5", "android_device_samsung_p5-common"],
    "p5wifi": ["android_device_samsung_p5wifi", "android_device_samsung_p5-common"],
    "p500" : ["android_device_lge_p500", "lge-kernel-msm7x27"],
    "p920": ["android_device_lge_p920"],
    "p925": ["android_device_lge_p925"],
    "p930": ["android_device_lge_p930"],
    "p970": ["android_device_lge_p970"],
    "p990": ["android_device_lge_p990", "android_device_lge_star-common", "lge-kernel-star"],
    "p999": ["android_device_lge_p999", "android_device_lge_star-common", "lge-kernel-star"],
    "passion": ["android_device_htc_passion", "android_device_htc_passion-common", "cm-kernel"],
    "pyramid": ["android_device_htc_pyramid", "android_vendor_htc_pyramid"],
    "robyn": ["android_device_semc_robyn", "android_device_semc_msm7x27-common"],
    "saga": ["android_device_htc_saga", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "satsuma": ["android_device_semc_satsuma"],
    "showcasemtd": ["android_device_samsung_showcasemtd"],
    "shadow": ["android_device_motorola_shadow"],
    "shakira": ["android_device_semc_shakira", "android_device_semc_msm7x27-common"],
    "sholes": ["android_device_motorola_sholes"],
    "smb_a1002": ["android_device_malata_smb_a1002", "android_device_malata_harmony"],
    "smdk4210": ["android_device_samsung_smdk4210", "android_kernel_samsung_smdk4210"],
    "smultron": ["android_device_semc_smultron", "android_device_semc_mogami-common", 
               "android_device_semc_msm7x30-common"],
    "stingray": ["android_device_moto_stingray"],
    "speedy": ["android_device_htc_speedy", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "sunfire": ["android_device_motorola_sunfire"],
    "supersonic": [ "android_device_htc_supersonic", "htc-kernel-supersonic", "cm-kernel"],
    "tass": ["android_device_samsung_tass"],
    "tenderloin": ["android_device_hp_tenderloin", "hp-kernel-tenderloin"],
    "tf101": ["android_device_asus_tf101", "device_asus_tf101", "vendor_proprietary_asus_tf101"],
    "tf201": ["android_device_asus_tf201", "device_asus_tf201"],
    "toro": ["android_device_samsung_toro", "android_device_samsung_tuna"],
    "toroplus": ["android_device_samsung_toroplus", "android_device_samsung_toro", "android_device_samsung_tuna"],
    "u8150": ["android_device_huawei_u8150"],
    "u8220": ["android_device_huawei_u8220"],
    "jordan": ["android_device_motorola_jordan"],
    "urushi": ["android_device_semc_urushi", "android_device_semc_mogami-common",
               "android_device_semc_msm7x30-common"],
    "vega": ["android_device_advent_vega"],
    "vibrantmtd": ["android_device_samsung_vibrantmtd", "android_device_samsung_aries-common",
                   "android_kernel_samsung_aries"],
    "ville": ["android_device_htc_ville"],
    "vision": ["android_device_htc_vision", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "vivo": ["android_device_htc_vivo", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "vivow": ["android_device_htc_vivow", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "v9": ["android_device_zte_v9"],
    "wingray": ["android_device_moto_wingray"],
    "z71": ["android_device_commtiva_z71"],
    "zeppelin": ["android_device_motorola_zeppelin"],
    "zero": ["android_device_geeksphone_zero", "geeksphone-kernel-zero"],
    "zeus": ["android_device_semc_zeus", "android_device_semc_zeus-common", 
               "android_device_semc_msm7x30-common"],
    "zeusc": ["android_device_semc_zeusc", "android_device_semc_zeus-common", 
               "android_device_semc_msm7x30-common"]
}
