-- ============================================================
-- Additional flight routes
-- ============================================================
INSERT INTO flight_routes (origin, destination, flight_minutes) VALUES
('SNA', 'ITM', 650),   -- Osaka Itami (Hakuba via train)
('SNA', 'MUC', 685),   -- Munich (Austria resorts)
('SNA', 'VCE', 700),   -- Venice (Dolomites/Cortina)
('LAX', 'ITM', 635),
('LAX', 'MUC', 670),
('LAX', 'VCE', 685);


-- ============================================================
-- Japan (additional) — LONG tier (8+ day trips)
-- ============================================================
INSERT INTO resorts (name, slug, country, region, continent, lat, lon, elevation_base_m, elevation_summit_m, nearest_airport, airport_drive_minutes, season_start_month, season_end_month, avg_annual_snowfall_cm, difficulty_mix, terrain_tags, vibe_tags, budget_tier, pass_affiliations, agent_notes) VALUES

('Furano', 'furano', 'JP', 'Hokkaido', 'asia', 43.3536, 142.3794, 237, 1077, 'CTS', 130, 12, 3, 1100,
 '{"beginner":30,"intermediate":40,"advanced":25,"expert":5}',
 '{powder,trees,groomers}', '{quiet,authentic,cultural,family,uncrowded}',
 'mid', '{}',
 'More relaxed and far less crowded than Niseko. Famous for dry Hokkaido powder and beautiful birch tree runs. Furano town is a real Japanese town (not a tourist village) with excellent ramen and local izakayas. Pairs well with a Niseko leg for a powder-tour week. 2.5hr from CTS by express bus.'),

('Rusutsu Resort', 'rusutsu', 'JP', 'Hokkaido', 'asia', 42.7437, 140.9075, 208, 994, 'CTS', 90, 12, 3, 1270,
 '{"beginner":15,"intermediate":45,"advanced":30,"expert":10}',
 '{powder,trees,variety}', '{resort-town,powder-focused,family,accessible}',
 'premium', '{}',
 'Japan''s best-kept secret. Three interconnected mountains with exceptional tree runs and consistent Hokkaido champagne powder. The Rusutsu Resort Hotel has 5 restaurants and an indoor amusement park — great for families. 1.5hr from CTS. Often overlooked in favor of Niseko but arguably has better tree skiing and far shorter lift lines.'),

('Nozawa Onsen', 'nozawa', 'JP', 'Nagano', 'asia', 36.9247, 138.4523, 585, 1650, 'NRT', 210, 12, 3, 900,
 '{"beginner":20,"intermediate":45,"advanced":25,"expert":10}',
 '{powder,trees,variety}', '{cultural,village,authentic,onsen,family}',
 'mid', '{}',
 'One of Japan''s most traditional ski onsen towns — a real village (not a resort) with 13 free public outdoor hot spring baths on the streets. Sea of Japan weather systems dump reliable powder. 3.5hr from Tokyo Narita via shinkansen to Iiyama + bus. Pairs perfectly with a few days in Tokyo. Less crowded than Hakuba, more authentically Japanese.'),

('Myoko Kogen', 'myoko', 'JP', 'Niigata', 'asia', 36.8897, 138.1089, 680, 1855, 'NRT', 175, 12, 3, 1200,
 '{"beginner":25,"intermediate":40,"advanced":25,"expert":10}',
 '{powder,trees,backcountry}', '{authentic,local,powder-focused,adventure,cultural}',
 'budget', '{}',
 'Off the beaten path for foreign tourists — a cluster of 10+ small resorts in the Niigata mountains with some of Japan''s deepest snowfall totals. Local farmers run family guesthouses (minpaku). 2.5hr from Tokyo by shinkansen + bus. Great for powder hunters who want to avoid Niseko crowds and prices without sacrificing snow quality.');


-- ============================================================
-- Europe (additional) — LONG/EXPEDITION tier
-- ============================================================
INSERT INTO resorts (name, slug, country, region, continent, lat, lon, elevation_base_m, elevation_summit_m, nearest_airport, airport_drive_minutes, season_start_month, season_end_month, avg_annual_snowfall_cm, difficulty_mix, terrain_tags, vibe_tags, budget_tier, pass_affiliations, agent_notes) VALUES

