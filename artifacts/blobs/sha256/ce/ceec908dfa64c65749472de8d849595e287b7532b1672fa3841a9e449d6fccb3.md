# Reported participant profile distribution

Source: `evidence/simulated_data.zip`, table `simulated_data/regular/data/Bot.csv`. Counts include completed simulated participants only (`complete == True` and `aborted == False`).

| bot_profile   |   completed_participants |
|:--------------|-------------------------:|
| normal_rgb    |                        5 |
| random        |                        5 |

Total completed simulated participants: 10.

Profile stability and trial completion checks from `CustomTrial.csv`:

|   participant_id | bot_profile   |   n_profiles |   n_color_trials | responses_in_range   |
|-----------------:|:--------------|-------------:|-----------------:|:---------------------|
|                1 | normal_rgb    |            1 |                7 | True                 |
|                2 | normal_rgb    |            1 |                7 | True                 |
|                3 | normal_rgb    |            1 |                7 | True                 |
|                4 | random        |            1 |                7 | True                 |
|                5 | random        |            1 |                7 | True                 |
|                6 | random        |            1 |                7 | True                 |
|                7 | normal_rgb    |            1 |                7 | True                 |
|                8 | random        |            1 |                7 | True                 |
|                9 | normal_rgb    |            1 |                7 | True                 |
|               10 | random        |            1 |                7 | True                 |

Lightweight behavioral comparison from finalized color trials:

| bot_profile   |   n_color_trials |   response_min |   response_max |   response_variance |   mean_abs_distance_from_start |   median_abs_distance_from_start |
|:--------------|-----------------:|---------------:|---------------:|--------------------:|-------------------------------:|---------------------------------:|
| normal_rgb    |               35 |              0 |            250 |             5774.63 |                         14.571 |                               12 |
| random        |               35 |              2 |            255 |             6118.97 |                         94.229 |                               87 |
