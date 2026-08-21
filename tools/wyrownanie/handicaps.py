"""BGA small-board handicap tables.

Source: https://www.britgo.org/handbook/hcap_9x9.pdf
        https://www.britgo.org/handbook/hcap_13x13.pdf

grade difference -> (handicap stones, komi to White)
Negative komi means White gives komi to Black, on top of the handicap stones.
"""

HCAP_9X9: dict[int, tuple[int, float]] = {
    0: (0, 6),
    1: (0, 4.5),
    2: (0, 3),
    3: (0, 1.5),
    4: (0, 0),
    5: (0, -2),
    6: (0, -4),
    7: (0, -6),
    8: (2, 6),
    9: (2, 4),
    10: (2, 2),
    11: (2, 0),
    12: (2, -2),
    13: (2, -4),
    14: (2, -6),
    15: (3, 6),
    16: (3, 4),
    17: (3, 2),
    18: (3, 0),
    19: (3, -2),
    20: (3, -4),
    21: (3, -6),
    22: (4, 6),
    23: (4, 4),
    24: (4, 2),
    25: (4, 0),
    26: (4, -2),
    27: (4, -4),
    28: (4, -6),
}

HCAP_13X13: dict[int, tuple[int, float]] = {
    0: (1, 6),
    1: (1, 2),
    2: (2, 8),
    3: (2, 4),
    4: (2, 0),
    5: (3, 6),
    6: (3, 2),
    7: (4, 8),
    8: (4, 4),
    9: (4, 0),
    10: (5, 6),
    11: (5, 2),
    12: (6, 8),
    13: (6, 4),
    14: (6, 0),
    15: (7, 6),
    16: (7, 2),
    17: (8, 8),
    18: (8, 4),
    19: (8, 0),
    20: (9, 6),
    21: (9, 2),
    22: (10, 8),
    23: (10, 4),
    24: (10, 0),
    25: (11, 6),
    26: (11, 2),
    27: (12, 8),
    28: (12, 4),
    29: (12, 0),
}

assert list(HCAP_9X9) == list(range(29)), "9x9 table must cover grade diffs 0..28 contiguously"
assert list(HCAP_13X13) == list(range(30)), "13x13 table must cover grade diffs 0..29 contiguously"
