# Pilot performance by metadata

All scores are percentages pooled over clips within each group. L = Whisper large-v3; T = turbo; P = Parakeet v3.

The official columns use upstream normalization and compound-aware alignment. The stem-weighted columns use stem normalization and weighted token alignment. These are separate policies; differences between those columns do not isolate one change.

The CSV/JSON contain all eight metrics, edit-cost components and denominator masses. Groups overlap across fields. Subgroup results are exploratory, with four meeting series and recurring speakers; no significance claims.

## meeting_type

| Value | Clips | Words | Minutes | Series | Speakers | Official L | Official T | Official P | Stem-weighted L | Stem-weighted T | Stem-weighted P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonscenario | 323 | 3161 | 16.75 | 1 | 4 | 19.84 | 20.53 | 13.35 | 19.86 | 20.51 | 13.33 |
| scenario | 477 | 5423 | 33.17 | 3 | 12 | 11.12 | 11.54 | 6.80 | 10.90 | 11.29 | 6.80 |

## meeting_series_id

| Value | Clips | Words | Minutes | Series | Speakers | Official L | Official T | Official P | Stem-weighted L | Stem-weighted T | Stem-weighted P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EN2002 | 323 | 3161 | 16.75 | 1 | 4 | 19.84 | 20.53 | 13.35 | 19.86 | 20.51 | 13.33 |
| ES2004 | 170 | 2280 | 12.47 | 1 | 4 | 10.39 | 10.83 | 5.96 | 10.16 | 10.73 | 6.18 |
| IS1009 | 127 | 1602 | 9.54 | 1 | 4 | 12.11 | 12.42 | 7.18 | 11.71 | 12.01 | 6.94 |
| TS3003 | 180 | 1541 | 11.16 | 1 | 4 | 11.16 | 11.68 | 7.66 | 11.13 | 11.36 | 7.55 |

## meeting_id

| Value | Clips | Words | Minutes | Series | Speakers | Official L | Official T | Official P | Stem-weighted L | Stem-weighted T | Stem-weighted P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EN2002a | 81 | 745 | 4.21 | 1 | 4 | 18.79 | 19.33 | 13.69 | 18.30 | 18.73 | 13.32 |
| EN2002b | 60 | 609 | 3.11 | 1 | 4 | 21.02 | 21.35 | 14.12 | 20.90 | 21.02 | 13.83 |
| EN2002c | 97 | 1073 | 5.21 | 1 | 3 | 21.06 | 20.69 | 12.67 | 21.75 | 21.39 | 13.40 |
| EN2002d | 85 | 734 | 4.21 | 1 | 4 | 18.12 | 20.84 | 13.35 | 17.82 | 20.64 | 12.82 |
| ES2004a | 22 | 300 | 1.61 | 1 | 4 | 9.67 | 10.67 | 5.67 | 8.76 | 9.71 | 5.19 |
| ES2004b | 44 | 696 | 3.71 | 1 | 4 | 9.05 | 9.91 | 5.89 | 8.78 | 9.62 | 5.96 |
| ES2004c | 48 | 696 | 3.95 | 1 | 4 | 11.78 | 11.21 | 4.60 | 10.88 | 10.97 | 4.71 |
| ES2004d | 56 | 588 | 3.20 | 1 | 4 | 10.71 | 11.56 | 7.82 | 11.65 | 12.31 | 8.73 |
| IS1009a | 17 | 153 | 1.06 | 1 | 4 | 15.03 | 16.34 | 12.42 | 18.57 | 19.80 | 14.59 |
| IS1009b | 36 | 539 | 2.96 | 1 | 4 | 11.50 | 12.43 | 4.27 | 11.22 | 11.91 | 4.48 |
| IS1009c | 33 | 422 | 2.64 | 1 | 4 | 11.37 | 10.90 | 5.92 | 10.56 | 10.05 | 5.33 |
| IS1009d | 41 | 488 | 2.87 | 1 | 4 | 12.50 | 12.50 | 9.84 | 11.13 | 11.39 | 8.71 |
| TS3003a | 28 | 224 | 1.69 | 1 | 3 | 8.48 | 8.48 | 5.80 | 9.87 | 9.87 | 7.31 |
| TS3003b | 46 | 455 | 3.17 | 1 | 4 | 11.65 | 11.87 | 9.01 | 11.31 | 11.07 | 8.95 |
| TS3003c | 44 | 401 | 3.09 | 1 | 4 | 11.22 | 10.97 | 6.23 | 10.72 | 10.40 | 5.70 |
| TS3003d | 62 | 461 | 3.22 | 1 | 4 | 11.93 | 13.67 | 8.46 | 11.88 | 13.14 | 7.82 |

