# Viva preparation – Chicago Crime Type Prediction (XMen 2.1)

The questions are grouped by slide or frontend screen. Each one has a short suggested answer.
Questions marked ⚠ are the ones most likely to catch you out.

---

## A. Know these numbers before you walk in

| What | Value | Where it comes from |
|---|---|---|
| Dataset | 662,472 incidents, 31 crime types, Jan 2024 – 16 Sep 2026 | notebooks 01–03 |
| Split | train < Jul 2025 · validation Jul–Dec 2025 · test 2026 | notebooks 07–14 |
| Always guessing THEFT (majority class) | 21.6% accuracy | notebook 14 |
| Earlier tuned XGBoost (notebook 13) | test accuracy 36.5%, macro F1 0.12, top-3 ≈ 65% | notebook 13 / 14 |
| Final XGBoost (notebook 14, **on the slides and served by the app**) | test top-3 68.2%, top-1 38.4%, macro F1 0.153, weighted F1 0.337 | notebook 14 |
| Best / weakest | BATTERY F1 0.55, THEFT 0.50 · rare classes ≈ 0 | notebook 14 |
| Biggest confusion | ASSAULT predicted as BATTERY (6,213 test records) | notebook 14 |

Notebook 14 reads 663,675 rows instead of 662,472. When run outside Databricks it downloads the same public
City of Chicago dataset, which has had a few late reports added since your snapshot. Re-running the previous
model on those rows gives the same results as notebook 13 (36.5% accuracy), so the comparison is fair.

The app serves the same final XGBoost. `backend/train_final_model.py` uses the same feature code
(`backend/app/final_pipeline.py`) and settings as notebook 14, and the dashboard reads its metrics from
`backend/models/final_model_metrics.json`.

---

## B. Business problem and value (slides 3, 4, 10)

1. **Who is the user of this product, and what decision does it help them make?**
   Crime analysts and dispatch or desk officers. It gives them a quick first categorisation of an incident, and
   lets them compare which crime types are likely in a given time and place. It supports their judgement; it
   does not replace it.

2. **Why predict crime *type* rather than *whether* a crime will happen?**
   Every row in the data is a crime that was reported, so we have no "no-crime" examples. That means we cannot
   learn the chance of a crime happening at all. What we can learn is, given an incident, which type it most
   likely is.

3. **Your top-1 accuracy is 38%. Why would anyone use this?**
   There are 31 classes, and always guessing THEFT gives 21.6%, so the model is 1.8× better than guessing.
   The interface shows a ranked list, and the true type is in the top 3 for 68% of unseen 2026 incidents. That
   narrows 31 options to 3 for two incidents in three.

4. **Why is accuracy limited at all? Is it bad modelling?**
   No. Several crime types happen in the same places at the same times. ASSAULT and BATTERY differ by the act
   itself, not by when or where it happened, so a model that only sees time and place cannot fully separate
   them. The leakage fields that would separate them (description, IUCR, FBI code, arrest) are only known
   *after* the incident is classified, so we excluded them on purpose.

5. **What is the business cost of a wrong prediction?**
   The output is decision support, so a person stays in the loop. A wrong suggestion costs a few seconds of
   review, not a wrong action. Slide 10's guardrail says not to rely on rare-class predictions for high-stakes
   decisions.

6. **Could this lead to biased or over-policing of certain areas?**
   Yes, that's a risk. Historical reports reflect where police already patrol, so the model can repeat that
   pattern. That is why we position it as decision support with a human in the loop, not automated
   deployment, and why the "suggested actions" are labelled as rule-based guidance.

7. **How would you measure business value after deployment?**
   Time saved per categorisation, analyst agreement rate with the top-3 list, and monthly top-3 accuracy on
   new incidents to watch for drift.

8. **How would this scale or stay accurate over time?**
   Retrain monthly or quarterly on a rolling window, evaluated on the most recent month. The chronological
   split already simulates exactly this.

9. **What is the one insight from the data that shaped the product? (slide 5)**
   Location type and the domestic flag matter most. Time patterns (Fridays, summer, night-time) add signal.
   In notebook 14, "domestic × location type" history was the single strongest feature.

---

## C. Frontend output – Crime Predictor screen ⚠ (most questions will be here)

10. **Walk us through the inputs. Why these fields?**
    Location type, community area, district, ward, beat, day of week, month, hour, domestic flag and
    coordinates. They are exactly the fields known when an incident is first reported. Choosing a community
    area fills in district, ward, beat and coordinates automatically to reduce input errors.

11. **What does "Predicted Crime Type" and the % next to it mean?**
    It is the class with the highest model probability. The % is the model's estimated probability for that
    class in this context. It is *not* the probability that a crime will happen.

12. **⚠ The top prediction is only around 19%. Isn't the model unsure? Why show it?**
    With 31 classes, an even guess would be about 3%, so 19% is a meaningful signal. When the top probability
    is below 40%, the UI says *"No single crime type dominates… consider the full distribution"*, and the
    suggested actions mention the next two types. That is the honest way to show uncertainty.

12b. **⚠ The predicted type shows 36.5%, but your accuracy is 68%. Why hasn't it improved?**
    They measure different things. The % is the model's probability *for this one situation*: with 31 types, the
    top type rarely goes above 50%. Accuracy is measured over all 165,895 test incidents and appears on the
    dashboard. The line underneath, "combined probability of the top 3 types", is the per-situation counterpart
    of the 68% top-3 accuracy.

