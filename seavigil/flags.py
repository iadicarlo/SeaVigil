"""Country + flag-emoji helpers for vessel identity.

AIS gives a flag via the MMSI's first 3 digits (the ITU Maritime Identification
Digits, MID); GFW SAR gives an ISO3 code. This maps both to an ISO2 country code and
a flag emoji. Unknown codes return ("", "") rather than guessing.
"""

from __future__ import annotations

# ITU MID (first 3 MMSI digits) -> ISO2. Broad coverage of common maritime flags.
_MID_ISO2 = {
    201: "AL", 202: "AD", 203: "AT", 204: "PT", 205: "BE", 206: "BY", 207: "BG",
    208: "VA", 209: "CY", 210: "CY", 211: "DE", 212: "CY", 213: "GE", 214: "MD",
    215: "MT", 218: "DE", 219: "DK", 220: "DK", 224: "ES", 225: "ES", 226: "FR",
    227: "FR", 228: "FR", 229: "MT", 230: "FI", 231: "FO", 232: "GB", 233: "GB",
    234: "GB", 235: "GB", 236: "GI", 237: "GR", 238: "HR", 239: "GR", 240: "GR",
    241: "GR", 242: "MA", 243: "HU", 244: "NL", 245: "NL", 246: "NL", 247: "IT",
    248: "MT", 249: "MT", 250: "IE", 251: "IS", 252: "LI", 253: "LU", 254: "MC",
    255: "PT", 256: "MT", 257: "NO", 258: "NO", 259: "NO", 261: "PL", 262: "ME",
    263: "PT", 264: "RO", 265: "SE", 266: "SE", 267: "SK", 268: "SM", 269: "CH",
    270: "CZ", 271: "TR", 272: "UA", 273: "RU", 274: "MK", 275: "LV", 276: "EE",
    277: "LT", 278: "SI", 279: "RS",
    301: "AI", 303: "US", 304: "AG", 305: "AG", 306: "CW", 307: "AW", 308: "BS",
    309: "BS", 310: "BM", 311: "BS", 312: "BZ", 314: "BB", 316: "CA", 319: "KY",
    321: "CR", 323: "CU", 325: "DM", 327: "DO", 329: "GP", 330: "GD", 331: "GL",
    332: "GT", 334: "HN", 336: "HT", 338: "US", 339: "JM", 341: "KN", 343: "LC",
    345: "MX", 347: "MQ", 348: "MS", 350: "NI", 351: "PA", 352: "PA", 353: "PA",
    354: "PA", 355: "PA", 356: "PA", 357: "PA", 358: "PR", 359: "SV", 361: "PM",
    362: "TT", 364: "TC", 366: "US", 367: "US", 368: "US", 369: "US", 370: "PA",
    371: "PA", 372: "PA", 373: "PA", 374: "PA", 375: "VC", 376: "VC", 377: "VC",
    378: "VG", 379: "VI",
    401: "AF", 403: "SA", 405: "BD", 408: "BH", 410: "BT", 412: "CN", 413: "CN",
    414: "CN", 416: "TW", 417: "LK", 419: "IN", 422: "IR", 423: "AZ", 425: "IQ",
    428: "IL", 431: "JP", 432: "JP", 434: "TM", 436: "KZ", 437: "UZ", 438: "JO",
    440: "KR", 441: "KR", 443: "PS", 445: "KP", 447: "KW", 450: "LB", 451: "KG",
    453: "MO", 455: "MV", 457: "MN", 459: "NP", 461: "OM", 463: "PK", 466: "QA",
    468: "SY", 470: "AE", 471: "AE", 472: "TJ", 473: "YE", 475: "YE", 477: "HK",
    478: "BA",
    501: "TF", 503: "AU", 506: "MM", 508: "BN", 510: "FM", 511: "PW", 512: "NZ",
    514: "KH", 515: "KH", 516: "CX", 518: "CK", 520: "FJ", 523: "CC", 525: "ID",
    529: "KI", 531: "LA", 533: "MY", 536: "MP", 538: "MH", 540: "NC", 542: "NU",
    544: "NR", 546: "PF", 548: "PH", 553: "PG", 555: "PN", 557: "SB", 559: "AS",
    561: "WS", 563: "SG", 564: "SG", 565: "SG", 566: "SG", 567: "TH", 570: "TO",
    572: "TV", 574: "VN", 576: "VU", 577: "VU", 578: "WF",
    601: "ZA", 603: "AO", 605: "DZ", 609: "BI", 610: "BJ", 611: "BW", 612: "CF",
    613: "CM", 615: "CG", 616: "KM", 617: "CV", 619: "CI", 620: "KM", 621: "DJ",
    622: "EG", 624: "ET", 625: "ER", 626: "GA", 627: "GH", 629: "GM", 630: "GW",
    631: "GQ", 632: "GN", 633: "BF", 634: "KE", 636: "LR", 637: "LR", 638: "SS",
    642: "LY", 644: "LS", 645: "MU", 647: "MG", 649: "ML", 650: "MZ", 654: "MR",
    655: "MW", 656: "NE", 657: "NG", 659: "NA", 661: "RW", 662: "SD", 663: "SN",
    664: "SC", 666: "SO", 667: "SL", 668: "ST", 669: "SZ", 670: "TD", 671: "TG",
    672: "TN", 674: "TZ", 675: "UG", 676: "CD", 677: "TZ", 678: "ZM", 679: "ZW",
    701: "AR", 710: "BR", 720: "BO", 725: "CL", 730: "CO", 735: "EC", 740: "FK",
    750: "GY", 755: "PY", 760: "PE", 765: "SR", 770: "UY", 775: "VE",
}

