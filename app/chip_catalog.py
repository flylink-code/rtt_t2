VENDOR_ORDER = [
    '意法半导体 (ST)',
    'Nordic',
    '恩智浦 (NXP)',
    '微芯 (Microchip)',
    '兆易创新 (GD)',
    '乐鑫 (Espressif)',
    '树莓派 (Raspberry Pi)',
    '其他',
]

DEFAULT_CHIP_CATALOG = {
    '意法半导体 (ST)': [
        'STM32F030C8',
        'STM32F051C8',
        'STM32F103C8',
        'STM32F103CB',
        'STM32F103RC',
        'STM32F103VE',
        'STM32F103ZE',
        'STM32F105RC',
        'STM32F401CC',
        'STM32F401RE',
        'STM32F405RG',
        'STM32F407VG',
        'STM32F411CE',
        'STM32F412RG',
        'STM32F429NI',
        'STM32F446RE',
        'STM32G031F6',
        'STM32G071RB',
        'STM32G431CB',
        'STM32H743II',
        'STM32H743XI',
        'STM32H750VB',
        'STM32H753II',
        'STM32L031F6',
        'STM32L412CB',
        'STM32L432KC',
        'STM32L476RG',
    ],
    'Nordic': [
        'nRF51822_xxAA',
        'nRF52832_xxAA',
        'nRF52832_xxAB',
        'nRF52833_xxAA',
        'nRF52840_xxAA',
        'nRF5340_xxAA_APP',
        'nRF9160_xxAA',
    ],
    '恩智浦 (NXP)': [
        'LPC1768',
        'LPC4088FET208',
        'MKL27Z64xxx4',
        'MK64FN1M0xxx12',
        'MIMXRT1052xxxxB',
        'MIMXRT1062xxxxA',
    ],
    '微芯 (Microchip)': [
        'ATSAMD21G18A',
        'ATSAM3X8E',
        'ATSAME70Q20',
    ],
    '兆易创新 (GD)': [
        'GD32F103C8',
        'GD32F103RB',
        'GD32F303VC',
        'GD32F405RG',
        'GD32F407VE',
    ],
    '乐鑫 (Espressif)': [
        'ESP32C3',
        'ESP32S3',
    ],
    '树莓派 (Raspberry Pi)': [
        'RP2040',
    ],
    '其他': [],
}

VENDOR_PREFIXES = (
    ('STM32', '意法半导体 (ST)'),
    ('nRF', 'Nordic'),
    ('LPC', '恩智浦 (NXP)'),
    ('MK', '恩智浦 (NXP)'),
    ('MIMX', '恩智浦 (NXP)'),
    ('ATSAM', '微芯 (Microchip)'),
    ('GD32', '兆易创新 (GD)'),
    ('ESP32', '乐鑫 (Espressif)'),
    ('RP2040', '树莓派 (Raspberry Pi)'),
)


def _clone_catalog(catalog):
    return {vendor: list(chips) for vendor, chips in catalog.items()}


def detect_chip_vendor(chip_name):
    upper = chip_name.upper()
    for prefix, vendor in VENDOR_PREFIXES:
        if upper.startswith(prefix.upper()):
            return vendor
    return '其他'


def get_chip_catalog(js_cfg):
    catalog = _clone_catalog(js_cfg.get('jk_chip_catalog') or DEFAULT_CHIP_CATALOG)
    for vendor in VENDOR_ORDER:
        catalog.setdefault(vendor, [])
    for vendor, chips in catalog.items():
        catalog[vendor] = sorted(dict.fromkeys(chips), key=str.casefold)
    return catalog


def iter_sorted_vendors(catalog):
    seen = set()
    for vendor in VENDOR_ORDER:
        if vendor in catalog:
            seen.add(vendor)
            yield vendor
    for vendor in sorted(catalog.keys(), key=str.casefold):
        if vendor not in seen:
            yield vendor


def catalog_chip_names(catalog):
    names = []
    for vendor in iter_sorted_vendors(catalog):
        names.extend(catalog.get(vendor, []))
    return names


def is_chip_header(text):
    return bool(text) and text in VENDOR_ORDER


def normalize_chip_config(config):
    catalog = _clone_catalog(DEFAULT_CHIP_CATALOG)
    user_catalog = config.get('jk_chip_catalog')
    if isinstance(user_catalog, dict):
        for vendor, chips in user_catalog.items():
            if not isinstance(chips, list):
                continue
            bucket = catalog.setdefault(vendor, [])
            for chip in chips:
                if isinstance(chip, str) and chip and chip not in bucket:
                    bucket.append(chip)

    selected = ''
    recent = []
    for chip in config.get('jk_chip', []):
        if not isinstance(chip, str) or not chip:
            continue
        if not selected:
            selected = chip
            continue
        if chip not in recent:
            recent.append(chip)

    for chip in [selected, *recent]:
        if not chip:
            continue
        vendor = detect_chip_vendor(chip)
        bucket = catalog.setdefault(vendor, [])
        if chip not in bucket:
            bucket.append(chip)

    for vendor in catalog:
        catalog[vendor] = sorted(dict.fromkeys(catalog[vendor]), key=str.casefold)

    config['jk_chip_catalog'] = catalog
    if selected:
        config['jk_chip'] = [selected] + [chip for chip in recent if chip != selected]
    elif config.get('jk_chip'):
        config['jk_chip'] = config['jk_chip'][:1]
    else:
        config['jk_chip'] = [catalog['意法半导体 (ST)'][0]]
    return config
