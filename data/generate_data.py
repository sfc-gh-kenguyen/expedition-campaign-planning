"""
Generates the messy Meridian Stay campaign exports used in the Day 2 lab.

Three source systems, each with its own conventions (and its own mistakes):
  - paid_media_export.csv        Ad platforms: YYYY-MM-DD dates, lowercase channels, currency-formatted budgets
  - email_sms_export.csv         Email & SMS platform: MM/DD/YYYY dates, 'Email'/'SMS', numeric budgets
  - crm_campaigns_export.csv     CRM campaign object: 'Mon DD, YYYY' dates, mixed status values

Planted problems the lab cleans up:
  1. Channel, region, and audience labels vary by system (e.g. 'fb_ads' vs 'Paid Social').
  2. Three different date formats.
  3. Budgets stored as text like "$65,000".
  4. The CRM re-lists the biggest paid campaigns (cross-system duplicates).
  5. Two rows in the paid export are exact re-export duplicates.
  6. One CRM campaign is 'Cancelled' and would create a false collision if not filtered out.

The plan covers November 2026 through January 2027. After cleaning there are 27 campaigns and exactly nine
audience collisions (same region + audience, overlapping dates, different campaigns) with $557,500 of combined
budget; five of them are in November. Run this script to regenerate the CSVs.
"""

import csv
import os
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))

# Canonical campaign plan: (name, owner_team, channel, region, audience, start, end, budget_usd)
CAMPAIGNS = [
    ("Thanksgiving Getaway Sale", "Brand Marketing", "Paid Social", "North America", "Leisure Travelers", "2026-11-02", "2026-11-22", 65000),
    ("Autumn Weekend Escapes", "Lifecycle Marketing", "Email", "North America", "Leisure Travelers", "2026-11-09", "2026-11-23", 12000),
    ("Business Travel Year-End Push", "Demand Gen", "Paid Search", "North America", "Business Travelers", "2026-11-01", "2026-11-30", 80000),
    ("Road Warrior Rewards", "Loyalty", "Email", "North America", "Business Travelers", "2026-11-16", "2026-11-30", 9000),
    ("Summit Series: Corporate Retreats", "Demand Gen", "Paid Search", "North America", "Meeting Planners", "2026-11-03", "2026-11-24", 40000),
    ("London Festive Stays", "EMEA Marketing", "Display", "EMEA", "Leisure Travelers", "2026-11-15", "2026-12-31", 55000),
    ("EMEA Winter Sun", "EMEA Marketing", "Email", "EMEA", "Leisure Travelers", "2026-12-01", "2026-12-20", 8000),
    ("Paris Business Hubs", "EMEA Marketing", "Paid Search", "EMEA", "Business Travelers", "2026-11-02", "2026-11-27", 30000),
    ("Singapore Staycation Deals", "APAC Marketing", "Paid Social", "APAC", "Families", "2026-12-05", "2026-12-27", 35000),
    ("Tokyo Cherry Blossom Preview", "APAC Marketing", "Paid Social", "APAC", "Leisure Travelers", "2027-01-05", "2027-01-25", 25000),
    ("APAC Year-End Flash Sale", "APAC Marketing", "SMS", "APAC", "Families", "2026-12-20", "2026-12-31", 5000),
    ("Sydney Summer Kickoff", "APAC Marketing", "Display", "APAC", "Leisure Travelers", "2027-01-10", "2027-01-31", 30000),
    ("Black Friday Mega Sale", "Brand Marketing", "Paid Social", "North America", "Loyalty Members", "2026-11-20", "2026-11-30", 90000),
    ("Loyalty Double Points Month", "Loyalty", "Email", "North America", "Loyalty Members", "2026-11-01", "2026-11-30", 7000),
    ("Cyber Monday Extension", "Lifecycle Marketing", "SMS", "North America", "Loyalty Members", "2026-12-01", "2026-12-03", 3000),
    ("Holiday Family Getaways", "Brand Marketing", "Display", "North America", "Families", "2026-12-01", "2026-12-24", 45000),
    ("New Year Escapes", "Lifecycle Marketing", "Email", "North America", "Leisure Travelers", "2026-12-26", "2027-01-10", 6000),
    ("LATAM Beach Resorts Launch", "LATAM Marketing", "Paid Social", "LATAM", "Leisure Travelers", "2026-11-15", "2026-12-15", 28000),
    ("Mexico City Business Weekends", "LATAM Marketing", "Paid Search", "LATAM", "Business Travelers", "2026-12-01", "2026-12-20", 15000),
    ("Brand Awareness: Meridian Moments", "Brand Marketing", "Display", "Global", "All Guests", "2026-11-01", "2027-01-31", 120000),
    ("EMEA Loyalty Welcome Series", "Loyalty", "Email", "EMEA", "Loyalty Members", "2026-11-01", "2027-01-31", 4000),
    ("APAC Business Rewards", "APAC Marketing", "Email", "APAC", "Business Travelers", "2026-11-10", "2026-11-24", 3500),
    ("Spring Break Early Bird", "Lifecycle Marketing", "Email", "North America", "Families", "2027-01-05", "2027-01-20", 5000),
    ("Winter Wellness Retreats", "Brand Marketing", "Paid Social", "EMEA", "Wellness Seekers", "2026-11-20", "2026-12-10", 22000),
]

