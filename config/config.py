from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import db


class Change(db.Model):
    id = db.IntegerProperty()
    project = db.StringProperty()
    subject = db.StringProperty()
    last_updated = db.StringProperty()


def qs_device(rh, device="ace"):
    qd = rh.request.get('device')

    if qd and qd in device_specific.keys():
        device = qd

    return device

device_specific = {
    "ace": ["android_device_htc_ace", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "blade": ["android_device_zte_blade"],
    "bravo": ["android_device_htc_bravo", "cm-kernel"],
    "bravoc": ["android_device_htc_bravoc", "cm-kernel"],
    "buzz": ["android_device_htc_buzz"],
    "captivatemtd": ["android_device_samsung_captivatemtd", "android_device_samsung_aries-common"],
    "click": ["android_device_htc_click"],
    "crespo": ["android_device_samsung_crespo", "samsung-kernel-crespo"],
    "crespo4g": ["android_device_samsung_crespo4g", "samsung-kernel-crespo"],
    "encore": ["android_device_bn_encore", "android_hardware_alsa_sound", "android_external_alsa-utils",
               "android_external_alsa-lib"],
    "espresso": ["android_device_htc_espresso", "htc-kernel-msm7227"],
    "galaxysmtd": ["android_device_samsung_galaxysmtd", "android_device_samsung_aries-common"],
    "glacier": ["android_device_htc_glacier", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "smb_a1002": ["android_device_malata_smb_a1002"],
    "hero": ["android_device_htc_hero"],
    "heroc": ["android_device_htc_heroc"],
    "inc": ["android_device_htc_inc", "cm-kernel", "htc-kernel-incrediblec"],
    "legend": ["android_device_htc_legend", "htc-kernel-msm7227"],
    "liberty": ["android_device_htc_liberty", "htc-kernel-msm7227"],
    # "mecha": ["android_device_htc_mecha"],
    "morrison": ["android_device_motorola_morrison"],
    "one": ["android_device_geeksphone_one"],
    "p990": ["android_device_lge_p990", "android_device_lge_star-common", "lge-kernel-star"],
    "p999": ["android_device_lge_p999", "android_device_lge_star-common", "lge-kernel-star"],
    "passion": ["android_device_htc_passion", "android_device_htc_passion-common", "cm-kernel"],
    "sholes": ["android_device_motorola_sholes"],
    "cdma_shadow": ["android_device_motorola_shadow"],
    "speedy": ["android_device_htc_speedy", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "supersonic": ["htc-kernel-supersonic", "cm-kernel", "android_device_htc_supersonic"],
    "vega": ["android_device_advent_vega"],
    "vibrantmtd": ["android_device_samsung_vibrantmtd", "android_device_samsung_aries-common"],
    "vision": ["android_device_htc_vision", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "vivo": ["android_device_htc_vivo", "android_device_htc_msm7x30-common", "htc-kernel-msm7x30"],
    "z71": ["android_device_commtiva_z71"],
    "zeppelin": ["android_device_motorola_zeppelin"],
    "zero": ["android_device_geeksphone_zero", "geeksphone-kernel-zero"]
}