13. **What is the "Multiclass Probability Distribution"?**
    The top 5 classes from the softmax output, sorted. They do not sum to 100% because the other 26 classes
    hold the rest.

14. **⚠ Where does "High / Moderate / Low severity" come from? Is it predicted?**
    No. It is a fixed, rule-based grouping of crime types; homicide, robbery, battery and weapons count as
    High. The UI says so under "Suggested Actions".

15. **⚠ Are the "Suggested Actions" produced by the ML model?**
    No. They are rule-based text built from the prediction, for example adding a patrol suggestion when the
    category is violent. The ML output is only the probabilities.

16. **⚠ The page subtitle says it predicts "risk level, and arrest likelihood". Does it?**
    It doesn't. The model predicts crime type only. Arrest is excluded because it is post-incident leakage.
    *(The subtitle in `frontend/src/pages/CrimePredictor.jsx` has now been corrected to say it ranks crime types.)*

17. **If I change only the hour (for example 03:00 vs 14:00), why does the prediction change?**
    Time of day shifts the mix. Late night raises battery and weapons violations; daytime raises theft and
    deceptive practice. Show this live; it is a good demo moment.

18. **Why does ticking "Domestic" change the result so much?**
    Domestic incidents are mostly battery and assault, so it is the strongest single input. Notebook 14's
    feature importance confirms this.

19. **What happens with bad input, such as ward 99 or coordinates outside Chicago?**
    Validation runs on the client and is repeated on the backend (FastAPI 422). The UI shows a clear error and
    does not predict. Demo this.

20. **What if the backend is down?**
    The UI shows "Cannot reach the prediction API…". There is no fake fallback output.

21. **Why can't the user enter the year or exact date?**
    The user describes a typical situation (month, weekday, hour), not one exact report. The backend predicts for
    every matching date in that month (for example every Saturday in July 2026) and for typical report minutes,
    with "on the hour" weighted by how often reports are rounded in the training data. It then averages the
    probabilities. The response's `averaged_over` field shows exactly which window was used.

---

## D. Frontend output – Dashboard, Map and Trends screens

22. **"Total Incidents", "Arrest Rate", "High Risk Hotspots": are these model outputs?**
    No. They are descriptive statistics from the cleaned dataset. Only the Predictor screen and the Model
    Performance card relate to the model.

23. **⚠ How is a "High Risk" hotspot defined?**
    It is a rule, not a prediction. The backend takes the 10 community areas with the most incidents in the
    cleaned dataset and labels an area "High" if it has at least **three times the median community area's count** (about 19,500 incidents, so the top 6 areas are High),
    otherwise "Moderate" (`backend/app/main.py`). The Map page states this. It is descriptive, not a forecast.

24. **⚠ The dashboard shows 68.2% "Top-3 Accuracy". Is that the accuracy of the model?**
    It is top-3 accuracy: the true type is among the 3 highest-ranked types. The same card shows top-1 accuracy
    (38.4%), and the Model Performance panel shows always guessing THEFT at 21.6%. Never call 68% "accuracy"
    without saying "top-3".

25. **Why are the model-performance bars "scaled to 20%"?**
    For readability, because all macro F1 values are below 0.2. Admit that macro F1 is low because of rare
    classes.

26. **What do the trend and map charts tell a business user?**
    The Trends page shows monthly theft, battery and robbery counts for 2025 (the last complete year), so summer
    peaks are visible. The Map page plots the 10 busiest community areas by location, with circle size showing
    incident count. Together they support patrol scheduling and resource planning. Both are calculated from the
    cleaned dataset when the backend starts.

---

## E. Model and method (likely but shorter)

27. **Why a chronological split and not a random one?** A random split lets the model learn from the future and
    gives over-optimistic results. Our test set is 2026, which the model never saw.
28. **Why macro F1 for model selection?** It weights every class equally, so the model cannot win by
    predicting only THEFT and BATTERY.
29. **What did feature engineering add to the final XGBoost?** It adds reporting-time flags (logged at 00:00, on the hour, or on the 1st)
    and smoothed historical crime-mix features per location type, beat, district, map grid and domestic flag.
    These are computed from training data only, out-of-fold. It also uses early stopping and finished at 234
    trees.
30. **⚠ Isn't the crime-mix feature target leakage?** No. It uses only training-period labels, and each
    training row gets values from the other folds, so a row never sees its own label. Validation and test rows
    use training statistics only.
31. **Why XGBoost over Random Forest or Logistic Regression?** It had the highest validation macro F1 under the
    same rule. Random Forest collapsed on rare classes (0.07).
32. **How did you handle class imbalance?** Macro F1 for selection. In notebook 14 we also tested per-class
    decision weights: macro F1 rose to 0.176 but accuracy fell to 35%, so we report it and don't deploy it.
33. **Why not group the 31 types into fewer categories?** We tested it. Grouping into Violent / Property /
    Public-order gives 70% accuracy, but the business asked for the specific type, so we kept 31 classes and
    show a ranked list instead.
34. **What would you do with more time?** Deploy the final XGBoost with an exact report-time input, add weather and event data,
    calibrate probabilities, and monitor drift monthly.