## speaker_id

| Value | Clips | Words | Minutes | Series | Speakers | Official L | Official T | Official P | Stem-weighted L | Stem-weighted T | Stem-weighted P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FEE013 | 64 | 698 | 4.26 | 1 | 1 | 7.88 | 7.74 | 5.59 | 7.43 | 7.56 | 5.54 |
| FEE016 | 42 | 572 | 2.63 | 1 | 1 | 9.44 | 8.22 | 8.04 | 8.80 | 7.59 | 8.21 |
| FEO070 | 33 | 241 | 1.83 | 1 | 1 | 25.31 | 25.73 | 19.09 | 25.13 | 25.13 | 18.65 |
| FEO072 | 80 | 820 | 4.47 | 1 | 1 | 15.98 | 18.90 | 6.22 | 16.40 | 19.31 | 6.14 |
| FIE088 | 48 | 546 | 3.61 | 1 | 1 | 9.71 | 10.26 | 5.86 | 10.48 | 10.91 | 6.42 |
| FIO084 | 28 | 408 | 2.26 | 1 | 1 | 16.18 | 16.42 | 8.58 | 14.78 | 15.23 | 8.32 |
| FIO087 | 18 | 167 | 0.96 | 1 | 1 | 16.77 | 17.96 | 10.18 | 15.22 | 16.25 | 8.27 |
| FIO089 | 33 | 481 | 2.70 | 1 | 1 | 9.77 | 9.56 | 6.44 | 8.96 | 8.71 | 5.76 |
| MEE014 | 42 | 707 | 4.07 | 1 | 1 | 12.59 | 14.85 | 3.82 | 12.68 | 15.10 | 3.96 |
| MEE071 | 92 | 945 | 4.39 | 1 | 1 | 25.61 | 26.24 | 17.57 | 25.60 | 26.38 | 17.81 |
| MEE073 | 118 | 1155 | 6.06 | 1 | 1 | 16.71 | 15.93 | 13.77 | 16.54 | 15.59 | 13.69 |
| MEO015 | 22 | 303 | 1.50 | 1 | 1 | 12.87 | 13.53 | 7.92 | 12.91 | 13.44 | 9.03 |
| MTD0010ID | 20 | 195 | 1.24 | 1 | 1 | 7.18 | 7.18 | 3.59 | 7.87 | 6.67 | 4.38 |
| MTD009PM | 80 | 692 | 5.29 | 1 | 1 | 9.10 | 10.84 | 6.21 | 8.92 | 10.58 | 5.92 |
| MTD011UID | 33 | 243 | 2.31 | 1 | 1 | 20.99 | 20.16 | 16.46 | 20.76 | 20.03 | 15.39 |
| MTD012ME | 47 | 411 | 2.32 | 1 | 1 | 10.71 | 10.22 | 6.81 | 10.73 | 9.81 | 7.20 |

## annotation_role

| Value | Clips | Words | Minutes | Series | Speakers | Official L | Official T | Official P | Stem-weighted L | Stem-weighted T | Stem-weighted P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ID | 90 | 1310 | 7.58 | 3 | 3 | 12.90 | 14.20 | 5.27 | 12.64 | 13.89 | 5.43 |
| ME | 122 | 1464 | 7.65 | 3 | 3 | 9.90 | 9.22 | 7.17 | 9.42 | 8.61 | 7.11 |
| PM | 192 | 1936 | 13.17 | 3 | 3 | 8.83 | 9.56 | 5.89 | 8.82 | 9.59 | 5.92 |
| UI | 73 | 713 | 4.78 | 3 | 3 | 16.55 | 16.83 | 11.36 | 16.10 | 16.33 | 10.96 |
| unannotated | 323 | 3161 | 16.75 | 1 | 4 | 19.84 | 20.53 | 13.35 | 19.86 | 20.51 | 13.33 |

## duration_bin

| Value | Clips | Words | Minutes | Series | Speakers | Official L | Official T | Official P | Stem-weighted L | Stem-weighted T | Stem-weighted P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Q1 | 197 | 828 | 4.39 | 4 | 16 | 23.79 | 22.83 | 20.17 | 23.60 | 22.30 | 19.77 |
| Q2 | 200 | 1394 | 7.56 | 4 | 16 | 18.29 | 20.30 | 14.28 | 18.03 | 19.81 | 13.83 |
| Q3 | 203 | 2237 | 12.97 | 4 | 16 | 12.11 | 12.65 | 7.78 | 12.27 | 12.85 | 8.10 |
| Q4 | 200 | 4125 | 24.99 | 4 | 16 | 12.29 | 12.61 | 6.08 | 11.92 | 12.27 | 6.06 |

