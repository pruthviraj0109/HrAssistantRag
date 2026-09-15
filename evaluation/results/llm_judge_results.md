# LLM-as-Judge Evaluation Results — 2026-09-11T16:16:14

**Average Faithfulness:** 4.56 / 5
**Average Relevance:** 4.78 / 5

## Q1 [direct]
**Question:** How many earned leaves are regular employees entitled to in a calendar year?
**Answer:** All regular employees are entitled to **18 earned leaves in a calendar year**【HR-Policy-new.pdf | Page: 4 | Chunk ID: recursive_b70e7e917f76】.
**Faithfulness:** 5/5 — The answer accurately reflects the information in the context without adding unsupported claims.
**Relevance:** 5/5 — It directly answers the question about the number of earned leaves for regular employees.

## Q2 [direct]
**Question:** What is the maximum number of casual leave days an employee can take in a calendar year?
**Answer:** The policy states that an employee can take up to **12 days of casual leave in a calendar year**【HR-Policy-new.pdf | Page: 4 | Chunk ID: recursive_bfec2576ecf0】.
**Faithfulness:** 5/5 — The answer accurately cites the context stating 12 days as the maximum casual leave.
**Relevance:** 5/5 — It directly answers the question about the maximum casual leave days.

## Q3 [hallucination_trap]
**Question:** How many days per week can an employee work from home?
**Answer:** I could not find this information in the available documents.
**Faithfulness:** 5/5 — The answer correctly states that the documents do not provide a specific number of work-from-home days, which is supported by the context.
**Relevance:** 4/5 — The answer directly addresses the question by indicating the lack of information, though it does not provide a specific number.

## Q4 [table]
**Question:** For Slab-5, what is the eligible travel mode and what are the listed allowance amounts?
**Answer:** **Slab 5 – Travel Policy**

| Item | Value |
|------|-------|
| **Eligible travel mode** | 3rd AC / AC Bus / Bike / Personal Car / Auto |
| **Hotel eligibility (Tier‑1)** | INR 1,250 |
| **Hotel eligibility (Tier‑2)** | INR 850 |
| **Hotel eligibility (Tier‑3)** | INR 750 |
| **Food allowance (Tier‑1)** | INR 590 |
| **Food allowance (Tier‑2)** | INR 530 |
| **Food allowance (Tier‑3)** | INR 420 |
| **Same‑day allowance** | INR 190 |

*Source: HR‑Policy‑new.pdf, travel‑policy section – “Slab ‑5” row (Chunk ID: recursive_afd394de46d2).*
**Faithfulness:** 1/5 — The answer provides details for Slab‑5, but the context contains no information about Slab‑5, making the claims unsupported.
**Relevance:** 4/5 — The answer directly addresses the question by listing a travel mode and allowance amounts, though the data is not sourced from the provided context.

## Q5 [follow_up]
**Question:** How many of those earned leaves can be carried forward to the next year?
**Answer:** The policy allows employees to carry forward up to **6 earned leaves** to the next calendar year【HR‑Policy‑new.pdf | Page: 5 | Chunk ID: recursive_3d7ac0bd11bd】.
**Faithfulness:** 5/5 — The answer states that employees can carry forward up to 6 earned leaves, which is directly supported by the context.
**Relevance:** 5/5 — The answer directly addresses the question about how many earned leaves can be carried forward to the next year.

## Q6 [multi_chunk]
**Question:** What are the leave credit rules for an employee who joins or is transferred during the month?
**Answer:** **Leave credit rules for an employee who joins or is transferred during the month**

| Joining / Transfer Date | Earned‑leave credit |
|-------------------------|---------------------|
| Before or on the **10th** of the month | **1.5 leaves** |
| Between the **11th and 18th** of the month | **1 leave** |
| After the **20th** of the month | **No credit** |

Additional notes:  
- Employees receive an extra **0.5 leave** on their birthday.  
- No paid leave is allowed for the first three months of employment.  
- No leave is allowed during a notice period.  
- All leaves are calculated from the employee’s date of joining.  

Source: HR‑Policy‑new.pdf, page 4, “Employee joining/transferred before or on 10th of the month: 1.5 Leaves …”【HR‑Policy‑new.pdf | Page: 4 | Chunk ID: recursive_d564ff0f03f3】.
**Faithfulness:** 5/5 — All claims in the answer are directly supported by the provided context.
**Relevance:** 5/5 — The answer directly addresses the leave credit rules for employees joining or transferring during the month.

## Q7 [direct]
**Question:** What are the normal working days and working hours of the company?
**Answer:** **Normal working days and hours**

- **Working days:** Monday through Saturday (Sunday is the weekly off).  
- **Working hours:** 9:30 am – 6:00 pm each day【HR‑Policy‑new.pdf | Page: 7 | Chunk ID: recursive_6b8103bd50cd】.
**Faithfulness:** 5/5 — All claims in the answer are directly supported by the provided context.
**Relevance:** 5/5 — The answer directly and completely addresses the question about normal working days and hours.

## Q8 [direct]
**Question:** How long is the lunch break and between what times can employees take it?
**Answer:** The policy allows **one hour of lunch break** each day.  
Employees may take this break **anytime between 1:00 pm and 2:00 pm** on a staggered schedule so that their absence does not disrupt colleagues【HR‑Policy‑new.pdf | Page: 8 | Chunk ID: recursive_24c92305bf72】.
**Faithfulness:** 5/5 — All claims in the answer are directly supported by the provided context.
**Relevance:** 5/5 — The answer directly answers the question about lunch break duration and timing.

## Q9 [direct]
**Question:** How many times in a month is flexi-entry allowed?
**Answer:** Employees may use flexi‑entry (arriving after 9:00 am) **only twice in a month**【HR‑Policy‑new.pdf | Page: 9 | Chunk ID: recursive_49a094326a77】.
**Faithfulness:** 5/5 — The answer states that flexi-entry is allowed twice a month, which is directly supported by the context.
**Relevance:** 5/5 — The answer directly answers the question about how many times flexi-entry is allowed in a month.
