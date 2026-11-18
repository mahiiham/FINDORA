"""Sample data for the MIET demo. Pure data only (no Flask imports) so it is easy to edit.
Coordinates are APPROXIMATE sample values - set the real ones in Admin > Locations."""

ORG = 'Meerut Institute of Engineering and Technology'

CAMPUS_CENTER = (29.0160, 77.6740)
LOCATIONS = [  # name, lat offset, lng offset
    ('Main Library', 0.0006, -0.0008), ('Central Cafeteria', -0.0004, 0.0006), ('Admin Block', 0.0010, 0.0002),
    ('Academic Block A', 0.0002, -0.0016), ('Academic Block B', -0.0008, -0.0010), ('Computer Centre', 0.0012, -0.0006),
    ('Sports Ground', -0.0016, 0.0014), ('Parking Area', -0.0010, 0.0024),
]

CATEGORIES = ['Electronics', 'Mobile Phone', 'Laptop', 'Wallet', 'ID Card', 'Keys', 'Bag', 'Books', 'Documents', 'Jewelry',
              'Clothing', 'Accessories', 'Glasses', 'Water Bottle', 'Umbrella', 'Stationery', 'Other']

USERS = [  # name, email, phone
    ('Aarav Sharma', 'user1@findora-demo.com', '9000000001'), ('Meera Gupta', 'user2@findora-demo.com', '9000000002'),
    ('Rohan Verma', 'user3@findora-demo.com', '9000000003'), ('Priya Singh', 'user4@findora-demo.com', '9000000004'),
    ('Aditya Mishra', 'user5@findora-demo.com', '9000000005'),
]
USER_PASSWORD = 'Demo1234'
ADMIN = ('MIET Admin', 'admin@findora-demo.com', 'Admin1234')

