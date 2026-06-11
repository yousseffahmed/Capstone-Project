# Category Assignment Error Analysis

k=6 full-history is an upper bound. All window rows use only the first N observed days and evaluate after that window.

## Performance Summary

| method                         |   window_days |   k | deployability              |     r2 |     rmse |      mae |   n_eval |
|:-------------------------------|--------------:|----:|:---------------------------|-------:|---------:|---------:|---------:|
| accepted_k4_baseline_reference |           nan |   4 | accepted_reference         | 0.564  | nan      | nan      |      nan |
| accepted_k4_safety_reference   |           nan |   4 | accepted_reference         | 0.558  | nan      | nan      |      nan |
| full_history                   |             0 |   6 | non_deployable_upper_bound | 0.5575 |  12.8135 |   9.3755 |    13944 |
| geodata                        |            60 |   6 | zero_deploy                | 0.4159 |  14.5793 |  10.3777 |    11604 |
| window                         |            60 |   6 | short_deploy               | 0.4463 |  14.1953 |  10.4178 |    11604 |
| distance                       |            60 |   6 | short_deploy               | 0.1166 |  17.9299 |  14.4461 |    11604 |
| soft                           |            60 |   6 | short_deploy               | 0.2345 |  16.6909 |  13.2428 |    11604 |
| classifier_window_geo          |            60 |   6 | short_deploy               | 0.2331 |  16.7051 |  13.259  |    11604 |
| window                         |            14 |   6 | short_deploy               | 0.4039 |  14.9395 |  10.7062 |    13398 |
| window                         |            30 |   6 | short_deploy               | 0.5049 |  13.683  |   9.9599 |    12774 |
| window                         |            45 |   6 | short_deploy               | 0.5059 |  13.5877 |   9.7639 |    12189 |
| window                         |            60 |   6 | short_deploy               | 0.4463 |  14.1953 |  10.4178 |    11604 |
| window                         |            90 |   6 | short_deploy               | 0.3803 |  14.7451 |  10.8496 |    10443 |
| window                         |           120 |   6 | short_deploy               | 0.4269 |  13.799  |  10.0968 |     9303 |

## Window-60 wrong category assignments

