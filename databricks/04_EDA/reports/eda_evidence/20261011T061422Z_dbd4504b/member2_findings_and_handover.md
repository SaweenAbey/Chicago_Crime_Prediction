# Member 2 — generated EDA findings

1. Coverage: 662,472 cleaned incident records, 22 source columns, 2024-01-01 05:30:00 through 2026-09-16 05:30:00. Partial periods need explicit exposure controls.

2. Class imbalance: THEFT represents 22.84% of records; NON-CRIMINAL has 9. Use macro/per-class metrics alongside accuracy.

3. Sparse targets: 5 classes have fewer than 100 records; top five classes account for 68.73%. Preserve class support in evaluation.

4. Temporal coverage: matched comparisons use 01-01 inclusive to 09-16 exclusive. Avoid interpreting a partial year's lower total as a decline.

5. Monthly/hourly structure: peak observed month 2024-07; peak recorded hour 00:00. Check partial months and default times before modelling.

6. Weekday structure: largest total on Friday; weekday_counts.csv includes calendar-day-normalized exposure.

7. Geographic structure: largest district group 8 (42,717); largest community_area group 25 (33,124); largest ward group 27 (31,090); largest beat group 1834 (8,050). Counts are not population-adjusted rates.

8. Coordinate coverage: 658,037 records (99.33%) plotted; 4,435 omitted from the coordinate plot only. Review class-specific missingness before imputation.

9. Context: leading location group STREET. Category-mix tables cover time, geography, location and domestic status; verify associations on validation data.

10. Review flags: 19 unusual daily totals, 0 zero-record days. Investigate rather than automatically delete. City Zone status: Pending Member 3: no features_table supplied.

## Handover to Member 3

Evaluate temporary time features, categorical geographic codes, location context and missingness. Review sparse groups. Exclude IUCR, crime description and FBI code from ordinary predictors; review arrest, updated_on and any post-event information. Confirm Domestic is known at prediction time. Fit encoders, imputers and any geographic clustering on training data only. Document the City Zone mapping.

## Handover to Member 4

Agree a time-aware train/validation/test protocol, retain support counts, and compare a training-majority baseline with models on the same evaluation population. Report accuracy, macro precision/recall/F1, weighted F1 and per-class results. Do not tune on the final test set. Use validation ablations to assess feature value.

## Limitations

These are associations in reported incidents, subject to reporting/enforcement patterns and extract coverage. They do not establish causality, future incident risk, or characteristics of individuals. No population denominators are available. City Zone EDA cannot establish model improvement.