('St. Anton am Arlberg', 'st-anton', 'AT', 'Tyrol', 'europe', 47.1295, 10.2677, 1304, 2811, 'MUC', 185, 12, 4, 850,
 '{"beginner":10,"intermediate":30,"advanced":40,"expert":20}',
 '{powder,steep,off-piste,backcountry,variety}', '{après-ski,expert,adventure,authentic,party,village}',
 'premium', '{}',
 'The best ski village in Austria. Part of Ski Arlberg — largest connected ski area in Austria (305km, 88 lifts). World-class off-piste terrain and legendary après-ski at the Mooserwirt and Krazy Kanguruh. Serious skiers'' mountain with a genuine alpine village atmosphere. 3hr drive from Munich airport. More affordable than Swiss alternatives with comparable or better off-piste terrain.'),

('Kitzbühel', 'kitzbuehel', 'AT', 'Tyrol', 'europe', 47.4458, 12.3917, 762, 2000, 'MUC', 155, 12, 4, 500,
 '{"beginner":15,"intermediate":40,"advanced":35,"expert":10}',
 '{groomers,steep,variety,scenery}', '{luxury,authentic,village,cultural,après-ski,celebrity}',
 'luxury', '{}',
 'The most iconic ski town in Austria — a medieval walled town with a ski history going back to 1893. Home of the Hahnenkamm downhill, the most prestigious race on the World Cup calendar. Charming cobblestone streets, designer boutiques, and excellent food. Snow reliability is moderate at lower elevation but the town experience is unmatched in Europe. 2.5hr from Munich airport.'),

('Ischgl', 'ischgl', 'AT', 'Tyrol', 'europe', 46.9892, 10.2922, 1377, 2872, 'MUC', 205, 12, 4, 700,
 '{"beginner":5,"intermediate":40,"advanced":40,"expert":15}',
 '{powder,variety,glacier,off-piste}', '{party,après-ski,resort-town,luxury}',
 'premium', '{}',
 'Europe''s party capital on snow. Famous for season-closing concerts with artists like Elton John and Taylor Swift. Part of the Silvretta Arena (185km) connected to duty-free Samnaun in Switzerland. High altitude (top at 2,872m) ensures excellent snow all season. The après-ski rivals Ibiza in intensity. 3.5hr drive from Munich airport. For those who want elite skiing and elite nightlife in one place.'),

('Courchevel 1850', 'courchevel', 'FR', 'Auvergne-Rhône-Alpes', 'europe', 45.4147, 6.6347, 1300, 3230, 'GVA', 165, 12, 4, 850,
 '{"beginner":10,"intermediate":35,"advanced":40,"expert":15}',
 '{powder,luxury,variety,glacier,groomers}', '{luxury,celebrity,après-ski,resort-town,world-class}',
 'luxury', '{}',
 'The crown jewel of Les Trois Vallées — the world''s largest ski area with 600km of connected pistes across Courchevel, Méribel, and Val Thorens. Courchevel 1850 has the highest concentration of Michelin-starred restaurants and private chalets of any ski resort in the world. You can ski across three resorts in a single day. 2.5hr from Geneva airport.'),

('St. Moritz', 'st-moritz', 'CH', 'Graubünden', 'europe', 46.4908, 9.8443, 1822, 3057, 'ZRH', 200, 12, 4, 625,
 '{"beginner":15,"intermediate":40,"advanced":35,"expert":10}',
 '{glacier,scenery,luxury,groomers,variety}', '{luxury,celebrity,iconic,cultural,scenery}',
 'luxury', '{}',
 'The original ski resort — St. Moritz invented alpine winter tourism in the 1860s. The Engadin valley setting is extraordinary. Corvatsch glacier ensures a long season and reliable snow. Unique attractions include the Cresta Run (skeleton toboggan) and polo on the frozen lake. Switzerland is expensive — plan your budget accordingly. 3.5hr from Zurich by scenic train (Glacier Express) or car.'),

('Cortina d''Ampezzo', 'cortina', 'IT', 'Veneto', 'europe', 46.5355, 12.1357, 1224, 2930, 'VCE', 175, 12, 3, 500,
 '{"beginner":25,"intermediate":45,"advanced":25,"expert":5}',
 '{scenery,groomers,variety}', '{luxury,scenery,cultural,village,foodie,iconic}',
 'premium', '{}',
 'The "Queen of the Dolomites" — arguably the most scenic ski resort on Earth. UNESCO World Heritage Dolomite spires create an otherworldly backdrop of pink-tinged rock. Italian culture means world-class food and effortless style. Host city of the 2026 Winter Olympics. Part of Dolomiti Superski (1,200km of connected runs). Snow reliability is moderate. 3hr drive from Venice airport.');
