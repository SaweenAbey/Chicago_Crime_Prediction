# Speaker notes – 10 minutes total (about 2 minutes each + demo)

Keep it conversational. Point at the slide instead of reading it. If the time is short, skip the lines in *(brackets)*.

---

## You – Slides 3 & 4 (Problem and Solution) · ~2 min

**Slide 3 – Problem**
- "Chicago records around **670 crime reports every day**. We used **662,472 reports** from 2024 to 2026, across **31 crime types**."
- "That's far too much for a person to scan quickly, and the patterns change with place and time."
- "So our idea is simple: give a tool the context of an incident (where, when, what kind of place) and it returns the **most likely crime types, ranked, with probabilities**."
- "To be clear, this does **not** predict future crime. It classifies the likely type of an incident."

**Slide 4 – Solution**
- "Here's our end-to-end pipeline in five steps: raw data, cleaning, finding patterns, training and validating, and finally a prediction system."
- "The user only sees a simple form and a ranked answer. All the complexity stays behind the interface."
- *(Handover:)* "Amasha will show what the data told us."

---

## Amasha – Slides 5 & 6 (Data insights and Model comparison) · ~2 min

**Slide 5 – What the data revealed**
- "Three things stood out."
- "**Category mix:** theft alone is about 23% of all reports, and the top 5 types make up about two thirds."
- "**Time:** Fridays are the busiest day and summer peaks. July 2024 had over 24,000 reports."
- "**Place:** location changes the mix. In District 18, around 40% of reports are theft, and the street is the most common location."
- "So where, when and what kind of place became our model inputs."

**Slide 6 – Comparing models**
- "We trained four models on the same data, with the same validation period and the same scoring rule."
- "We ranked them by **macro F1**, which treats every crime type equally, so a model can't win by guessing only the common types."
- "Logistic Regression was slightly ahead at first, but after feature engineering and tuning, **XGBoost became the strongest model, at 0.159**."
- *(Handover:)* "Sanuja will explain how we got there and how it did on unseen data."

---

## Sanuja – Slides 7 & 8 (Final model and Test results) · ~2 min

**Slide 7 – From baseline to final XGBoost**
- "We started from a basic XGBoost at 0.116 macro F1."
- "Then we engineered new features. For example, whether a report was logged exactly on the hour or on the 1st of the month, which is typical of fraud and theft reports filed later. We also added the past crime mix for each location type and area, using **training data only, so there's no leakage**."
- "That raised the balanced score by about **37%**, to **0.159**."
- "Once we chose the model, we **froze it**. The test data was never used for tuning."

**Slide 8 – Final test on unseen 2026 data**
- "On 2026 data the model had never seen, the **true crime type is in our top 3 for 68% of incidents**, two out of three."
- "Its single top guess is right **38%** of the time. For comparison, always guessing the most common type gives only 22%, and there are 31 types."
- "Battery is predicted best. The main confusion is **assault versus battery**: they happen in the same places at the same times, so time and place alone can't separate them."
- *(Handover:)* "Savin will now show the system live."

---

## Savin – Slides 9 & 10 (Demo and Business value) · ~2 min talk + ~2 min demo

**Slide 9 – Live demo (Crime Predictor page)**
1. "I'll pick a situation: **Englewood, street, Saturday, 11 PM**." Click **Predict**.
2. "Here's the most likely type, with its probability, and underneath, the combined chance of the **top 3**, which is how we measure the model."
3. "And here's the full ranked list."
4. Tick **Domestic** and predict again: "Notice how the answer changes. Battery jumps to the top, at about 56%, because domestic incidents are mostly battery." (Without Domestic, the top type is Motor Vehicle Theft at about 25%.)
5. Type **ward 99**: "Invalid input gives a clear error. The system doesn't guess."
6. *(If there's time:)* open the **Dashboard**: "Here are the model's test results and real statistics from the dataset."

**Slide 10 – Business value and responsible use**
- "This gives **faster categorisation**, **data-driven insight** into time and place, and context for analysts, and it can grow with more data and retraining."
- "But it's **decision support, not automated policing**. A person always stays in the loop, and the severity level and suggested actions are simple rules, not model outputs."
- "Thank you. We're happy to take questions."

---

### If someone asks "why only 38%?" (anyone can answer)
"There are 31 crime types, so guessing gets about 22%. Our app shows a ranked list, and the right answer is in the top 3 for 68% of cases. Some types, like assault and battery, can't be told apart from time and place alone."
