-- ============================================================
-- Flight routes from SNA (Orange County) and LAX
-- ============================================================
INSERT INTO flight_routes (origin, destination, flight_minutes) VALUES
-- SNA origin
('SNA', 'SLC', 95),    -- Salt Lake City (Utah)
('SNA', 'DEN', 145),   -- Denver (Colorado)
('SNA', 'RNO', 90),    -- Reno (Tahoe)
('SNA', 'YVR', 150),   -- Vancouver (Whistler)
('SNA', 'YYC', 175),   -- Calgary (Banff/Lake Louise)
('SNA', 'NRT', 640),   -- Tokyo (Niseko/Hakuba)
('SNA', 'CDG', 690),   -- Paris (Chamonix, Val d'Isère)
('SNA', 'GVA', 680),   -- Geneva (Verbier, Zermatt)
('SNA', 'ZRH', 685),   -- Zurich (Zermatt, St. Moritz)
('SNA', 'AKL', 760),   -- Auckland (Queenstown, NZ)
('SNA', 'SCL', 600),   -- Santiago (Valle Nevado, Portillo)
-- LAX (often cheaper for international)
('LAX', 'SLC', 90),
('LAX', 'DEN', 140),
('LAX', 'RNO', 85),
('LAX', 'YVR', 145),
('LAX', 'YYC', 170),
('LAX', 'NRT', 620),
('LAX', 'CDG', 670),
('LAX', 'GVA', 665),
('LAX', 'ZRH', 670),
('LAX', 'AKL', 745),
('LAX', 'SCL', 585);


-- ============================================================
-- Resorts
-- ============================================================

-- SoCal (day trip / weekend tier)
INSERT INTO resorts (name, slug, country, region, continent, lat, lon, elevation_base_m, elevation_summit_m, nearest_airport, airport_drive_minutes, season_start_month, season_end_month, avg_annual_snowfall_cm, difficulty_mix, terrain_tags, vibe_tags, budget_tier, pass_affiliations, agent_notes) VALUES
('Big Bear Mountain', 'big-bear', 'US', 'California', 'north_america', 34.2359, -116.8914, 2073, 2664, 'ONT', 90, 12, 4, 127, '{"beginner":35,"intermediate":35,"advanced":20,"expert":10}', '{groomers,park,beginner-friendly}', '{family,weekend-getaway,accessible}', 'budget', '{ikon}', 'Closest ski area to LA/OC. Low snow reliability but convenient. Best for beginners and park riders. Works when everywhere else is full. 2hr drive from OC.'),

('Snow Summit', 'snow-summit', 'US', 'California', 'north_america', 34.2390, -116.8914, 2073, 2664, 'ONT', 90, 12, 4, 107, '{"beginner":25,"intermediate":45,"advanced":20,"expert":10}', '{groomers,park}', '{family,weekend-getaway}', 'budget', '{ikon}', 'Shares a pass with Big Bear. Adjacent resorts, often combined into one trip. More intermediate terrain than Big Bear.'),

('Mt. Baldy', 'mt-baldy', 'US', 'California', 'north_america', 34.2617, -117.6464, 1997, 2750, 'ONT', 75, 12, 4, 152, '{"beginner":10,"intermediate":30,"advanced":40,"expert":20}', '{powder,steep,backcountry}', '{local,no-frills,gnarly}', 'budget', '{}', 'Underrated gem 75min from OC. Low-key vibe, no frills. Surprisingly steep and challenging. Gets decent powder on big storm cycles. Season is short.'),

('Mammoth Mountain', 'mammoth', 'US', 'California', 'north_america', 37.6308, -119.0326, 2424, 3369, 'MMH', 5, 11, 6, 914, '{"beginner":25,"intermediate":40,"advanced":25,"expert":10}', '{powder,groomers,park,trees,backcountry}', '{resort-town,party,accessible,big-mountain}', 'mid', '{ikon}', 'Best all-around resort within driving distance of SoCal (~4.5hr from OC). Massive vertical, reliable snow (300+ inches/yr), long season. Has it all. Easiest to justify for a weekend trip. Town of Mammoth is fun.'),

('June Mountain', 'june-mountain', 'US', 'California', 'north_america', 37.7634, -119.0770, 2296, 3069, 'MMH', 20, 11, 5, 762, '{"beginner":35,"intermediate":45,"advanced":15,"expert":5}', '{groomers,trees,uncrowded}', '{quiet,local,uncrowded,family}', 'budget', '{ikon}', '20min from Mammoth. Same ownership, less crowded, cheaper. Great for intermediates who want a relaxed day. Often overlooked.'),

-- Utah (short/medium tier)
('Alta Ski Area', 'alta', 'US', 'Utah', 'north_america', 40.5880, -111.6378, 2600, 3216, 'SLC', 45, 11, 4, 1372, '{"beginner":25,"intermediate":40,"advanced":35,"expert":0}', '{powder,trees,steep,backcountry}', '{powder-focused,no-frills,locals,authentic}', 'mid', '{}', 'Skiers only (no snowboarding). Legendary powder — averages 500+ inches/yr. One of the holiest pilgrimage sites in skiing. Snowbird is adjacent and combined passes exist. Affordable lodging at the base. SLC airport is 45min away.'),

('Snowbird', 'snowbird', 'US', 'Utah', 'north_america', 40.5814, -111.6556, 2365, 3352, 'SLC', 43, 11, 5, 1372, '{"beginner":10,"intermediate":30,"advanced":35,"expert":25}', '{powder,steep,backcountry,glaciers}', '{expert,powder-focused,serious}', 'mid', '{ikon}', 'Adjacent to Alta. Gnarliest resort in Utah — massive cliffs, serious terrain. Combined with Alta it''s the best powder destination in North America. Long season (sometimes open into July). Not for beginners.'),

('Park City Mountain', 'park-city', 'US', 'Utah', 'north_america', 40.6514, -111.5080, 2103, 3048, 'SLC', 40, 11, 4, 914, '{"beginner":17,"intermediate":52,"advanced":31,"expert":0}', '{groomers,park,trees,variety}', '{resort-town,luxury,accessible,family,après-ski}', 'premium', '{epic}', 'Largest ski resort in the US by acreage. 17min from SLC airport. Park City town is charming with good food and nightlife. Great for mixed groups. Connects to Canyons via gondola.'),

('Deer Valley', 'deer-valley', 'US', 'Utah', 'north_america', 40.6375, -111.4783, 2103, 2918, 'SLC', 45, 12, 4, 914, '{"beginner":27,"intermediate":41,"advanced":32,"expert":0}', '{groomers,luxury,service}', '{luxury,ski-only,upscale,family}', 'luxury', '{ikon}', 'Skiers only (no snowboarding). The most luxurious resort in Utah — impeccable grooming, valet ski check, tablecloth restaurants on the mountain. Expensive but worth it for the experience. Opens to snowboarders in 2025.'),

-- Colorado (short/medium tier)
('Breckenridge', 'breckenridge', 'US', 'Colorado', 'north_america', 39.4817, -106.0669, 2926, 3914, 'DEN', 115, 11, 5, 762, '{"beginner":14,"intermediate":31,"advanced":55,"expert":0}', '{powder,terrain-variety,high-altitude,park}', '{resort-town,party,accessible,variety}', 'premium', '{epic}', '~2hr drive from DEN. Charming historic mining town. High altitude means more powder days than most Colorado resorts. The Peak 6 area is a hidden gem. Good nightlife. Tends to get crowded on peak weeks.'),

('Telluride', 'telluride', 'US', 'Colorado', 'north_america', 37.9375, -107.8123, 2661, 4114, 'TEX', 10, 11, 4, 762, '{"beginner":23,"intermediate":38,"advanced":39,"expert":0}', '{powder,steep,scenery,luxury}', '{remote,luxury,adventure,authentic,village}', 'luxury', '{ikon}', 'One of the most beautiful ski towns in the world — box canyon, 14,000ft peaks, Victorian architecture. Remote (small regional airport or long drive from DEN). Worth every bit of effort. Less crowded than Vail/Breckenridge. Excellent snow quality.'),

('Aspen Snowmass', 'aspen', 'US', 'Colorado', 'north_america', 39.1911, -106.8175, 2422, 3813, 'ASE', 5, 11, 4, 762, '{"beginner":8,"intermediate":42,"advanced":50,"expert":0}', '{powder,luxury,steep,variety}', '{luxury,celebrity,après-ski,authentic,village}', 'luxury', '{ikon}', '4 mountains on one pass. The most iconic ski town in America. Expensive but the skiing across all 4 mountains is exceptional. Snowmass is massive and less crowded. Easier flights from LAX than most people think.'),

-- Tahoe (short/medium tier)
('Palisades Tahoe', 'palisades', 'US', 'California', 'north_america', 39.1968, -120.2357, 1890, 2762, 'RNO', 75, 11, 5, 1143, '{"beginner":13,"intermediate":29,"advanced":58,"expert":0}', '{steep,powder,freestyle,backcountry}', '{big-mountain,adventure,authentic,party}', 'mid', '{ikon}', 'Two mountains (Palisades + Alpine Meadows) connected by gondola. Best expert terrain in California. Gets big Tahoe storms. 75min from Reno airport. Impressive vertical. Used to host the Olympics.'),

('Heavenly', 'heavenly', 'US', 'Nevada', 'north_america', 38.9350, -119.9397, 1939, 3060, 'RNO', 60, 11, 4, 762, '{"beginner":20,"intermediate":45,"advanced":35,"expert":0}', '{groomers,views,variety}', '{resort-town,party,casino,accessible}', 'mid', '{epic}', 'Straddles the California-Nevada border. Lake Tahoe views are unreal. South Lake Tahoe has casino nightlife 5min from the base. Great for groups with mixed interests.'),

-- Canada (medium tier)
('Whistler Blackcomb', 'whistler', 'CA', 'British Columbia', 'north_america', 50.1163, -122.9574, 652, 2182, 'YVR', 135, 11, 5, 1143, '{"beginner":18,"intermediate":55,"advanced":27,"expert":0}', '{powder,trees,glaciers,variety,backcountry}', '{resort-town,luxury,adventure,après-ski,world-class}', 'premium', '{epic}', 'Largest ski resort in North America by skiable terrain. 2hr from Vancouver airport. Whistler Village is an exceptionally well-designed pedestrian resort town. Glacier skiing in summer. Heli-skiing day trips available. Worth the flight for a 4+ day trip.'),

('Banff Sunshine', 'banff-sunshine', 'CA', 'Alberta', 'north_america', 51.0720, -115.7633, 1660, 2730, 'YYC', 90, 11, 5, 914, '{"beginner":20,"intermediate":55,"advanced":25,"expert":0}', '{powder,scenery,variety,trees}', '{adventure,scenery,national-park,authentic}', 'mid', '{ikon}', 'Inside Banff National Park. Stunning Rocky Mountain scenery. The SkiBig3 pass covers Sunshine, Lake Louise, and Norquay — 3 resorts in one trip. Consistently dry Alberta powder. Banff town is charming.'),

('Lake Louise', 'lake-louise', 'CA', 'Alberta', 'north_america', 51.4254, -116.1773, 1645, 2637, 'YYC', 115, 11, 4, 914, '{"beginner":25,"intermediate":45,"advanced":30,"expert":0}', '{powder,scenery,groomers,variety}', '{scenery,luxury,remote,adventure}', 'premium', '{ikon}', 'One of the most scenic ski resorts on Earth. Château Frontenac-style hotel at the base. Less crowded than Whistler. Part of SkiBig3 pass. Often has the best grooming in the Canadian Rockies.'),

-- Japan (long tier 7+ days)
('Niseko United', 'niseko', 'JP', 'Hokkaido', 'asia', 42.8033, 140.6867, 190, 1308, 'CTS', 120, 12, 3, 1524, '{"beginner":30,"intermediate":40,"advanced":20,"expert":10}', '{powder,trees,off-piste,backcountry}', '{powder-focused,cultural,onsen,village,adventure,foodie}', 'premium', '{}', 'Widely considered the best powder skiing in the world. Hokkaido gets 15m+ of ultra-dry champagne snow per season. 4 interconnected resorts. Onsen culture, incredible ramen and izakayas in Niseko town. Peak season Jan-Feb. ~2hr from New Chitose airport (CTS). A once-in-a-lifetime trip for powder hounds. Book accommodation 6-12 months ahead for Jan/Feb.'),

('Hakuba Valley', 'hakuba', 'JP', 'Nagano', 'asia', 36.7003, 137.8608, 760, 2696, 'ITM', 240, 12, 3, 1143, '{"beginner":25,"intermediate":45,"advanced":20,"expert":10}', '{powder,trees,variety,backcountry}', '{cultural,village,authentic,onsen,adventure}', 'mid', '{}', '10 resorts in one valley. Hosted the 1998 Olympics. Less commercialized than Niseko, more authentic Japanese mountain village experience. 3hr from Osaka (ITM) by express bus or 2hr from Tokyo by Shinkansen. Pairs well with Tokyo or Kyoto extension.'),

-- Europe (long tier 7+ days)
('Chamonix', 'chamonix', 'FR', 'Auvergne-Rhône-Alpes', 'europe', 45.9237, 6.8694, 1035, 3842, 'GVA', 90, 12, 4, 914, '{"beginner":10,"intermediate":30,"advanced":40,"expert":20}', '{steep,off-piste,glaciers,backcountry,extreme}', '{adventure,expert,authentic,village,cultural,foodie}', 'mid', '{}', 'The spiritual home of alpinism. Aiguille du Midi cable car goes to 3,842m — the views are otherworldly. Best for advanced and expert skiers. The Vallée Blanche off-piste glacier run is a bucket list item. Geneva airport is 90min away. Combine with a night in Geneva or Lyon.'),

('Verbier', 'verbier', 'CH', 'Valais', 'europe', 46.0964, 7.2283, 1500, 3330, 'GVA', 150, 12, 4, 762, '{"beginner":10,"intermediate":30,"advanced":40,"expert":20}', '{powder,steep,off-piste,luxury}', '{luxury,party,après-ski,expert,celebrity}', 'luxury', '{}', 'One of the most prestigious ski resorts in the Alps. Part of the 4 Vallées — massive interconnected terrain. The Tortin mogul field and Mont Fort are legendary. Vibrant après-ski. Geneva airport 2.5hr. Expensive but iconic.'),

('Zermatt', 'zermatt', 'CH', 'Valais', 'europe', 46.0207, 7.7491, 1620, 3883, 'GVA', 180, 11, 4, 762, '{"beginner":20,"intermediate":45,"advanced":25,"expert":10}', '{scenery,glacier,variety,luxury}', '{luxury,scenery,iconic,car-free,cultural}', 'luxury', '{}', 'Car-free village beneath the Matterhorn. Glacier skiing makes it one of few resorts open year-round. More accessible than Verbier for mixed ability groups. Switzerland is expensive — budget accordingly. Geneva airport 3hr.'),

('Val d''Isère / Tignes', 'val-disere', 'FR', 'Auvergne-Rhône-Alpes', 'europe', 45.4480, 6.9805, 1550, 3456, 'GVA', 195, 11, 5, 914, '{"beginner":15,"intermediate":40,"advanced":35,"expert":10}', '{powder,variety,glacier,backcountry}', '{resort-town,après-ski,adventure,serious}', 'premium', '{}', 'Espace Killy: Val d''Isère and Tignes share a massive 300km ski area. Reliable snow (high altitude + glacier). One of Europe''s best for serious skiers. Geneva airport is ~3hr. Good value compared to Switzerland.'),

-- Oceania (southern hemisphere — season June–September)
('Queenstown / Remarkables', 'remarkables', 'NZ', 'Otago', 'oceania', -45.0312, 168.8311, 1943, 2319, 'ZQN', 45, 6, 9, 305, '{"beginner":30,"intermediate":40,"advanced":20,"expert":10}', '{scenery,variety,adventure}', '{adventure,bungee,party,accessible,cultural}', 'mid', '{}', 'Southern Hemisphere option for June-September. Queenstown is the adventure capital of the world — skiing is just one of many activities. The Remarkables and Coronet Peak are solid intermediate mountains. Good for a NZ trip that combines skiing with Fiordland, Milford Sound, etc. ~1.5hr flight from Auckland.'),

('Mount Hutt', 'mt-hutt', 'NZ', 'Canterbury', 'oceania', -43.4930, 171.5523, 1481, 2086, 'CHC', 90, 6, 9, 254, '{"beginner":25,"intermediate":45,"advanced":30,"expert":0}', '{powder,views,uncrowded}', '{remote,authentic,uncrowded}', 'budget', '{}', 'Best snow reliability in NZ. Steep access road but worth it. Pairs well with a Christchurch base and South Island road trip. Less touristy than Queenstown.'),

-- South America (southern hemisphere — season June–September)
('Portillo', 'portillo', 'CL', 'Valparaíso', 'south_america', -32.8369, -70.1308, 2590, 3310, 'SCL', 165, 6, 9, 914, '{"beginner":15,"intermediate":45,"advanced":25,"expert":15}', '{powder,steep,remote}', '{remote,adventure,authentic,historic,intimate}', 'premium', '{}', 'The oldest ski resort in South America — a single iconic yellow hotel at 2,800m. Small (no lift lines ever), legendary steep terrain, extraordinary dry Andean powder. Where World Cup teams train in the northern summer. 3hr from Santiago airport. A true bucket list trip.'),

('Valle Nevado', 'valle-nevado', 'CL', 'Santiago Metropolitan', 'south_america', -33.3573, -70.2753, 3025, 3670, 'SCL', 120, 6, 9, 762, '{"beginner":20,"intermediate":45,"advanced":25,"expert":10}', '{powder,variety,heli-skiing}', '{adventure,heli-skiing,accessible}', 'mid', '{}', 'Closest major resort to Santiago (2hr). 3 interconnected resorts (Valle Nevado, La Parva, El Colorado). Heli-skiing is a specialty. Dry Andean powder when conditions align. More accessible than Portillo for a Santiago-base trip.');