# Per-system label conventions (the "mess")
PAID_CHANNEL = {"Paid Social": ["fb_ads", "meta", "paid_social"], "Paid Search": ["google_ads", "sem"], "Display": ["display", "programmatic"]}
PAID_REGION = {"North America": ["NA", "north america"], "EMEA": ["emea", "EMEA"], "APAC": ["apac"], "LATAM": ["latam"], "Global": ["global"]}
PAID_AUDIENCE = {
    "Leisure Travelers": ["leisure", "leisure_travelers"], "Business Travelers": ["business", "biz_travel"],
    "Families": ["families", "family"], "Loyalty Members": ["loyalty"], "Meeting Planners": ["meeting_planners"],
    "All Guests": ["all"], "Wellness Seekers": ["wellness"],
}
EMAIL_CHANNEL = {"Email": "Email", "SMS": "SMS"}
EMAIL_REGION = {"North America": "US & Canada", "EMEA": "Europe/ME/Africa", "APAC": "Asia Pacific", "LATAM": "Latin America"}
EMAIL_AUDIENCE = {
    "Leisure Travelers": "Leisure Segment", "Business Travelers": "Corporate Segment", "Families": "Family Segment",
    "Loyalty Members": "Meridian Rewards Members", "Wellness Seekers": "Wellness Segment",
}
CRM_CHANNEL = {"Paid Social": "Social Media", "Paid Search": "Search Engine Marketing", "Display": "Display Advertising", "Email": "Email Marketing", "SMS": "Text Messaging"}
CRM_REGION = {"North America": "N. America", "EMEA": "Europe", "APAC": "Asia-Pacific", "LATAM": "Latin America", "Global": "Worldwide"}
CRM_AUDIENCE = {
    "Leisure Travelers": "Leisure", "Business Travelers": "Business", "Families": "Family Travelers",
    "Loyalty Members": "Rewards Members", "Meeting Planners": "Event Planners", "All Guests": "All",
    "Wellness Seekers": "Wellness",
}


def d(s):
    return date.fromisoformat(s)


def fmt_crm(dt):
    return dt.strftime("%b %d, %Y")


def pick(options, i):
    return options[i % len(options)]


def write_csv(name, header, rows):
    path = os.path.join(HERE, name)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")


def main():
    paid, email, crm = [], [], []
    for i, (name, team, channel, region, audience, start, end, budget) in enumerate(CAMPAIGNS):
        s, e = d(start), d(end)
        if channel in PAID_CHANNEL:
            paid.append([
                f"PM-{1001 + i}", name, pick(PAID_CHANNEL[channel], i), pick(PAID_REGION[region], i),
                pick(PAID_AUDIENCE[audience], i), s.isoformat(), e.isoformat(), f"${budget:,}", team,
            ])
        else:
            email.append([
                f"ES-{501 + i}", name, EMAIL_CHANNEL[channel], EMAIL_REGION[region], EMAIL_AUDIENCE[audience],
                s.strftime("%m/%d/%Y"), e.strftime("%m/%d/%Y"), budget, team,
            ])

    # Planted problem 5: exact re-export duplicates in the paid media file
    paid.append(list(paid[0]))
    paid.append(list(paid[5]))

    # Planted problem 4: the CRM re-lists the largest paid campaigns (with trailing spaces / different casing)
    crm_dupes = [
        ("Thanksgiving Getaway Sale ", "Paid Social", "North America", "Leisure Travelers", "2026-11-02", "2026-11-22", 65000, "Active"),
        ("BLACK FRIDAY MEGA SALE", "Paid Social", "North America", "Loyalty Members", "2026-11-20", "2026-11-30", 90000, "Planned"),
        ("Brand Awareness: Meridian Moments", "Display", "Global", "All Guests", "2026-11-01", "2027-01-31", 120000, "Active"),
    ]
    # CRM-only campaigns (partner programs that only live in the CRM)
    crm_only = [
        ("Amex Travel Partner Promo", "Email", "North America", "Business Travelers", "2026-11-09", "2026-11-23", 0, "Planned"),
        ("Holiday Gift Card Push", "Email", "North America", "Families", "2026-12-05", "2026-12-20", 2500, "Planned"),
        # Planted problem 6: cancelled campaign that would falsely collide with Thanksgiving Getaway Sale / Autumn Weekend Escapes
        ("Veterans Day Weekend Blitz", "Paid Social", "North America", "Leisure Travelers", "2026-11-06", "2026-11-11", 18000, "Cancelled"),
        ("Tokyo Business District Launch", "Paid Search", "APAC", "Business Travelers", "2027-01-11", "2027-01-25", 20000, "Draft"),
    ]
    for j, (name, channel, region, audience, start, end, budget, status) in enumerate(crm_dupes + crm_only):
        crm.append([
            f"CRM-{7001 + j}", name, CRM_CHANNEL[channel], CRM_REGION[region], CRM_AUDIENCE[audience],
            fmt_crm(d(start)), fmt_crm(d(end)), budget, status, "Salesforce",
        ])

    write_csv(
        "paid_media_export.csv",
        ["ad_campaign_id", "campaign_name", "platform_channel", "geo", "target_audience", "flight_start", "flight_end", "budget", "owner"],
        paid,
    )
    write_csv(
        "email_sms_export.csv",
        ["program_id", "program_name", "channel_type", "region_name", "segment", "send_start", "send_end", "budget_usd", "team"],
        email,
    )
    write_csv(
        "crm_campaigns_export.csv",
        ["crm_campaign_id", "campaign_title", "campaign_type", "territory", "audience_group", "start_date", "end_date", "budgeted_cost", "status", "source_system"],
        crm,
    )


if __name__ == "__main__":
    main()
