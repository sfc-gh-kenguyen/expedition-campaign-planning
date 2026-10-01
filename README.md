# Campaign Planning, Simplified: Build It with CoCo, Ask It with CoWork

Companion repo for the **Campaign Planning, Simplified** hands-on lab (Expedition, Day 2: Marketing / GTM).

In this 60-minute lab you help **Meridian Stay**, a fictional global hotel brand, answer a question every marketing team eventually asks:

> **Which of our campaigns are about to hit the same audience at the same time?**

You land messy campaign exports in open **Apache Iceberg** tables, clean and standardize them by prompting **Snowflake CoCo**, see the plan on a live campaign calendar, and then ask planning questions in plain language through a Cortex Agent in **Snowflake CoWork**.

## What's in this repo

| Path | What it is |
|---|---|
| **`lab.ipynb`** | The notebook you run. It walks through landing, cleaning, and collision detection cell by cell, with CoCo prompts shown inline. |
| **`data/`** | The three raw campaign exports (`paid_media_export.csv`, `email_sms_export.csv`, `crm_campaigns_export.csv`) and `generate_data.py`, which regenerates them. |
| **`campaign_calendar/streamlit_app.py`** | The pre-built campaign calendar app. You run it from the Workspace, then extend it with CoCo. |
| **`expedition-campaign-planning.md`** | The step-by-step guide. |
| **`README.md`** | This file. |

## What you'll build

**Land**
- Three raw **Snowflake-managed Iceberg tables**, one per source system, loaded with `COPY INTO` from an internal stage.

**Clean (with CoCo)**
- `CURATED.CAMPAIGNS`: 27 deduplicated campaigns in one standard vocabulary for channel, region, and audience, with real dates and budgets. Stored as Iceberg.
- `CURATED.CAMPAIGN_COLLISIONS`: every pair of campaigns that target the same region and audience on overlapping dates (9 collisions, $557,500 combined budget). Stored as Iceberg.

**See**
- A Streamlit campaign calendar, customized with CoCo to outline colliding campaigns in red.

**Ask** (done in the Snowsight UI; see the guide)
- A **Semantic View** created with Autopilot.
- A **Cortex Agent** backed by the Semantic View.
- **Snowflake CoWork**, where you ask questions like *"What's launching in APAC in December 2026?"*

## Data layers

| Schema | Contents |
|---|---|
| `MERIDIAN_STAY.RAW` | The three exports exactly as they arrived (Iceberg), plus the stage and file format |
| `MERIDIAN_STAY.CURATED` | `CAMPAIGNS` and `CAMPAIGN_COLLISIONS` (Iceberg) |
| `MERIDIAN_STAY.ANALYTICS` | `CAMPAIGN_PLANNING_SV` and `CAMPAIGN_PLANNING_AGENT` |

## What's messy in the source data (on purpose)

| Problem | Example |
|---|---|
| Different labels per system | `fb_ads` / `meta` / `Social Media` are all Paid Social; `NA` / `US & Canada` / `N. America` are all North America |
| Three date formats | `2026-10-05`, `10/12/2026`, `Oct 05, 2026` |
| Budgets stored as text | `"$65,000"` |
| Cross-system duplicates | The CRM re-lists *Fall Getaway Sale* (trailing space), *BLACK FRIDAY MEGA SALE*, and *Brand Awareness: Meridian Moments* |
| Re-export duplicates | Two paid media rows appear twice |
| A cancelled campaign | *Columbus Day Weekend Blitz* is cancelled in the CRM; left in, it causes two false collisions |

## Answer key

| Check | Expected |
|---|---|
| Rows loaded (ad platforms / email & SMS / CRM) | 16 / 10 / 7 |
| `CURATED.CAMPAIGNS` rows | 27 |
| Unmapped channel / region / audience / date / budget values | 0 |
| `CURATED.CAMPAIGN_COLLISIONS` rows | 9 |
| Combined budget across collisions | $557,500 |
| Region and audience with the most collisions | North America, Business Travelers (3, all in October 2026) |

## Prerequisites

- A free **Snowflake trial account** on **AWS** (Snowflake-managed Iceberg storage is available on AWS and Azure): [sign up here](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&trial=student&cloud=aws&region=us-east-2&utm_campaign=introtosnowflake&utm_cta=developer-guides).
- No coding experience required.

## How to run it

1. **Sign in** to Snowsight as **`ACCOUNTADMIN`**.
2. **Create a Git-backed Workspace**: *Projects » Workspaces » + » Create new Git workspace*, using this repo's URL. When prompted, create a Git API integration named `GITHUB_MERIDIAN_LAB` with this repo's GitHub organization as the allowed prefix, and check **Public repository**.
3. **Open `lab.ipynb`**, click **Connect → Create and connect**, and set Role = `ACCOUNTADMIN`, Warehouse = `COMPUTE_WH`.
4. **Run the cells top to bottom.** Where a markdown cell shows a CoCo prompt, open the **CoCo** panel, paste the prompt, compare the SQL with the expected output, and click **Allow**.
5. **Open `campaign_calendar/streamlit_app.py`** and click **Run**.
6. **Create the Semantic View and Cortex Agent, then ask your questions in CoWork**, following the *"Ask It With CoWork"* section of the guide.

## Regenerating the data

```bash
python3 data/generate_data.py
```

The script is deterministic, so it always produces the same three CSVs and the same answer key.

## Resources

- [Apache Iceberg™ tables in Snowflake](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [Git-backed Workspaces](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-git)
- [Streamlit in Snowflake in Workspaces](https://docs.snowflake.com/en/developer-guide/streamlit/streamlit-in-workspaces/streamlit-in-workspaces-overview)
- [Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic/sql) · [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage) · [Snowflake CoWork](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-cowork/getting-started)