| site_id   |   fold | method                |   window_days |   true_full_category |   assigned_category | category_correct   |   rmse |    mae |    bias |
|:----------|-------:|:----------------------|--------------:|---------------------:|--------------------:|:-------------------|-------:|-------:|--------:|
| site_61   |      5 | classifier_window_geo |            60 |                    5 |                   4 | False              | 29.078 | 25.707 | -12.033 |
| site_68   |      4 | classifier_window_geo |            60 |                    4 |                   5 | False              | 27.052 | 24.758 |  24.59  |
| site_52   |      5 | classifier_window_geo |            60 |                    1 |                   2 | False              | 22.731 | 20.38  |  19.421 |
| site_59   |      2 | classifier_window_geo |            60 |                    4 |                   2 | False              | 21.626 | 15.637 | -10.797 |
| site_54   |      1 | classifier_window_geo |            60 |                    3 |                   5 | False              | 18.778 | 15.24  | -14.428 |
| site_63   |      3 | classifier_window_geo |            60 |                    1 |                   4 | False              | 17.362 | 14.414 |   9.311 |
| site_36   |      1 | classifier_window_geo |            60 |                    0 |                   5 | False              | 16.067 | 13.52  |   8.535 |
| site_64   |      2 | classifier_window_geo |            60 |                    4 |                   2 | False              | 16.022 | 13.564 |  10.191 |
| site_58   |      2 | classifier_window_geo |            60 |                    4 |                   2 | False              | 15.056 | 11.142 |  -5.837 |
| site_66   |      1 | classifier_window_geo |            60 |                    5 |                   0 | False              | 13.675 | 12.86  |  12.701 |
| site_29   |      3 | classifier_window_geo |            60 |                    1 |                   0 | False              | 11.925 | 10.755 |  10.367 |
| site_70   |      3 | classifier_window_geo |            60 |                    1 |                   4 | False              |  9.812 |  8.137 |   6.005 |
| site_49   |      2 | classifier_window_geo |            60 |                    3 |                   2 | False              |  9.352 |  8.159 |   7.37  |
| site_91   |      5 | classifier_window_geo |            60 |                    2 |                   1 | False              |  9.149 |  5.939 |   1.67  |
| site_47   |      3 | classifier_window_geo |            60 |                    1 |                   0 | False              |  8.1   |  6.48  |   2.305 |
| site_65   |      4 | classifier_window_geo |            60 |                    0 |                   1 | False              |  6.687 |  5.085 |   3.272 |
| site_88   |      2 | classifier_window_geo |            60 |                    3 |                   0 | False              |  5.687 |  4.943 |   3.66  |
| site_76   |      4 | distance              |            60 |                    0 |                   4 | False              | 31.823 | 30.358 |  30.348 |
| site_74   |      5 | distance              |            60 |                    2 |                   4 | False              | 29.611 | 28.189 |  27.911 |
| site_61   |      5 | distance              |            60 |                    5 |                   2 | False              | 27.204 | 24.296 |  -7.773 |
| site_52   |      5 | distance              |            60 |                    1 |                   2 | False              | 22.769 | 20.468 |  19.555 |
| site_54   |      1 | distance              |            60 |                    3 |                   1 | False              | 19.132 | 15.063 | -13.235 |
| site_71   |      5 | distance              |            60 |                    4 |                   3 | False              | 19.041 | 17.497 |  17.129 |
| site_66   |      1 | distance              |            60 |                    5 |                   3 | False              | 18.77  | 18.025 |  17.947 |
| site_63   |      3 | distance              |            60 |                    1 |                   4 | False              | 18.57  | 15.864 |   8.284 |
| site_68   |      4 | distance              |            60 |                    4 |                   5 | False              | 17.929 | 15.451 |  14.405 |
| site_36   |      1 | distance              |            60 |                    0 |                   1 | False              | 17.411 | 15.089 |  12.422 |
| site_53   |      2 | distance              |            60 |                    2 |                   4 | False              | 16.408 | 13.222 | -12.709 |
| site_79   |      1 | distance              |            60 |                    4 |                   0 | False              | 16.381 | 15.41  |  15.309 |
| site_70   |      3 | distance              |            60 |                    1 |                   4 | False              | 14.373 | 12.009 |  10.43  |
| site_57   |      1 | distance              |            60 |                    5 |                   1 | False              | 13.642 | 11.489 |   4.244 |
| site_43   |      3 | distance              |            60 |                    1 |                   2 | False              | 13.598 | 11.81  |  10.92  |
| site_29   |      3 | distance              |            60 |                    1 |                   0 | False              | 13.103 | 12.052 |  11.821 |
| site_51   |      4 | distance              |            60 |                    1 |                   0 | False              | 12.857 | 10.114 |   1.112 |
| site_35   |      1 | distance              |            60 |                    5 |                   1 | False              | 12.167 | 10.232 |   7.724 |
| site_47   |      3 | distance              |            60 |                    1 |                   0 | False              |  9.992 |  8.272 |   6.325 |
| site_39   |      4 | distance              |            60 |                    1 |                   0 | False              |  7.752 |  6.353 |   2.691 |
| site_49   |      2 | distance              |            60 |                    3 |                   4 | False              |  7.019 |  5.762 |   3.46  |
| site_26   |      2 | distance              |            60 |                    3 |                   4 | False              |  5.862 |  4.648 |   1.677 |
| site_88   |      2 | distance              |            60 |                    3 |                   0 | False              |  4.337 |  3.439 |   0.502 |
| site_54   |      1 | geodata               |            60 |                    3 |                   4 | False              | 36.39  | 33.254 | -33.254 |
| site_61   |      5 | geodata               |            60 |                    5 |                   2 | False              | 31.069 | 26.226 | -17.093 |
| site_59   |      2 | geodata               |            60 |                    4 |                   2 | False              | 21.232 | 15.366 | -10.467 |
| site_57   |      1 | geodata               |            60 |                    5 |                   4 | False              | 20.615 | 16.158 | -15.927 |
| site_58   |      2 | geodata               |            60 |                    4 |                   3 | False              | 19.645 | 15.516 | -13.396 |
| site_72   |      5 | geodata               |            60 |                    5 |                   3 | False              | 19.505 | 15.982 | -15.636 |
| site_48   |      5 | geodata               |            60 |                    2 |                   0 | False              | 18.961 | 17.045 |  17.045 |
| site_63   |      3 | geodata               |            60 |                    1 |                   4 | False              | 18.191 | 15.289 |  13.787 |
| site_51   |      4 | geodata               |            60 |                    1 |                   5 | False              | 17.034 | 14.33  |  11.988 |
| site_70   |      3 | geodata               |            60 |                    1 |                   4 | False              | 13.324 | 11.585 |  10.645 |
| site_45   |      1 | geodata               |            60 |                    3 |                   5 | False              | 13.203 | 10.35  |  -4.288 |
| site_64   |      2 | geodata               |            60 |                    4 |                   1 | False              | 12.662 | 10.883 |   3.65  |
| site_35   |      1 | geodata               |            60 |                    5 |                   0 | False              | 12.545 | 10.599 |   7.289 |
| site_47   |      3 | geodata               |            60 |                    1 |                   0 | False              | 11.661 |  9.291 |  -7.774 |
| site_89   |      3 | geodata               |            60 |                    0 |                   5 | False              | 11.483 | 10.424 |  10.424 |
| site_71   |      5 | geodata               |            60 |                    4 |                   2 | False              | 10.813 |  9.302 |   8.237 |
| site_91   |      5 | geodata               |            60 |                    2 |                   3 | False              | 10.295 |  6.521 |   2.922 |
| site_74   |      5 | geodata               |            60 |                    2 |                   0 | False              | 10.09  |  7.819 |   5.213 |
| site_52   |      5 | geodata               |            60 |                    1 |                   0 | False              |  9.912 |  7.545 |   2.421 |
| site_135  |      4 | geodata               |            60 |                    0 |                   1 | False              |  9.698 |  7.904 |   6.303 |
| site_43   |      3 | geodata               |            60 |                    1 |                   0 | False              |  9.662 |  7.161 |  -4.815 |
| site_68   |      4 | geodata               |            60 |                    4 |                   1 | False              |  8.897 |  6.626 |   0.523 |
| site_69   |      3 | geodata               |            60 |                    5 |                   0 | False              |  7.497 |  5.713 |  -2.404 |
| site_67   |      3 | geodata               |            60 |                    5 |                   1 | False              |  7.404 |  5.903 |   3.513 |
| site_65   |      4 | geodata               |            60 |                    0 |                   1 | False              |  7.03  |  5.054 |   2.755 |
| site_26   |      2 | geodata               |            60 |                    3 |                   0 | False              |  6.391 |  4.462 |  -3.467 |
| site_49   |      2 | geodata               |            60 |                    3 |                   1 | False              |  5.486 |  4.435 |   1.357 |
| site_66   |      1 | geodata               |            60 |                    5 |                   4 | False              |  4.709 |  3.63  |   0.36  |
| site_79   |      1 | geodata               |            60 |                    4 |                   0 | False              |  4.549 |  3.554 |   1.522 |
| site_88   |      2 | geodata               |            60 |                    3 |                   0 | False              |  4.491 |  3.397 |  -2.144 |
| site_76   |      4 | soft                  |            60 |                    0 |                   4 | False              | 29.811 | 28.319 |  28.306 |
| site_61   |      5 | soft                  |            60 |                    5 |                   2 | False              | 29.077 | 25.707 | -12.029 |
| site_68   |      4 | soft                  |            60 |                    4 |                   5 | False              | 27.052 | 24.758 |  24.59  |
| site_74   |      5 | soft                  |            60 |                    2 |                   4 | False              | 26.243 | 24.748 |  24.431 |
| site_52   |      5 | soft                  |            60 |                    1 |                   2 | False              | 22.731 | 20.38  |  19.421 |
| site_54   |      1 | soft                  |            60 |                    3 |                   1 | False              | 18.551 | 14.987 | -14.117 |
| site_63   |      3 | soft                  |            60 |                    1 |                   4 | False              | 17.362 | 14.414 |   9.311 |
| site_36   |      1 | soft                  |            60 |                    0 |                   1 | False              | 16.136 | 13.628 |   8.73  |
| site_71   |      5 | soft                  |            60 |                    4 |                   3 | False              | 15.537 | 13.769 |  13.23  |
| site_57   |      1 | soft                  |            60 |                    5 |                   1 | False              | 14.703 | 11.015 |  -5.46  |
| site_51   |      4 | soft                  |            60 |                    1 |                   0 | False              | 13.788 | 11.282 |   2.541 |
| site_66   |      1 | soft                  |            60 |                    5 |                   3 | False              | 13.675 | 12.86  |  12.701 |
| site_53   |      2 | soft                  |            60 |                    2 |                   4 | False              | 13.594 | 10.648 |  -9.519 |
| site_29   |      3 | soft                  |            60 |                    1 |                   0 | False              | 11.925 | 10.755 |  10.367 |
| site_39   |      4 | soft                  |            60 |                    1 |                   0 | False              | 11.03  |  8.697 |   6.269 |
| site_35   |      1 | soft                  |            60 |                    5 |                   1 | False              | 10.289 |  8.281 |   3.283 |
| site_43   |      3 | soft                  |            60 |                    1 |                   2 | False              | 10.177 |  8.673 |   6.359 |
| site_79   |      1 | soft                  |            60 |                    4 |                   0 | False              | 10.12  |  8.965 |   8.682 |
| site_70   |      3 | soft                  |            60 |                    1 |                   4 | False              |  9.812 |  8.137 |   6.005 |
| site_49   |      2 | soft                  |            60 |                    3 |                   4 | False              |  9.346 |  8.151 |   7.355 |
| site_47   |      3 | soft                  |            60 |                    1 |                   0 | False              |  8.1   |  6.48  |   2.305 |
| site_26   |      2 | soft                  |            60 |                    3 |                   4 | False              |  7.694 |  6.605 |   5.041 |
| site_88   |      2 | soft                  |            60 |                    3 |                   0 | False              |  5.687 |  4.943 |   3.66  |
| site_61   |      5 | window                |            60 |                    5 |                   2 | False              | 31.069 | 26.226 | -17.093 |
| site_61   |      5 | window                |            60 |                    5 |                   2 | False              | 31.069 | 26.226 | -17.093 |
| site_54   |      1 | window                |            60 |                    3 |                   1 | False              | 24.949 | 21.344 | -21.264 |
| site_54   |      1 | window                |            60 |                    3 |                   1 | False              | 24.949 | 21.344 | -21.264 |
| site_68   |      4 | window                |            60 |                    4 |                   5 | False              | 21.523 | 19.708 |  19.261 |
| site_68   |      4 | window                |            60 |                    4 |                   5 | False              | 21.523 | 19.708 |  19.261 |
| site_66   |      1 | window                |            60 |                    5 |                   3 | False              | 20.557 | 19.689 |  19.625 |
| site_66   |      1 | window                |            60 |                    5 |                   3 | False              | 20.557 | 19.689 |  19.625 |
| site_51   |      4 | window                |            60 |                    1 |                   0 | False              | 18.689 | 14.234 | -13.126 |
| site_51   |      4 | window                |            60 |                    1 |                   0 | False              | 18.689 | 14.234 | -13.126 |
| site_63   |      3 | window                |            60 |                    1 |                   4 | False              | 18.191 | 15.289 |  13.787 |
| site_63   |      3 | window                |            60 |                    1 |                   4 | False              | 18.191 | 15.289 |  13.787 |
| site_53   |      2 | window                |            60 |                    2 |                   4 | False              | 16.507 | 14.201 | -14.013 |
| site_53   |      2 | window                |            60 |                    2 |                   4 | False              | 16.507 | 14.201 | -14.013 |
| site_76   |      4 | window                |            60 |                    0 |                   4 | False              | 15.882 | 13.794 |  13.242 |
| site_76   |      4 | window                |            60 |                    0 |                   4 | False              | 15.882 | 13.794 |  13.242 |
| site_35   |      1 | window                |            60 |                    5 |                   1 | False              | 14.298 | 12.22  |  10.008 |
| site_35   |      1 | window                |            60 |                    5 |                   1 | False              | 14.298 | 12.22  |  10.008 |
| site_57   |      1 | window                |            60 |                    5 |                   1 | False              | 14.065 | 10.265 |  -5.742 |
| site_57   |      1 | window                |            60 |                    5 |                   1 | False              | 14.065 | 10.265 |  -5.742 |
| site_70   |      3 | window                |            60 |                    1 |                   4 | False              | 13.324 | 11.585 |  10.645 |
| site_70   |      3 | window                |            60 |                    1 |                   4 | False              | 13.324 | 11.585 |  10.645 |
| site_39   |      4 | window                |            60 |                    1 |                   0 | False              | 12.512 | 10.311 |  -9.431 |
| site_39   |      4 | window                |            60 |                    1 |                   0 | False              | 12.512 | 10.311 |  -9.431 |
| site_36   |      1 | window                |            60 |                    0 |                   1 | False              | 11.987 |  9.266 |  -0.228 |
| site_36   |      1 | window                |            60 |                    0 |                   1 | False              | 11.987 |  9.266 |  -0.228 |
| site_47   |      3 | window                |            60 |                    1 |                   0 | False              | 11.661 |  9.291 |  -7.774 |
| site_47   |      3 | window                |            60 |                    1 |                   0 | False              | 11.661 |  9.291 |  -7.774 |
| site_71   |      5 | window                |            60 |                    4 |                   3 | False              | 11.515 | 10.07  |   9.371 |
| site_71   |      5 | window                |            60 |                    4 |                   3 | False              | 11.515 | 10.07  |   9.371 |
| site_52   |      5 | window                |            60 |                    1 |                   2 | False              | 10.93  |  7.767 |  -0.69  |
| site_52   |      5 | window                |            60 |                    1 |                   2 | False              | 10.93  |  7.767 |  -0.69  |
| site_74   |      5 | window                |            60 |                    2 |                   4 | False              | 10.083 |  7.816 |   5.206 |
| site_74   |      5 | window                |            60 |                    2 |                   4 | False              | 10.083 |  7.816 |   5.206 |
| site_43   |      3 | window                |            60 |                    1 |                   2 | False              |  8.105 |  6.457 |   2.562 |
| site_43   |      3 | window                |            60 |                    1 |                   2 | False              |  8.105 |  6.457 |   2.562 |
| site_49   |      2 | window                |            60 |                    3 |                   4 | False              |  6.226 |  5.001 |   2.837 |
| site_49   |      2 | window                |            60 |                    3 |                   4 | False              |  6.226 |  5.001 |   2.837 |
| site_29   |      3 | window                |            60 |                    1 |                   0 | False              |  6.124 |  4.894 |   0.144 |
| site_29   |      3 | window                |            60 |                    1 |                   0 | False              |  6.124 |  4.894 |   0.144 |
| site_26   |      2 | window                |            60 |                    3 |                   4 | False              |  5.016 |  3.807 |   0.413 |
| site_26   |      2 | window                |            60 |                    3 |                   4 | False              |  5.016 |  3.807 |   0.413 |
| site_79   |      1 | window                |            60 |                    4 |                   0 | False              |  4.549 |  3.554 |   1.522 |
| site_79   |      1 | window                |            60 |                    4 |                   0 | False              |  4.549 |  3.554 |   1.522 |
| site_88   |      2 | window                |            60 |                    3 |                   0 | False              |  4.491 |  3.397 |  -2.144 |
| site_88   |      2 | window                |            60 |                    3 |                   0 | False              |  4.491 |  3.397 |  -2.144 |

## Diagnosis

- The full-history k=6 label captures mature pollution level, volatility, seasonality, and ventilation. Early windows often do not contain enough seasonal variation to recover the fine label.

- Moving from 14 to 120 days tests whether this is just a short-window problem. If R2 does not approach the full-history upper bound, the gap is also caused by unstable small clusters and category noise.

- Distance/probability features reduce hard-routing brittleness in principle, but they must beat the accepted k=4 reference before being promoted.

- Geodata-only category inference remains zero-deploy, but it cannot observe the local PM2.5 regime and should be treated as a weak prior, not a true category.