ITEMS = [
 dict(key='bag_l', type='LOST', title='Red backpack with laptop sleeve', desc='Red backpack with a padded laptop sleeve, lost after the evening study session.', cat='Bag', loc='Main Library', owner=0, color='Red', brand='Wildcraft', model='', feat='Blue keychain on the main zip', days=2, photo='bag_lost', private='Inside are a blue notebook with the MIET logo and a laptop charger.', gps=True),
 dict(key='bag_f', type='FOUND', title='Red backpack found near the library', desc='Red backpack with a laptop sleeve found on a bench outside the library.', cat='Bag', loc='Main Library', owner=1, color='Red', brand='Wildcraft', model='', feat='Blue keychain on the main zip', days=1, photo='bag_found', private='It contains a blue notebook and a laptop charger.', gps=True),
 dict(key='keys_l', type='LOST', title='Hostel and bike keys with red tag', desc='Bunch of two keys with a red rubber tag, dropped near the parking area.', cat='Keys', loc='Parking Area', owner=0, color='Silver', brand='', model='', feat='Red rubber tag with two keys', days=3, photo='keys_lost', private='The red tag has the initials AS written in black marker.', gps=True),
 dict(key='keys_f', type='FOUND', title='Set of keys with a red tag', desc='Silver keys on a red rubber tag found beside the parking area gate.', cat='Keys', loc='Parking Area', owner=1, color='Silver', brand='', model='', feat='Red rubber tag with two keys and a small bike key', days=2, photo='keys_found', private='The tag says AS in black marker.', gps=True),
 dict(key='bottle_l', type='LOST', title='Blue sipper bottle', desc='Blue steel sipper bottle left on the bleachers after practice.', cat='Water Bottle', loc='Sports Ground', owner=0, color='Blue', brand='Milton', model='', feat='Football sticker on the cap', days=4, photo='bottle_lost', private='There is a football sticker on the cap.', gps=False),
 dict(key='purse_f', type='FOUND', title='Pink coin purse', desc='Small pink coin purse with a clasp found on a cafeteria table.', cat='Wallet', loc='Central Cafeteria', owner=1, color='Pink', brand='', model='', feat='Metal clasp', days=1, photo='wallet_found', private='It holds a hundred rupee note and a bus pass.', gps=False),
 dict(key='pouch_l', type='LOST', title='Yellow zip pouch used as wallet', desc='Yellow zipped pouch that I use as a wallet, probably left at the cafeteria counter.', cat='Wallet', loc='Central Cafeteria', owner=2, color='Yellow', brand='', model='', feat='Zip with a tiny red puller', days=2, photo='wallet_lost', private='Contains a library card and two fifty rupee notes.', gps=True),
 dict(key='phone_l', type='LOST', title='Black smartphone with cracked corner', desc='Black Samsung smartphone with a blue case, lost during the afternoon lecture.', cat='Mobile Phone', loc='Academic Block A', owner=2, color='Black', brand='Samsung', model='Galaxy M31', feat='Crack on the top right corner, blue case', days=3, photo='phone_lost', private='The lock screen wallpaper is a cricket stadium.', gps=True),
 dict(key='phone_f', type='FOUND', title='Samsung phone with blue cover', desc='Black Samsung phone with a blue cover found under a desk in a classroom.', cat='Mobile Phone', loc='Academic Block A', owner=3, color='Black', brand='Samsung', model='Galaxy M31', feat='Blue cover, cracked top corner', days=2, photo='phone_found', private='The wallpaper shows a stadium.', gps=True),
 dict(key='id_l', type='LOST', title='MIET student ID card', desc='Student identity card with a red background photo, lost near the admin block.', cat='ID Card', loc='Admin Block', owner=3, color='White', brand='', model='', feat='Photo has a red background', days=4, photo='id_lost', private='The photo has a red background and the card holder wears glasses.', gps=False),
 dict(key='id_f', type='FOUND', title='ID card found near the cafeteria', desc='Student identity card found on the floor near the cafeteria entrance.', cat='ID Card', loc='Central Cafeteria', owner=4, color='White', brand='', model='', feat='Card with a blue strip', days=3, photo='id_found', private='The card holder is wearing glasses.', gps=False),
 dict(key='glass_l', type='LOST', title='Prescription glasses with brown frame', desc='Brown frame prescription glasses in a black case, lost in the library reading room.', cat='Glasses', loc='Main Library', owner=4, color='Brown', brand='', model='', feat='Small scratch on the left arm', days=2, photo='glasses_lost', private='The left arm has a small scratch.', gps=True),
 dict(key='glass_f', type='FOUND', title='Brown frame spectacles', desc='Pair of brown frame spectacles found on a table in the academic block.', cat='Glasses', loc='Academic Block B', owner=0, color='Brown', brand='', model='', feat='Scratch on the left arm', days=1, photo='glasses_found', private='There is a scratch on the left arm.', gps=True),
 dict(key='books_l', type='LOST', title='Engineering Physics textbook', desc='Engineering Physics textbook with a red and blue cover left in a lecture hall.', cat='Books', loc='Academic Block B', owner=1, color='Red', brand='', model='', feat='Name written on page 3', days=5, photo='books_lost', private='My name is written inside on page 3.', gps=False),
 dict(key='umb_f', type='FOUND', title='Purple folding umbrella', desc='Purple folding umbrella found near the sports ground pavilion.', cat='Umbrella', loc='Sports Ground', owner=2, color='Purple', brand='', model='', feat='One bent spoke', days=1, photo='umbrella_found', private='One spoke is bent on the left side.', gps=True),
 dict(key='ruler_l', type='LOST', title='Geometry set square', desc='Transparent set square from a drawing instrument box.', cat='Stationery', loc='Academic Block A', owner=3, color='Green', brand='', model='', feat='Name sticker on the back', days=6, photo='ruler_lost', private='A name sticker is on the back.', gps=False),
 dict(key='watch_f', type='FOUND', title='Brown strap wrist watch', desc='Analog wrist watch with a brown leather strap found in the cafeteria.', cat='Accessories', loc='Central Cafeteria', owner=4, color='Brown', brand='', model='', feat='Round white dial', days=1, photo='watch_found', private='There is an engraving AK on the back.', gps=True),
 dict(key='ring_l', type='LOST', title='Gold ring with small stone', desc='Thin gold ring with a small clear stone lost near the computer centre.', cat='Jewelry', loc='Computer Centre', owner=1, color='Gold', brand='', model='', feat='Initials engraved inside the band', days=2, photo=None, private='Initials are engraved inside the band.', gps=False),
 dict(key='hood_f', type='FOUND', title='Grey hooded sweatshirt', desc='Grey hooded sweatshirt left on a chair in the library.', cat='Clothing', loc='Main Library', owner=2, color='Grey', brand='', model='', feat='Small tear on the left pocket', days=1, photo=None, private='The left pocket has a small tear.', gps=False),
 dict(key='lap_l', type='LOST', title='Black Dell laptop in sleeve', desc='Black Dell laptop inside a black sleeve, forgotten in the computer centre this morning.', cat='Laptop', loc='Computer Centre', owner=3, color='Black', brand='Dell', model='Inspiron 15', feat='Sticker of a gear on the lid', days=0, hours=3, photo=None, private='A gear sticker is on the lid and the wallpaper is a mountain.', gps=True),
 dict(key='lap_f', type='FOUND', title='Dell laptop in a black sleeve', desc='Black Dell laptop with a sleeve found on a workstation in the computer centre.', cat='Laptop', loc='Computer Centre', owner=0, color='Black', brand='Dell', model='Inspiron 15', feat='Gear sticker on the lid', days=0, hours=2, photo=None, private='There is a gear sticker on the lid.', gps=True),
]