# Complete ISO 3166-1 alpha-3 -> alpha-2 (every assigned country code), so a flag-state
# tally never splits a nation across an unmapped ISO3 and a mapped ISO2.
_ISO3_ISO2 = {
    "ABW": "AW", "AFG": "AF", "AGO": "AO", "AIA": "AI", "ALA": "AX", "ALB": "AL", "AND": "AD", "ARE": "AE", "ARG": "AR",
    "ARM": "AM", "ASM": "AS", "ATA": "AQ", "ATF": "TF", "ATG": "AG", "AUS": "AU", "AUT": "AT", "AZE": "AZ", "BDI": "BI",
    "BEL": "BE", "BEN": "BJ", "BES": "BQ", "BFA": "BF", "BGD": "BD", "BGR": "BG", "BHR": "BH", "BHS": "BS", "BIH": "BA",
    "BLM": "BL", "BLR": "BY", "BLZ": "BZ", "BMU": "BM", "BOL": "BO", "BRA": "BR", "BRB": "BB", "BRN": "BN", "BTN": "BT",
    "BVT": "BV", "BWA": "BW", "CAF": "CF", "CAN": "CA", "CCK": "CC", "CHE": "CH", "CHL": "CL", "CHN": "CN", "CIV": "CI",
    "CMR": "CM", "COD": "CD", "COG": "CG", "COK": "CK", "COL": "CO", "COM": "KM", "CPV": "CV", "CRI": "CR", "CUB": "CU",
    "CUW": "CW", "CXR": "CX", "CYM": "KY", "CYP": "CY", "CZE": "CZ", "DEU": "DE", "DJI": "DJ", "DMA": "DM", "DNK": "DK",
    "DOM": "DO", "DZA": "DZ", "ECU": "EC", "EGY": "EG", "ERI": "ER", "ESH": "EH", "ESP": "ES", "EST": "EE", "ETH": "ET",
    "FIN": "FI", "FJI": "FJ", "FLK": "FK", "FRA": "FR", "FRO": "FO", "FSM": "FM", "GAB": "GA", "GBR": "GB", "GEO": "GE",
    "GGY": "GG", "GHA": "GH", "GIB": "GI", "GIN": "GN", "GLP": "GP", "GMB": "GM", "GNB": "GW", "GNQ": "GQ", "GRC": "GR",
    "GRD": "GD", "GRL": "GL", "GTM": "GT", "GUF": "GF", "GUM": "GU", "GUY": "GY", "HKG": "HK", "HMD": "HM", "HND": "HN",
    "HRV": "HR", "HTI": "HT", "HUN": "HU", "IDN": "ID", "IMN": "IM", "IND": "IN", "IOT": "IO", "IRL": "IE", "IRN": "IR",
    "IRQ": "IQ", "ISL": "IS", "ISR": "IL", "ITA": "IT", "JAM": "JM", "JEY": "JE", "JOR": "JO", "JPN": "JP", "KAZ": "KZ",
    "KEN": "KE", "KGZ": "KG", "KHM": "KH", "KIR": "KI", "KNA": "KN", "KOR": "KR", "KWT": "KW", "LAO": "LA", "LBN": "LB",
    "LBR": "LR", "LBY": "LY", "LCA": "LC", "LIE": "LI", "LKA": "LK", "LSO": "LS", "LTU": "LT", "LUX": "LU", "LVA": "LV",
    "MAC": "MO", "MAF": "MF", "MAR": "MA", "MCO": "MC", "MDA": "MD", "MDG": "MG", "MDV": "MV", "MEX": "MX", "MHL": "MH",
    "MKD": "MK", "MLI": "ML", "MLT": "MT", "MMR": "MM", "MNE": "ME", "MNG": "MN", "MNP": "MP", "MOZ": "MZ", "MRT": "MR",
    "MSR": "MS", "MTQ": "MQ", "MUS": "MU", "MWI": "MW", "MYS": "MY", "MYT": "YT", "NAM": "NA", "NCL": "NC", "NER": "NE",
    "NFK": "NF", "NGA": "NG", "NIC": "NI", "NIU": "NU", "NLD": "NL", "NOR": "NO", "NPL": "NP", "NRU": "NR", "NZL": "NZ",
    "OMN": "OM", "PAK": "PK", "PAN": "PA", "PCN": "PN", "PER": "PE", "PHL": "PH", "PLW": "PW", "PNG": "PG", "POL": "PL",
    "PRI": "PR", "PRK": "KP", "PRT": "PT", "PRY": "PY", "PSE": "PS", "PYF": "PF", "QAT": "QA", "REU": "RE", "ROU": "RO",
    "RUS": "RU", "RWA": "RW", "SAU": "SA", "SDN": "SD", "SEN": "SN", "SGP": "SG", "SGS": "GS", "SHN": "SH", "SJM": "SJ",
    "SLB": "SB", "SLE": "SL", "SLV": "SV", "SMR": "SM", "SOM": "SO", "SPM": "PM", "SRB": "RS", "SSD": "SS", "STP": "ST",
    "SUR": "SR", "SVK": "SK", "SVN": "SI", "SWE": "SE", "SWZ": "SZ", "SXM": "SX", "SYC": "SC", "SYR": "SY", "TCA": "TC",
    "TCD": "TD", "TGO": "TG", "THA": "TH", "TJK": "TJ", "TKL": "TK", "TKM": "TM", "TLS": "TL", "TON": "TO", "TTO": "TT",
    "TUN": "TN", "TUR": "TR", "TUV": "TV", "TWN": "TW", "TZA": "TZ", "UGA": "UG", "UKR": "UA", "UMI": "UM", "URY": "UY",
    "USA": "US", "UZB": "UZ", "VAT": "VA", "VCT": "VC", "VEN": "VE", "VGB": "VG", "VIR": "VI", "VNM": "VN", "VUT": "VU",
    "WLF": "WF", "WSM": "WS", "YEM": "YE", "ZAF": "ZA", "ZMB": "ZM", "ZWE": "ZW",
}


