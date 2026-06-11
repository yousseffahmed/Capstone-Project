# k=4 vs k=6 Cluster Comparison

Both k values are fit on full-site behavioral signatures for diagnosis only. Production scoring must still use fold-safe assignment.

## k=4 Profiles

|   cluster |   n_sites |   pm25_mean |   pm25_std |   pm25_p90 |   pm25_season_amp |   temp_mean |   humidity_mean |   windspeed_mean |   precip_mean | behavior_label                                   |
|----------:|----------:|------------:|-----------:|-----------:|------------------:|------------:|----------------:|-----------------:|--------------:|:-------------------------------------------------|
|         1 |        13 |      29.699 |     11.51  |     44.812 |            24.336 |      22.092 |          81.082 |            1.57  |         0.808 | pollution-rank-1 / stable / stagnant / humid     |
|         3 |        16 |      36.384 |     15.853 |     56.654 |            37.749 |      22.33  |          80.67  |            1.643 |         0.863 | pollution-rank-2 / stable / ventilated / drier   |
|         2 |         3 |      46.555 |     20.222 |     73.463 |            42.35  |      21.338 |          86.056 |            1.148 |         1.017 | pollution-rank-3 / volatile / stagnant / humid   |
|         0 |         7 |      51.882 |     21.355 |     80.015 |            48.827 |      22.14  |          80.661 |            1.579 |         0.8   | pollution-rank-4 / volatile / ventilated / drier |

## k=6 Profiles

|   cluster |   n_sites |   pm25_mean |   pm25_std |   pm25_p90 |   pm25_season_amp |   temp_mean |   humidity_mean |   windspeed_mean |   precip_mean | behavior_label                                   |
|----------:|----------:|------------:|-----------:|-----------:|------------------:|------------:|----------------:|-----------------:|--------------:|:-------------------------------------------------|
|         3 |        13 |      29.699 |     11.51  |     44.812 |            24.336 |      22.092 |          81.082 |            1.57  |         0.808 | pollution-rank-1 / stable / stagnant / humid     |
|         5 |         6 |      35.093 |     14.72  |     54.268 |            33.245 |      22.541 |          80.34  |            1.696 |         0.917 | pollution-rank-2 / stable / ventilated / drier   |
|         1 |        11 |      37.681 |     16.711 |     59.032 |            40.606 |      22.181 |          80.899 |            1.608 |         0.829 | pollution-rank-3 / stable / ventilated / humid   |
|         2 |         3 |      46.555 |     20.222 |     73.463 |            42.35  |      21.338 |          86.056 |            1.148 |         1.017 | pollution-rank-4 / volatile / stagnant / humid   |
|         4 |         5 |      52.899 |     20.436 |     79.673 |            45.448 |      22.154 |          80.6   |            1.561 |         0.793 | pollution-rank-5 / volatile / stagnant / drier   |
|         0 |         1 |      55.776 |     28.812 |     93.255 |            72.392 |      22.253 |          80.425 |            1.672 |         0.823 | pollution-rank-6 / volatile / ventilated / drier |

## k=4 to k=6 Crosswalk

|   k4_cluster |   0 |   1 |   2 |   3 |   4 |   5 |
|-------------:|----:|----:|----:|----:|----:|----:|
|            0 |   1 |   1 |   0 |   0 |   5 |   0 |
|            1 |   0 |   0 |   0 |  13 |   0 |   0 |
|            2 |   0 |   0 |   3 |   0 |   0 |   0 |
|            3 |   0 |  10 |   0 |   0 |   0 |   6 |

## Sites in small k=6 clusters

| site_id   |   k4_cluster |   k6_cluster |   pm25_mean |   pm25_p90 |   windspeed_mean |   humidity_mean |
|:----------|-------------:|-------------:|------------:|-----------:|-----------------:|----------------:|
| site_58   |            2 |            2 |      46.725 |     72.064 |            1.178 |          86.175 |
| site_59   |            2 |            2 |      54.626 |     83.704 |            1.17  |          85.859 |
| site_61   |            0 |            0 |      55.776 |     93.255 |            1.672 |          80.425 |
| site_64   |            2 |            2 |      38.312 |     64.621 |            1.095 |          86.134 |

## Interpretation

- k=6 is not random noise: it separates higher-resolution pollution/volatility/ventilation regimes that k=4 merges.

- The risk is sample size. Several k=6 groups contain only one to three sites, so a full-history category can act like a high-resolution site-regime label.

- That explains why k=6 full-history can score well: the oracle category captures mature pollution behavior. The deployable problem is recovering that same fine label from early evidence.

- Treat k=6 as meaningful but fragile: useful as an upper-bound research lead, not a production replacement until early-window assignment is reliable or more sites stabilize the small groups.
