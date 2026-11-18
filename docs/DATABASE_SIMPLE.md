# The database in simple words

Think of the database as **one big Excel workbook**. Every sheet is a **table**; each row is one record
(one user, one report…); each column is one detail (name, title…). Findora uses **SQLite**, so the whole
workbook is a single file: `instance/findora.db`. Run `python seed.py` to refill it with sample data.

## The sheets (tables) and what they hold

| Table | One row is… | Important columns | Plain meaning |
|---|---|---|---|
| `organization` | the college | name | "Meerut Institute of Engineering and Technology" |
| `location` | a campus place | name, latitude, longitude | Library, Cafeteria… used for the map and risk |
| `category` | a kind of item | name | Bag, Keys, Wallet… (each has a sticker picture) |
| `user` | a person | name, email, **password_hash**, role | `USER` or `ADMIN`. The real password is never stored — only a scrambled hash |
| `item` | a lost or found **report** | item_type (LOST/FOUND), title, description, category, location, **image_path**, **reported_lat/lng**, status | The photo file name and the reporter's GPS position are stored here |
| `private_verification_detail` | the secret proof for one report | protected_details | Stored **encrypted**; only the admin can read it |
| `match` | one AI match | lost_item, found_item, score + 6 part-scores | Pairs that scored at least the threshold (80 % by default) |
| `match_log` | every pair the AI scored | score, **threshold**, passed (yes/no) | Includes the rejected pairs, so the admin can explain "why not matched" |
| `claim` | "this is mine" request | item, claimant, answer (encrypted), status | PENDING → APPROVED / REJECTED |
| `message` | one chat message on a claim | claim, sender, body, was_redacted | Anonymous chat after a claim |
| `match_message` | one chat message on a match | match, sender, body | **User-to-user** anonymous chat, no claim needed |
| `ticket` / `ticket_message` | a user↔admin conversation and its messages | subject, kind, status | The "Contact admin" channel |
| `notification` | an alert | user, title, message, **link** | The bell icon; `link` opens the chat/ticket |
| `location_ping` | one remembered position | user, lat, lng, location, time | The opt-in **6-hour trail**; auto-deleted, only the owner can read it |
| `flag` | "this report looks suspicious" | item, reporter, reason | Admin moderation queue |
| `audit_log` | a record of an important action | who, action, IP, time | Accountability |

## How the sheets connect (arrows = "belongs to")
```
user ──< item >── category          item >── location          item ──1 private_verification_detail
item ──< match >── item (lost + found)      match ──< match_message
item ──< claim >── user (claimant)          claim ──< message
user ──< ticket ──< ticket_message          user ──< notification          user ──< location_ping
```
`──<` means "one to many": one user has many reports; one claim has many messages.

## Where do the uploaded photos live?
Not in the database. The **file** goes into the `uploads/` folder (a full-size JPEG and a small `thumb_` copy);
the database only keeps the **file name** in `item.image_path`. Pages show `/items/uploads/<file name>`.
Phone photos are straightened (EXIF rotation) and re-saved as JPEG; reports without a photo show a category sticker.

## How is the location stored?
1. When you open *Report Lost/Found*, the browser asks permission. If you allow it, your position is placed in two
   hidden form fields and saved with the report as `item.reported_lat/lng` (shown in *My past locations*).
2. The report also stores the campus place you choose (`item.location_id`).
3. If you tick **Remember my location for 6 hours**, a point is saved every ~5 minutes in `location_ping`
   and deleted automatically after 6 hours.
4. **High-risk suggestions** are calculated from `item` rows only: for each campus place, how many LOST reports it has
   (and the busiest 2-hour window). The top places become the "be extra careful" list. No personal data is used.