def flag_emoji(iso2: str | None) -> str:
    if not iso2 or len(iso2) != 2 or not iso2.isalpha():
        return ""
    base = 0x1F1E6
    return chr(base + ord(iso2[0].upper()) - 65) + chr(base + ord(iso2[1].upper()) - 65)


def from_mmsi(mmsi) -> tuple[str, str]:
    """(iso2, emoji) from an MMSI's MID; ('', '') if unknown."""
    try:
        mid = int(str(int(float(mmsi)))[:3])
    except (TypeError, ValueError):
        return "", ""
    iso2 = _MID_ISO2.get(mid, "")
    return iso2, flag_emoji(iso2)


def from_iso3(iso3: str | None) -> tuple[str, str]:
    """(iso2, emoji) from an ISO3 code; ('', '') if unknown."""
    if not iso3:
        return "", ""
    iso2 = _ISO3_ISO2.get(str(iso3).upper(), "")
    return iso2, flag_emoji(iso2)


def to_iso2(code: str | None) -> str:
    """Normalize an ISO2 or ISO3 country code to ISO2 ('' if unknown).

    Sources disagree: GFW SAR + the disabling CSV give ISO3 (CHN, ESP), while
    MMSI-derived flags are ISO2 (RU, KR). Collapse both so a flag-state tally does
    not split one country across two codes.
    """
    if not code:
        return ""
    c = str(code).strip().upper()
    if len(c) == 2:
        return c if c.isalpha() else ""
    if len(c) == 3:
        return from_iso3(c)[0]
    return ""


def emoji_for(code: str | None) -> str:
    """Flag emoji from an ISO2 (2 letters) or ISO3 (3 letters) country code."""
    if not code:
        return ""
    c = str(code).strip()
    if len(c) == 2:
        return flag_emoji(c)
    if len(c) == 3:
        return from_iso3(c)[1]
    return ""