CLAIMS = [
 dict(key='c_bag', item='bag_f', claimant=0, answer='It has a blue notebook with the MIET logo and a laptop charger inside.', status='PENDING', note=None),
 dict(key='c_keys', item='keys_f', claimant=0, answer='The red tag has the letters AS written in black marker.', status='APPROVED', note='Initials AS matched the private detail exactly.'),
 dict(key='c_phone', item='phone_f', claimant=2, answer='The wallpaper on the lock screen is a cricket stadium.', status='APPROVED', note='Wallpaper matched. Phone handed over at the Admin Block desk.'),
 dict(key='c_id', item='id_f', claimant=3, answer='It is a plain white card with a green strip.', status='REJECTED', note='Answer did not match the private detail. Claim rejected.'),
 dict(key='c_purse', item='purse_f', claimant=2, answer='It is a small wallet with some money in it.', status='PENDING', note=None),
 dict(key='c_lap', item='lap_f', claimant=3, answer='A gear sticker on the lid and a mountain wallpaper.', status='PENDING', note=None),
]
RETURNED_ITEMS = ['phone_l', 'phone_f']

HIDDEN = '[hidden by Findora — contact details are not allowed in chat]'
CHATS = {
 'c_keys': [('claimant', 'Hi, I think these are my keys. They have a red tag.', False), ('reporter', 'Hello! What is written on the tag?', False),
            ('claimant', 'The letters AS. You can call me on ' + HIDDEN, True), ('reporter', 'Thanks, the admin approved it. Let us hand them over at the parking area office.', False),
            ('claimant', 'Great, I will be there at 4 pm.', False)],
 'c_bag': [('claimant', 'Hello, I lost a red backpack near the library yesterday. Is this yours?', False), ('reporter', 'I found it on a bench. Does it have a keychain?', False),
           ('claimant', 'Yes, a blue one on the main zip.', False)],
}

# anonymized chats between the OWNER of a lost report and the FINDER of the matching found report (no claim needed)
MATCH_CHATS = {  # only pairs at or above the match threshold exist, so these use the strongest sample matches
 'laptop': ('lap_l', 'lap_f', [('owner', 'Hello! I think the Dell laptop you found is mine. Is there a gear sticker on the lid?', False),
                                ('finder', 'Yes, there is a gear sticker on the lid. I left it at the Computer Centre desk.', False),
                                ('owner', 'Great, thank you! You can reach me on ' + HIDDEN, True),
                                ('finder', 'No problem. Please also file a claim so the admin can verify it.', False)]),
 'bag': ('bag_l', 'bag_f', [('owner', 'Hi, I lost a red backpack near the library. Does yours have a blue keychain on the zip?', False),
                           ('finder', 'Yes it does. It is safe with me, I will leave it at the library desk.', False)]),
}

# sample "last 6 hours" location trail for user1 (index 0): hours ago, location name
TRAIL = [(5.2, 'Academic Block B'), (4.6, 'Academic Block B'), (3.4, 'Central Cafeteria'), (2.1, 'Main Library'), (1.2, 'Main Library'), (0.4, 'Parking Area')]
