UNIVERSE = [
    "HUT", "IREN", "NBIS", "WULF", "MARA", "APLD", "ORCL", "CRWV", "CRCL",
    "RKLB", "AAOI", "ONDS", "AXTI", "MXL", "FOTO", "LITE", "COHR", "APH",
    "FN", "MU", "SNDK",
]
PHOTONICS = ["FOTO", "LITE", "COHR", "APH", "FN", "AAOI", "AXTI"]
MINERS = ["HUT", "IREN", "WULF", "MARA"]
MEMORY = ["MU", "SNDK"]

EVENTS = {
    "MXL": {"date": "2026-07-23", "label": "Q2 2026 results after close"},
    "APLD": {"date": "2026-07-27", "label": "FY2026 Q4/full-year results after close"},
    "SNDK": {"date": "2026-08-05", "label": "FY2026 Q4/full-year results after close"},
}

BASELINES = {
    "FOTO": {"pullback": [20.80, 21.00], "tactical": 20.45, "structural": 19.90, "trigger": 21.30, "tp": [21.875, 22.475, 23.20]},
    "LITE": {"pullback": [830.0, 836.0], "tactical": 824.0, "structural": 799.80, "trigger": 845.10, "tp": [861.5, 887.5, 930.0]},
    "COHR": {"pullback": [315.50, 317.50], "tactical": 313.80, "structural": 309.50, "trigger": 320.60, "tp": [326.5, 335.5, 348.5]},
    "APH": {"pullback": [156.50, 157.20], "tactical": 155.20, "structural": 152.80, "trigger": 158.50, "tp": [162.0, 167.5, 175.0]},
    "FN": {"pullback": [523.0, 528.0], "tactical": 518.0, "structural": 505.40, "trigger": 534.20, "tp": [548.5, 570.0, 595.0]},
    "AAOI": {"pullback": [117.50, 119.00], "tactical": 114.50, "structural": 107.40, "trigger": 123.50, "tp": [129.0, 138.0, 149.5]},
    "ONDS": {"pullback": [7.55, 7.65], "tactical": 7.47, "structural": 7.22, "invalidation": 6.95, "trigger": 7.85, "tp": [8.225, 8.775, 9.375]},
    "AXTI": {"pullback": [54.80, 56.00], "tactical": 53.70, "structural": 51.20, "trigger": 57.60, "strong_trigger": 58.50, "tp": [60.5, 65.0, 71.5]},
    "MXL": {"pullback": [87.50, 89.00], "tactical": 85.80, "structural": 81.50, "trigger15": 91.30, "trigger": 92.60, "tp": [95.25, 99.75, 104.0]},
    "MU": {"pullback": [963.0, 970.0], "tactical": 948.0, "structural": 936.0, "trigger15": 979.0, "trigger": 988.0, "tp": [1000.0, 1045.0, 1097.5]},
    "SNDK": {"pullback": [1575.0, 1590.0], "tactical": 1548.0, "structural": 1515.0, "invalidation": 1504.0, "trigger15": 1619.0, "trigger": 1637.0, "tp": [1680.0, 1775.0, 1930.0]},
}
