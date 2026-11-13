# (place, upazila, status, source_url, report_date, quote)
TBS = "https://www.tbsnews.net/bangladesh/floods-leave-over-75-lakh-people-marooned-ctg-1484941"
BSS = "https://www.bssnews.net/others/404930"
BD = "https://bdnews24.com/bangladesh/eda23461240f"
PA = "https://en.prothomalo.com/amp/story/bangladesh/7jbpk0qmji"
NONE = "no place-level flood report found (searched UN SitRep #1, NAWG 9 and 11 Jul, BDRCS 7 Jul, TBS, BSS, bdnews24, Prothom Alo, Daily Observer, Financial Express)"
q1 = "submerged large parts of ... unions (Sangu and Dolu rivers), 10 Jul"
q2 = "situation worsening in ... unions; ~50% of the upazila underwater, 10 Jul"
PLACES = [
 ("Bajalia", "Satkania", 1, TBS, "2026-07-10", q1), ("Keochia", "Satkania", 1, TBS, "2026-07-10", q1),
 ("Chadaha", "Satkania", 1, TBS, "2026-07-10", "at least five wards of the union were completely submerged"),
 ("Kaliaish", "Satkania", 1, TBS, "2026-07-10", q1), ("Dharmapur", "Satkania", 1, TBS, "2026-07-10", q1),
 ("Khagaria", "Satkania", 1, TBS, "2026-07-10", q1), ("Amilaish", "Satkania", 1, TBS, "2026-07-10", q1),
 ("Dhemsha", "Satkania", 1, TBS, "2026-07-10", q1), ("Nalua", "Satkania", 1, TBS, "2026-07-10", q1),
 ("Charati", "Satkania", 1, TBS, "2026-07-10", q1), ("Puranagar", "Satkania", 1, TBS, "2026-07-10", q1),
 ("Satkania Municipality", "Satkania", 1, BD, "2026-07-10", "Satkania Municipality, Dhemsha and Bajalia among the worst-hit areas"),
 ("Hasan Balipara", "Satkania", 1, PA, "2026-07-12", "photo of inundation taken in Hasan Balipara village on 12 July"),
 ("Baharchhara", "Banshkhali", 1, TBS, "2026-07-10", q2), ("Katharia", "Banshkhali", 1, TBS, "2026-07-10", q2),
 ("Gandamara", "Banshkhali", 1, TBS, "2026-07-10", q2), ("Shekherkhil", "Banshkhali", 1, TBS, "2026-07-10", q2),
 ("Saral", "Banshkhali", 1, TBS, "2026-07-10", q2), ("Chhanua", "Banshkhali", 1, TBS, "2026-07-10", q2),
 ("Khankhanabad", "Banshkhali", 1, TBS, "2026-07-10", q2), ("Gunagari", "Banshkhali", 1, TBS, "2026-07-10", q2),
 ("Napora", "Banshkhali", 1, BD, "2026-07-10", "among the worst-hit unions"), ("Bailchhari", "Banshkhali", 1, BD, "2026-07-10", "among the worst-hit unions"),
 ("Amirabad", "Lohagara", 1, BD, "2026-07-10", "Amirabad, Adhunagar, Padua and Lohagara unions have been hit, with Amirabad suffering the most"),
 ("Adhunagar", "Lohagara", 1, BD, "2026-07-10", "unions have been hit"), ("Padua", "Lohagara", 1, BD, "2026-07-10", "unions have been hit"),
 ("Lohagara", "Lohagara", 1, BD, "2026-07-10", "unions have been hit"),
] + [(p, u, 0, NONE, "", "") for p, u in [
 ("Maitbhanga", "Sandwip"), ("Musapur", "Sandwip"), ("Haramia", "Sandwip"), ("Santoshpur", "Sandwip"), ("Gachhua", "Sandwip"), ("Bauria", "Sandwip"),
 ("Zorarganj", "Mirsharai"), ("Mithanala", "Mirsharai"), ("Durgapur", "Mirsharai"), ("Katachhara", "Mirsharai"), ("Hinguli", "Mirsharai"), ("Wahedpur", "Mirsharai"), ("Mayani", "Mirsharai"),
 ("Barabkunda", "Sitakunda"), ("Kumira", "Sitakunda"), ("Bhatiari", "Sitakunda"), ("Muradpur", "Sitakunda"), ("Saidpur", "Sitakunda"),
 ("Gahira", "Raozan"), ("Noapara", "Raozan"), ("Binajuri", "Raozan"), ("Kadalpur", "Raozan"), ("Bagoan", "Raozan"),
]]
