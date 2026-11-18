# Testing steps — user interface and admin console

Prepare once: `python seed.py` then `python run.py` → http://127.0.0.1:5000
(use a normal and a private browser window so you can be a user and the admin at the same time).

## A. User interface (log in as `user1@findora-demo.com` / `Demo1234`)

1. **Background and branding** — the MIET campus photo is behind every page; the header shows
   "FINDORA · Meerut Institute of Engineering and Technology". Open the palette icon and switch Dark / Light / Aurora / Sunset.
2. **Dashboard** (`Dashboard`) — five counters, then *My report dashboard* with **Lost by me** / **Found by me** cards.
   Cards with an uploaded photo show it (camera badge); the laptop report has no photo, so it shows its **Laptop sticker**.
3. **AI matches** — the *AI matches for my reports* list shows percentages (only pairs at or above the 80 % threshold appear: backpack ≈ 82 %, keys ≈ 85 %, laptop ≈ 89 %). Click **Why?** → six score bars.
4. **Claims** — *My claims* shows the backpack claim (PENDING) and the keys claim (APPROVED); *Claims on my reports* shows claims from others as "Anonymous claimant".
5. **Past locations** — scroll to *My past locations*: a map with a marker per report (red = lost, green = found, bold outline = exact GPS) and a list with a **GPS** or **campus** tag.
6. **Search by category** — `Search` → click a category tile; every card shows photo or sticker and the category sticker chip.
7. **Report with auto location** — `Report Lost`: allow the browser location prompt. Expect the blue "You" dot, red/orange/green risk circles and the nearest location pre-selected
   (sample coordinates are near MIET; away from campus pick a location manually). Upload any photo, fill the form, submit.
   Then open your new report: the photo is shown large, and *Where it was lost* shows a map and "GPS stored".
8. **Duplicate warning** — submit the same report again: a yellow "looks similar" notice appears.
9. **Anonymized chat** — `Claims` → *Chat* on the keys claim: messages appear as Claimant / Reporter; one message shows a hidden phone number.
   Send "call me on 9876543210" → it is masked automatically.
10. **Contact admin (direct reporting)** — `Contact Admin` → choose *Direct report*, write a subject and message → **Send**. The thread appears under *My conversations*.
    Log in as user3 (`user3@findora-demo.com`) to see the admin's answer to "Why was my wallet not matched?".
11. **Alerts** — the bell shows unread alerts (matches, claim decisions, admin replies).

## A2. New in v7 — images, location, risk and chat (as `user1@findora-demo.com`)

12. **Uploaded photos** — `Report Lost`, choose a photo taken on a phone (up to 16 MB). Submit, then open the report: the photo is upright,
    the card on `Search`/`Dashboard` shows the thumbnail with a camera badge. If an image file is ever missing, the category sticker is shown instead.
13. **Location saved with the report** — on `Report Lost` allow location. The green line "Your device position (…) will be saved with this report" appears.
    Submit, then `Dashboard` → *My past locations*: your report has a **GPS** tag and the report page says "GPS stored".
    (Works even if the map cannot load. Use http://127.0.0.1:5000 or localhost — location is blocked on plain LAN IP addresses.)
14. **High-risk suggestions** — the report form shows "You are near … — High-risk spot: N lost reports, mostly 14:00-16:00" and a list
    *Where items go missing most often*; the same top spots appear on `Dashboard` → *Campus risk suggestions*.
15. **6-hour trail** — tick *Remember where I am for the next 6 hours*: *Where you were in the last 6 hours* fills in (sample data already has 6 points for user1);
    press **Use this place** to select that campus location; **Clear my trail** deletes it. Log in as user2 — user2 sees an empty trail (it is private).
16. **User ↔ user chat** — `Dashboard` → *AI matches* → chat icon (or `Why?` → **Message anonymously**). user1 is the *Finder* of the Dell laptop and the *Owner* of the red backpack, and both matches already have a conversation: messages are labelled "Owner (lost item)" / "Finder" and a phone number is shown as hidden.
    Send a message, then log in as `user4@findora-demo.com` (owner of the lost laptop): the bell shows an alert with an **Open** button that jumps into the same chat,
    and your message appears within ~4 seconds. A third user who opens the chat link gets "403 Forbidden".
17. **User ↔ admin** — `Contact Admin` → send; log in as admin → `User messages` → reply; back as the user, the bell shows "The admin replied" → **Open**.
    Admin can also start a conversation: `Users` → **Contact**.

## B. Admin console (log in as `admin@findora-demo.com` / `Admin1234` → you land on `/admin`)

1. **Layout** — left sidebar, top bar with **Meerut Institute of Engineering and Technology**, same campus background. Counters include *Pairs rejected* and the **AI threshold (80 %)**.
2. **All reports** — every lost and found report with photo/sticker, reporter, stored location (GPS or campus), **best AI score** and an outcome (*Matched* / *Below threshold*).
   Filter by type/status/keyword. Click **Open** for the full record: private proof, GPS, all scored pairs and claims.
3. **AI match log** — tabs *All / Matched / Rejected by threshold*. Open **Rejected**: the Samsung phone pair shows **76 % vs 80 %, gap −4 pts, Rejected**, and the yellow pouch vs pink purse about 44 % — each with the full score breakdown.
   This is the evidence to show a user who asks why their report did not match.
4. **Claims** — every claim with photo, claimant, owner, AI score/threshold and status. **Review** a PENDING claim (e.g. the laptop): see both private texts, the verification-confidence badge and the AI pairs table; **Approve** or **Reject** with a reason.
5. **User messages** — the inbox shows *Needs reply* items. Open "I handed a found watch to the admin desk", write a reply → status becomes *Answered* and the user gets an alert.
   The side panel shows the AI scores for the related report.
6. **Contact a user directly** — `Users` → **Contact** (or *Contact reporter* on a report) → send a message; it appears in the user's *Contact admin* page.
7. **Master data** — Categories, Locations (edit latitude/longitude), Organizations; **Flags** → resolve the open flag; **Audit log** → see every action with IP.
8. **Access control** — while logged in as a normal user, open `/admin` → you receive "403 Forbidden".

## C. Automated tests
`pytest` — covers registration/login, AI scoring, claims workflow, anonymized chat access, redaction, map data,
dashboards, admin console pages, logging of rejected AI pairs, direct admin contact and GPS storage.
