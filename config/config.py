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
    "ace": ["android_device_htc_ace", "htc-kernel-msm7x30"],
    "blade": ["android_device_zte_blade"],
    "bravo": ["cm-kernel", "android_device_htc_bravo"],
    "bravoc": ["cm-kernel", "android_device_htc_bravoc"],
    "buzz": ["android_device_htc_buzz"],
    "click": ["android_device_htc_click"],
    "crespo": ["android_device_samsung_crespo"],
    "encore": ["android_device_bn_encore", "android_hardware_alsa_sound", 
               "android_external_alsa-utils", "android_external_alsa-lib"],
    "espresso": ["android_device_htc_espresso"],
    "glacier": ["android_device_htc_glacier", "htc-kernel-msm7x30"],
    "harmony": ["android_device_harmony"],
    "hero": ["android_device_htc_hero"],
    "inc": ["htc-kernel-incrediblec", "android_device_htc_inc"],
    "legend": ["android_device_htc_legend"],
    "liberty": ["android_device_htc_liberty"],
    "one": ["android_device_geeksphone_one"],
    "heroc": ["android_device_htc_heroc"],
    "passion": ["android_device_htc_passion",
                "android_device_htc_passion-common"],
    "sholes": ["android_device_motorola_sholes"],
    "speedy": ["android_device_htc_speedy"],
    "supersonic": ["htc-kernel-supersonic", "android_device_htc_supersonic"],
    "vega": ["android_device_advent_vega"],
    "vision": ["android_device_htc_vision", "htc-kernel-msm7x30"],
    "z71": ["android_device_commtiva_z71"],
    "zeppelin": ["android_device_motorola_zeppelin"],
    "zero": ["android_device_geeksphone_zero"]
}
