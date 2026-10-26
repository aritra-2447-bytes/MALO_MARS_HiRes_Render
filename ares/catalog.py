"""Curated planetary atlas: historical missions, discovered landmarks,
namesake biographies, and aqueous-mineral targets.

All coordinates are planetocentric latitude (degrees north) and east
longitude (0-360 deg E, the convention used by NASA PDS / ODE and the IAU
planetary gazetteer).  A signed -180..180 longitude is also emitted for the
3D globe renderer.

Sources: NASA PDS Planetary Data System, IAU Gazetteer of Planetary
Nomenclature, NASA/JPL mission archives, NASA Mars Trek, and published
CRISM/OMEGA/CTX/HiRISE literature.
"""

# ---------------------------------------------------------------------------
# Historical figures, crews, and place-name etymologies
# ---------------------------------------------------------------------------

FIGURES = {
    "octavia_butler": {
        "name": "Octavia E. Butler (1947-2006)",
        "role": "American science-fiction author; MacArthur Fellow",
        "bio": (
            "Octavia Estelle Butler was one of the most influential American "
            "writers of the late 20th century. Her novels Kindred, Dawn, and "
            "Parable of the Sower weave race, gender, power, and ecological "
            "collapse into visionary speculative fiction. In 1995 she became "
            "the first science-fiction writer awarded a MacArthur Fellowship. "
            "NASA named the Perseverance touchdown site in Jezero Crater after "
            "her in 2021, honouring a storyteller who imagined humanity's "
            "future beyond Earth."
        ),
    },
    "ray_bradbury": {
        "name": "Ray Bradbury (1920-2012)",
        "role": "American author of The Martian Chronicles",
        "bio": (
            "Ray Douglas Bradbury's The Martian Chronicles (1950) imagined Mars "
            "as a mirror for human longing, colonialism, and loss. His lyrical, "
            "often elegiac stories helped shape the public's imagination of the "
            "red planet. Curiosity's touchdown site in Gale Crater was named "
            "Bradbury Landing on 22 August 2012, on what would have been his "
            "92nd birthday."
        ),
    },
    "carl_sagan": {
        "name": "Carl Sagan (1934-1996)",
        "role": "American astronomer, planetary scientist, and science communicator",
        "bio": (
            "Carl Edward Sagan advanced planetary science through studies of "
            "Mars, Venus, and the outer solar system, and through the Viking, "
            "Voyager, and Galileo missions. His television series Cosmos and "
            "his books made science a public inheritance. He chaired the "
            "committee that designed the Voyager Golden Record and argued "
            "passionately for the search for life beyond Earth. Mars Pathfinder's "
            "landing site in Ares Vallis is the Carl Sagan Memorial Station."
        ),
    },
    "thomas_mutch": {
        "name": "Thomas A. Mutch (1936-1980)",
        "role": "American planetary geologist; Viking imaging team leader",
        "bio": (
            "Thomas A. Mutch was a Brown University geologist who led the Viking "
            "lander imaging team and later served as NASA Associate Administrator "
            "for Space Science. His work on lunar and Martian surface processes "
            "helped establish planetary geology as a quantitative discipline. "
            "He died in a climbing accident in the Himalayas in 1980. Viking 1's "
            "Chryse Planitia site is the Thomas Mutch Memorial Station."
        ),
    },
    "gerald_soffen": {
        "name": "Gerald A. Soffen (1926-2000)",
        "role": "American biologist; Viking project scientist",
        "bio": (
            "Gerald Soffen was the Viking project scientist and a central figure "
            "in the first direct experiments searching for life on Mars. He also "
            "helped create NASA's Exobiology program and the NASA Astrobiology "
            "Institute. Viking 2's Utopia Planitia site is the Gerald Soffen "
            "Memorial Station."
        ),
    },
    "ptolemy": {
        "name": "Claudius Ptolemy (c. 100-c. 170 CE)",
        "role": "Greco-Roman astronomer, geographer, and mathematician",
        "bio": (
            "Ptolemy worked in Alexandria and wrote the Almagest, the Geographia, "
            "and the Tetrabiblos. His geocentric model dominated astronomy for "
            "more than a millennium, and his coordinate geography gave mapmakers "
            "a mathematical frame for the known world. Mars 3 came down near "
            "Ptolemaeus Crater, named in his honour."
        ),
    },
    "sts107": {
        "name": "STS-107 Columbia crew (2003)",
        "role": "Rick Husband, William McCool, Michael Anderson, Kalpana Chawla, David Brown, Laurel Clark, Ilan Ramon",
        "bio": (
            "The seven astronauts of Space Shuttle Columbia were lost on "
            "1 February 2003 during re-entry at the end of the STS-107 science "
            "mission. Their 16-day flight conducted microgravity and Earth-"
            "observation research. Spirit's Gusev Crater landing site is the "
            "Columbia Memorial Station, and the Columbia Hills preserve the "
            "crew's name in Martian topography."
        ),
    },
    "sts51l": {
        "name": "STS-51-L Challenger crew (1986)",
        "role": "Francis Scobee, Michael Smith, Ronald McNair, Ellison Onizuka, Judith Resnik, Gregory Jarvis, Christa McAuliffe",
        "bio": (
            "The seven crew members of Challenger were lost 73 seconds after "
            "launch on 28 January 1986. The mission carried the first Teacher in "
            "Space, Christa McAuliffe, and a wide programme of microgravity "
            "science. Opportunity's Meridiani Planum site is the Challenger "
            "Memorial Station."
        ),
    },
    "walter_gale": {
        "name": "Walter Frederick Gale (1865-1945)",
        "role": "Australian banker and amateur astronomer",
        "bio": (
            "Walter Gale observed Mars from Sydney and made detailed drawings of "
            "its surface in the late 19th and early 20th centuries. He also "
            "discovered several comets and reported features near the planet's "
            "southern limb. Gale Crater, the Curiosity landing site, is named "
            "after him."
        ),
    },
    "vera_rubin": {
        "name": "Vera Rubin (1928-2016)",
        "role": "American astronomer; dark-matter pioneer",
        "bio": (
            "Vera Rubin's measurements of galaxy rotation curves provided some of "
            "the strongest observational evidence for dark matter. She was a "
            "tireless advocate for women in science and received the National "
            "Medal of Science. Curiosity's Vera Rubin Ridge on Mount Sharp is "
            "named for her."
        ),
    },
    "henri_becquerel": {
        "name": "Antoine Henri Becquerel (1852-1908)",
        "role": "French physicist; Nobel laureate",
        "bio": (
            "Becquerel discovered natural radioactivity in uranium salts in 1896, "
            "a discovery that reshaped physics and earned him the 1903 Nobel "
            "Prize with the Curies. Becquerel Crater on Mars exposes layered "
            "sedimentary and sulfate-bearing deposits studied by orbiting "
            "spectrometers."
        ),
    },
    "edgar_burroughs": {
        "name": "Edgar Rice Burroughs (1875-1950)",
        "role": "American author; creator of John Carter of Mars",
        "bio": (
            "Burroughs's A Princess of Mars (1912) launched the Barsoom series and "
            "gave generations a romantic, adventure-filled Mars. His pulp "
            "imagination helped create modern science fiction. Burroughs Crater "
            "on Mars carries his name."
        ),
    },
    "hg_wells": {
        "name": "H. G. Wells (1866-1946)",
        "role": "English author of The War of the Worlds",
        "bio": (
            "Herbert George Wells's The War of the Worlds (1898) imagined Martian "
            "invaders and became a foundational text of science fiction. Wells "
            "was also a prolific social novelist and historian. A Martian crater "
            "bears his name."
        ),
    },
    "arthur_clarke": {
        "name": "Arthur C. Clarke (1917-2008)",
        "role": "British science-fiction author and engineer",
        "bio": (
            "Clarke co-wrote 2001: A Space Odyssey and proposed the geostationary "
            "communications satellite in 1945. His writing combined hard science "
            "with a sense of wonder and spiritual inquiry. Clarke Crater on Mars "
            "honours him."
        ),
    },
    "robert_heinlein": {
        "name": "Robert A. Heinlein (1907-1988)",
        "role": "American science-fiction author",
        "bio": (
            "Heinlein helped define modern science fiction with Stranger in a "
            "Strange Land, Starship Troopers, and The Moon Is a Harsh Mistress. "
            "His work explored politics, liberty, and human adaptation to space. "
            "Heinlein Crater on Mars is named for him."
        ),
    },
    "gene_roddenberry": {
        "name": "Gene Roddenberry (1921-1991)",
        "role": "American television producer; creator of Star Trek",
        "bio": (
            "Roddenberry created Star Trek, a series that imagined a diverse, "
            "exploratory human future and became a cultural force for inclusion "
            "and scientific curiosity. Roddenberry Crater on Mars bears his name."
        ),
    },
    "george_airy": {
        "name": "Sir George Biddell Airy (1801-1892)",
        "role": "British Astronomer Royal",
        "bio": (
            "Airy served as Astronomer Royal for 46 years and established the "
            "Greenwich meridian as the world's prime meridian. Mars' own prime "
            "meridian is defined by the small crater Airy-0, named in his honour."
        ),
    },
    "schiaparelli": {
        "name": "Giovanni Virginio Schiaparelli (1835-1910)",
        "role": "Italian astronomer",
        "bio": (
            "Schiaparelli mapped Mars in the 1870s and described linear features "
            "as canali, a word translated as canals and taken by some as evidence "
            "of intelligent life. He also linked meteor showers to comet orbits. "
            "Schiaparelli Crater and the failed ESA Schiaparelli lander both bear "
            "his name."
        ),
    },
    "lowell": {
        "name": "Percival Lowell (1855-1916)",
        "role": "American astronomer and Mars observer",
        "bio": (
            "Lowell founded the Lowell Observatory in Flagstaff and popularised "
            "the idea of Martian canals, a hypothesis later disproved. His "
            "observatory nonetheless contributed to the discovery of Pluto. "
            "Lowell Crater on Mars carries his name."
        ),
    },
    "huygens": {
        "name": "Christiaan Huygens (1629-1695)",
        "role": "Dutch astronomer, physicist, and mathematician",
        "bio": (
            "Huygens discovered Titan, described Saturn's rings, invented the "
            "pendulum clock, and developed the wave theory of light. Huygens "
            "Crater on Mars honours his contributions to planetary observation."
        ),
    },
    "john_holden": {
        "name": "Edward Singleton Holden (1846-1914)",
        "role": "American astronomer",
        "bio": (
            "Holden was the first director of the Lick Observatory and a founder "
            "of the Astronomical Society of the Pacific. He studied Mars and the "
            "Moon. Holden Crater, a proposed Mars rover landing site with exposed "
            "lacustrine clays, is named for him."
        ),
    },
    "gusev": {
        "name": "Matvey Gusev (1826-1866)",
        "role": "Russian astronomer",
        "bio": (
            "Gusev pioneered photographic astronomy and heliographic studies at "
            "the Pulkovo Observatory. Gusev Crater, explored by Spirit, is named "
            "in his honour."
        ),
    },
    "wright_brothers": {
        "name": "Orville and Wilbur Wright (1871-1948; 1867-1912)",
        "role": "American aviation pioneers",
        "bio": (
            "The Wright brothers achieved the first powered, controlled, "
            "sustained airplane flight at Kitty Hawk on 17 December 1903. Their "
            "methodical engineering opened the air age. Ingenuity's first-flight "
            "airfield in Jezero Crater is named Wright Brothers Field."
        ),
    },
    "beagle": {
        "name": "HMS Beagle (1820-1870)",
        "role": "British survey ship; Charles Darwin's voyage",
        "bio": (
            "HMS Beagle carried Charles Darwin around the world from 1831 to 1836, "
            "a voyage that led to On the Origin of Species. ESA's Beagle 2 lander "
            "was named for the ship; it reached Isidis Planitia in 2003 but did "
            "not return data."
        ),
    },
    "jezero_place": {
        "name": "Jezero, Bosnia and Herzegovina",
        "role": "Municipality whose name means 'lake' in Slavic languages",
        "bio": (
            "Jezero is a town and municipality in Republika Srpska, Bosnia and "
            "Herzegovina. Its name means 'lake' in Bosnian, Croatian, and Serbian, "
            "an apt name for the ancient lake basin that Perseverance is "
            "exploring."
        ),
    },
}


# ---------------------------------------------------------------------------
# Complete historical Mars landing registry
# ---------------------------------------------------------------------------

def _lon180(lon_east):
    lon = float(lon_east) % 360.0
    if lon > 180.0:
        lon -= 360.0
    return round(lon, 4)


def _mission(entry):
    entry = dict(entry)
    entry["lon"] = _lon180(entry["lon_east"])
    entry.setdefault("type", "lander")
    entry.setdefault("agency", "NASA")
    entry.setdefault("status", "Completed")
    entry.setdefault("elevation_m", 0)
    return entry


HISTORICAL_MISSIONS = [
    _mission({
        "id": "mars_2_lander",
        "name": "Mars 2 Lander / Prop-M",
        "vehicle": "Mars 2 (M-71)",
        "station": "Mars 2 Impact Site",
        "type": "lander",
        "agency": "USSR",
        "launch": "19 May 1971",
        "arrival": "27 November 1971",
        "status": "Failed",
        "lat": -45.0,
        "lon_east": 302.0,
        "elevation_m": 1200,
        "figure": "ptolemy",
        "significance": (
            "Mars 2 carried the first Prop-M walking robot, a small skis-and-"
            "tethered demonstrator intended to step across the Martian surface. "
            "The descent system failed and the lander crashed; the orbiter still "
            "returned valuable images and atmospheric data."
        ),
        "summary": "First Soviet Mars lander attempt; carried the Prop-M walking rover concept.",
    }),
    _mission({
        "id": "mars_3_lander",
        "name": "Mars 3 Lander / Prop-M",
        "vehicle": "Mars 3 (M-71)",
        "station": "Ptolemaeus Station",
        "type": "lander",
        "agency": "USSR",
        "launch": "28 May 1971",
        "arrival": "2 December 1971",
        "status": "Failed",
        "lat": -45.04,
        "lon_east": 202.02,
        "elevation_m": 1500,
        "figure": "ptolemy",
        "significance": (
            "Mars 3 achieved the first soft landing on Mars, in Ptolemaeus Crater "
            "near Sirenum Fossae, and began transmitting before contact was lost "
            "after about 20 seconds. It carried the Prop-M tethered walking robot, "
            "a precursor of planetary rovers."
        ),
        "summary": "First soft landing on Mars (1971), near Ptolemaeus Crater; contact lost after 20 s.",
    }),
    _mission({
        "id": "mars_6_lander",
        "name": "Mars 6 Lander",
        "vehicle": "Mars 6",
        "station": "Margaritifer Impact Site",
        "type": "lander",
        "agency": "USSR",
        "launch": "5 August 1973",
        "arrival": "12 March 1974",
        "status": "Failed",
        "lat": -23.9,
        "lon_east": 340.2,
        "elevation_m": -800,
        "significance": (
            "Mars 6 transmitted atmospheric data during descent but fell silent "
            "just before touchdown in the Margaritifer Terra region. Its "
            "measurements contributed to early models of the Martian atmosphere."
        ),
        "summary": "Soviet descent probe; returned atmospheric data before failing at touchdown.",
    }),
    _mission({
        "id": "viking_1",
        "name": "Viking 1 Lander",
        "vehicle": "Viking 1",
        "station": "Thomas Mutch Memorial Station",
        "type": "lander",
        "agency": "NASA",
        "launch": "20 August 1975",
        "arrival": "20 July 1976",
        "status": "Completed",
        "lat": 22.48,
        "lon_east": 312.03,
        "elevation_m": -3627,
        "figure": "thomas_mutch",
        "significance": (
            "Viking 1 returned the first clear images from the Martian surface and "
            "conducted the first life-detection experiments. Its Chryse Planitia "
            "site revealed a rocky, wind-scoured plain and provided daily weather "
            "and seismology records for years."
        ),
        "summary": "First successful Mars lander; first surface images and biology experiments.",
    }),
    _mission({
        "id": "viking_2",
        "name": "Viking 2 Lander",
        "vehicle": "Viking 2",
        "station": "Gerald Soffen Memorial Station",
        "type": "lander",
        "agency": "NASA",
        "launch": "9 September 1975",
        "arrival": "3 September 1976",
        "status": "Completed",
        "lat": 48.269,
        "lon_east": 134.01,
        "elevation_m": -3820,
        "figure": "gerald_soffen",
        "significance": (
            "Viking 2 landed in Utopia Planitia and operated for more than three "
            "years. Its cameras showed a boulder-strewn plain with frost and dust "
            "events; its biology and meteorology instruments extended the Viking "
            "1 record."
        ),
        "summary": "Second Viking lander; long-duration weather, imaging, and biology campaign.",
    }),
    _mission({
        "id": "pathfinder_sojourner",
        "name": "Mars Pathfinder / Sojourner",
        "vehicle": "Mars Pathfinder",
        "station": "Carl Sagan Memorial Station",
        "type": "rover",
        "agency": "NASA",
        "launch": "4 December 1996",
        "arrival": "4 July 1997",
        "status": "Completed",
        "lat": 19.13,
        "lon_east": 326.78,
        "elevation_m": -3682,
        "figure": "carl_sagan",
        "significance": (
            "Pathfinder demonstrated airbag landing and deployed Sojourner, the "
            "first wheeled rover on Mars. The Ares Vallis site contains rounded "
            "pebbles and layered rocks consistent with catastrophic floods, and "
            "Sojourner's APXS analysed the andesitic Barnacle Bill and Yogi rocks."
        ),
        "summary": "First Mars rover mission; airbag landing and 83-sol Sojourner traverse.",
    }),
    _mission({
        "id": "beagle2_lander",
        "name": "Beagle 2",
        "vehicle": "Mars Express / Beagle 2",
        "station": "Isidis Planitia Station",
        "type": "lander",
        "agency": "ESA",
        "launch": "2 June 2003",
        "arrival": "25 December 2003",
        "status": "Failed",
        "lat": 11.5265,
        "lon_east": 90.4295,
        "elevation_m": -3610,
        "figure": "beagle",
        "significance": (
            "Beagle 2 was Europe's first Mars lander, designed to search for "
            "past life with a miniature gas-analysis laboratory. It reached "
            "Isidis Planitia but failed to deploy all of its solar panels; the "
            "lander was imaged from orbit in 2015."
        ),
        "summary": "ESA's first Mars lander; reached Isidis Planitia but did not deploy fully.",
    }),
    _mission({
        "id": "mer_spirit",
        "name": "Spirit (MER-A)",
        "vehicle": "Mars Exploration Rover Spirit",
        "station": "Columbia Memorial Station",
        "type": "rover",
        "agency": "NASA",
        "launch": "10 June 2003",
        "arrival": "4 January 2004",
        "status": "Completed",
        "lat": -14.5684,
        "lon_east": 175.4726,
        "elevation_m": -1910,
        "figure": "sts107",
        "significance": (
            "Spirit explored Gusev Crater and the Columbia Hills, finding evidence "
            "of ancient hydrothermal alteration, explosive volcanism, and near-"
            "neutral water. It became trapped in soft sulfate sands near Home "
            "Plate in 2009 and operated as a stationary observatory until 2010."
        ),
        "summary": "MER-A; discovered hydrothermal silica and ancient water in Gusev Crater.",
    }),
    _mission({
        "id": "mer_opportunity",
        "name": "Opportunity (MER-B)",
        "vehicle": "Mars Exploration Rover Opportunity",
        "station": "Challenger Memorial Station",
        "type": "rover",
        "agency": "NASA",
        "launch": "7 July 2003",
        "arrival": "25 January 2004",
        "status": "Completed",
        "lat": -1.9462,
        "lon_east": 354.4734,
        "elevation_m": -1390,
        "figure": "sts51l",
        "significance": (
            "Opportunity landed at Eagle Crater in Meridiani Planum and found "
            "hematite spherules, jarosite, and layered sulfates that established "
            "a history of acidic, salty surface water. It traversed 45.16 km to "
            "Endeavour Crater, setting the off-world driving record."
        ),
        "summary": "MER-B; 45.16 km traverse and definitive evidence of ancient acidic water.",
    }),
    _mission({
        "id": "phoenix_lander",
        "name": "Phoenix Lander",
        "vehicle": "Phoenix Mars Lander",
        "station": "Green Valley Station",
        "type": "lander",
        "agency": "NASA",
        "launch": "4 August 2007",
        "arrival": "25 May 2008",
        "status": "Completed",
        "lat": 68.2188,
        "lon_east": 234.2508,
        "elevation_m": -4130,
        "significance": (
            "Phoenix touched down in the northern polar region and dug into ice-"
            "cemented soil, confirming subsurface water ice. Its wet-chemistry "
            "laboratory detected perchlorate salts and measured the local "
            "atmosphere and frost cycle."
        ),
        "summary": "Confirmed subsurface water ice and perchlorate chemistry at the north polar margin.",
    }),
    _mission({
        "id": "msl_curiosity",
        "name": "Curiosity (MSL)",
        "vehicle": "Mars Science Laboratory",
        "station": "Bradbury Landing",
        "type": "rover",
        "agency": "NASA",
        "launch": "26 November 2011",
        "arrival": "6 August 2012",
        "status": "Active",
        "lat": -4.5895,
        "lon_east": 137.4417,
        "elevation_m": -4501,
        "figure": "ray_bradbury",
        "significance": (
            "Curiosity found lake and stream deposits, organic molecules, and "
            "varied redox chemistry in Gale Crater. Its climb of Aeolis Mons "
            "(Mount Sharp) is reading a layered record of environmental change "
            "from a wet, habitable early Mars to a drier, sulfate-rich world."
        ),
        "summary": "Active MSL rover; ancient habitable lake deposits and Mount Sharp stratigraphy.",
    }),
    _mission({
        "id": "insight_lander",
        "name": "InSight Lander",
        "vehicle": "Interior Exploration using Seismic Investigations, Geodesy and Heat Transport",
        "station": "Homestead Hollow",
        "type": "lander",
        "agency": "NASA",
        "launch": "5 May 2018",
        "arrival": "26 November 2018",
        "status": "Completed",
        "lat": 4.502,
        "lon_east": 135.623,
        "elevation_m": -2613,
        "significance": (
            "InSight deployed the first seismometer on another planet and detected "
            "marsquakes, revealing a crust, mantle, and core structure beneath "
            "Elysium Planitia. Its heat-flow probe struggled with the soil, but "
            "the seismic record transformed understanding of Mars' interior."
        ),
        "summary": "First dedicated Mars geophysics lander; detected marsquakes and mapped the interior.",
    }),
    _mission({
        "id": "m20_perseverance",
        "name": "Perseverance (Mars 2020)",
        "vehicle": "Mars 2020 Perseverance",
        "station": "Octavia E. Butler Landing",
        "type": "rover",
        "agency": "NASA",
        "launch": "30 July 2020",
        "arrival": "18 February 2021",
        "status": "Active",
        "lat": 18.4446,
        "lon_east": 77.4508,
        "elevation_m": -2570,
        "figure": "octavia_butler",
        "significance": (
            "Perseverance is characterising Jezero Crater's ancient lake and river "
            "delta, caching rock cores for possible Mars Sample Return, and testing "
            "oxygen production and autonomous navigation. Its instruments have "
            "identified carbonate, clay, and sulfate-bearing materials in the "
            "western fan and Neretva Vallis."
        ),
        "summary": "Active Mars 2020 rover; sampling Jezero delta and caching cores for return.",
    }),
    _mission({
        "id": "ingenuity_helicopter",
        "name": "Ingenuity Mars Helicopter",
        "vehicle": "Mars 2020 Ingenuity",
        "station": "Wright Brothers Field",
        "type": "aircraft",
        "agency": "NASA",
        "launch": "30 July 2020",
        "arrival": "18 February 2021",
        "status": "Completed",
        "lat": 18.4447,
        "lon_east": 77.4508,
        "elevation_m": -2570,
        "figure": "wright_brothers",
        "significance": (
            "Ingenuity made the first powered, controlled flight on another planet "
            "on 19 April 2021. Across 72 flights it scouted terrain for "
            "Perseverance and demonstrated aerial reconnaissance in a thin "
            "atmosphere, a milestone for future Mars aviation."
        ),
        "summary": "First powered flight on another world; 72 sorties from Wright Brothers Field.",
    }),
    _mission({
        "id": "cnsa_zhurong",
        "name": "Zhurong (Tianwen-1)",
        "vehicle": "Tianwen-1",
        "station": "Utopia Planitia South",
        "type": "rover",
        "agency": "CNSA",
        "launch": "23 July 2020",
        "arrival": "15 May 2021",
        "status": "Completed",
        "lat": 25.0833,
        "lon_east": 109.9084,
        "elevation_m": -4099,
        "significance": (
            "Zhurong was China's first Mars rover, landing in southern Utopia "
            "Planitia and driving 1.92 km across aeolian ridges and polygonal "
            "terrain. Ground-penetrating radar detected shallow subsurface "
            "structure and possible buried ice; the rover entered hibernation in "
            "2022."
        ),
        "summary": "China's first Mars rover; 1.92 km traverse and subsurface radar survey.",
    }),
    _mission({
        "id": "mars_polar_lander",
        "name": "Mars Polar Lander",
        "vehicle": "Mars Polar Lander / Deep Space 2",
        "station": "Planum Australe Impact Site",
        "type": "lander",
        "agency": "NASA",
        "launch": "3 January 1999",
        "arrival": "3 December 1999",
        "status": "Failed",
        "lat": -76.18,
        "lon_east": 195.38,
        "elevation_m": 1200,
        "significance": (
            "Mars Polar Lander was intended to study the south polar layered "
            "deposits and volatile history. Contact was lost during descent, and "
            "the failure was later traced to premature engine shutdown. It also "
            "carried the Deep Space 2 penetrators."
        ),
        "summary": "Failed south-polar lander; no contact after descent.",
    }),
    _mission({
        "id": "schiaparelli_edm",
        "name": "Schiaparelli EDM Lander",
        "vehicle": "ExoMars 2016 / Schiaparelli",
        "station": "Meridiani Impact Site",
        "type": "lander",
        "agency": "ESA / Roscosmos",
        "launch": "14 March 2016",
        "arrival": "19 October 2016",
        "status": "Failed",
        "lat": -2.07,
        "lon_east": 353.79,
        "elevation_m": -1400,
        "figure": "schiaparelli",
        "significance": (
            "Schiaparelli was an ESA technology demonstration lander for the "
            "ExoMars programme. It reached Meridiani Planum but crashed after a "
            "guidance and parachute anomaly; the accident investigation improved "
            "entry, descent, and landing models for later missions."
        ),
        "summary": "ESA ExoMars test lander; crashed during descent in Meridiani Planum.",
    }),
    _mission({
        "id": "exomars_rosalind_franklin",
        "name": "ExoMars Rosalind Franklin (planned)",
        "vehicle": "ExoMars Rosalind Franklin",
        "station": "Oxia Planum",
        "type": "rover",
        "agency": "ESA / Roscosmos",
        "launch": "Planned",
        "arrival": "Planned",
        "status": "Proposed",
        "lat": 18.2,
        "lon_east": 335.6,
        "elevation_m": -2000,
        "significance": (
            "The Rosalind Franklin rover is designed to drill two metres into "
            "ancient clay-rich terrain at Oxia Planum, searching for organic "
            "molecular biosignatures. The site preserves some of the oldest "
            "exposed phyllosilicates on Mars."
        ),
        "summary": "Planned ESA rover targeting ancient clay-rich Oxia Planum.",
    }),
]


# ---------------------------------------------------------------------------
# Discovered landmarks & astrobiology-relevant features
# ---------------------------------------------------------------------------

LANDMARKS = [
    {
        "id": "olympus_mons", "name": "Olympus Mons", "lat": 18.65, "lon_east": 226.2,
        "elevation_m": 21287, "category": "volcano", "diameter_km": 600,
        "namesake": {"name": "Mount Olympus", "role": "Mythic home of the Greek gods", "bio": "In Greek mythology Mount Olympus was the seat of the Olympian gods. The Martian volcano is the tallest known mountain in the Solar System, rising about 21.3 km above the surrounding plains."},
        "significance": "A shield volcano built by long-lived basaltic volcanism, with a 600 km footprint and a summit caldera complex. Its flanks preserve lava flows and graben.",
    },
    {
        "id": "valles_marineris", "name": "Valles Marineris", "lat": -9.8, "lon_east": 283.5,
        "elevation_m": -8200, "category": "canyon", "diameter_km": 4000,
        "namesake": {"name": "Mariner 9 (1971)", "role": "NASA orbiter that discovered the canyon system", "bio": "Mariner 9 was the first spacecraft to orbit another planet. During the 1971 global dust storm its cameras revealed Valles Marineris, Olympus Mons, and the volcanic provinces of Tharsis."},
        "significance": "A 4,000 km tectonic rift system with walls exposing kilometres of layered stratigraphy, sulfate deposits, and possible ancient lake basins such as Melas Chasma.",
    },
    {
        "id": "melas_chasma", "name": "Melas Chasma", "lat": -10.0, "lon_east": 283.6,
        "elevation_m": -8000, "category": "chasma", "diameter_km": 500,
        "namesake": {"name": "Melas (Greek: black/dark)", "role": "Classical place name", "bio": "Melas is a Greek word for dark or black, used in classical geography. The chasma's floor contains some of the deepest exposed terrain on Mars."},
        "significance": "Layered sulfates and clay minerals indicate past standing water and groundwater upwelling in the deepest part of Valles Marineris.",
    },
    {
        "id": "candor_chasma", "name": "Candor Chasma", "lat": -6.2, "lon_east": 283.0,
        "elevation_m": -5500, "category": "chasma", "diameter_km": 800,
        "namesake": {"name": "Candor (Latin: shining/white)", "role": "Classical place name", "bio": "Candor is Latin for brightness or sincerity, a classical name applied to this central chasma of Valles Marineris."},
        "significance": "Contains thick layered deposits with hydrated sulfates, suggesting a past lake or groundwater-fed evaporitic basin.",
    },
    {
        "id": "ophir_chasma", "name": "Ophir Chasma", "lat": -4.0, "lon_east": 287.0,
        "elevation_m": -4000, "category": "chasma", "diameter_km": 300,
        "namesake": {"name": "Ophir", "role": "Biblical land of gold", "bio": "Ophir is a legendary land of gold in the Hebrew Bible, associated with King Solomon's trade."},
        "significance": "Layered light-toned deposits and landslides record wall collapse and possible lacustrine sedimentation.",
    },
    {
        "id": "echus_chasma", "name": "Echus Chasma", "lat": 1.0, "lon_east": 278.0,
        "elevation_m": -2000, "category": "chasma", "diameter_km": 400,
        "namesake": {"name": "Echo (Greek nymph)", "role": "Classical mythological figure", "bio": "Echo was a nymph in Greek mythology condemned to repeat the last words spoken to her."},
        "significance": "Source region of Kasei Valles; layered deposits and channels record catastrophic outflow and later sapping.",
    },
    {
        "id": "arsia_mons", "name": "Arsia Mons", "lat": -8.35, "lon_east": 239.0,
        "elevation_m": 17700, "category": "volcano", "diameter_km": 435,
        "namesake": {"name": "Arsia Silva", "role": "Roman name for a sacred grove", "bio": "Arsia Silva was a sacred grove in ancient Rome, associated with the Arsia stream. The name was given to one of the three Tharsis Montes."},
        "significance": "A giant shield volcano with a summit caldera and young lava flows; its flank pits and glacial deposits record recent ice-rock interactions.",
    },
    {
        "id": "pavonis_mons", "name": "Pavonis Mons", "lat": 1.48, "lon_east": 247.0,
        "elevation_m": 14000, "category": "volcano", "diameter_km": 375,
        "namesake": {"name": "Pavo (Latin: peacock)", "role": "Constellation and classical bird", "bio": "Pavo is the Latin word for peacock and the name of a southern constellation. The volcano sits on the Tharsis bulge."},
        "significance": "Central Tharsis volcano with a broad summit caldera; its flanks are cut by faults and lava channels.",
    },
    {
        "id": "ascraeus_mons", "name": "Ascraeus Mons", "lat": 11.92, "lon_east": 255.9,
        "elevation_m": 18200, "category": "volcano", "diameter_km": 460,
        "namesake": {"name": "Ascra", "role": "Birthplace of Hesiod in Greek Boeotia", "bio": "Ascra was a village in Boeotia, Greece, celebrated as the birthplace of the poet Hesiod."},
        "significance": "The northernmost of the Tharsis Montes, with a complex caldera and extensive lava-flow fields.",
    },
    {
        "id": "tharsis", "name": "Tharsis Bulge", "lat": 0.0, "lon_east": 260.0,
        "elevation_m": 8000, "category": "volcanic_plateau", "diameter_km": 5000,
        "namesake": {"name": "Tarshish", "role": "Biblical land at the edge of the world", "bio": "Tarshish appears in the Hebrew Bible as a distant land rich in silver and trade. The name was applied to the vast volcanic rise on Mars."},
        "significance": "A 5,000 km volcanic plateau that dominates Martian topography and may have influenced the planet's early climate and hydrology.",
    },
    {
        "id": "elysium_mons", "name": "Elysium Mons", "lat": 25.02, "lon_east": 147.21,
        "elevation_m": 12600, "category": "volcano", "diameter_km": 240,
        "namesake": {"name": "Elysium", "role": "Greek mythological afterlife", "bio": "Elysium was the paradise of Greek myth, a blessed land at the edge of the world."},
        "significance": "The principal volcano of the Elysium province, with flank channels and a summit caldera.",
    },
    {
        "id": "hellas_planitia", "name": "Hellas Planitia", "lat": -42.7, "lon_east": 70.0,
        "elevation_m": -7152, "category": "impact_basin", "diameter_km": 2300,
        "namesake": {"name": "Hellas", "role": "Greek name for Greece", "bio": "Hellas is the classical Greek name for Greece, the homeland of the Hellenic world."},
        "significance": "One of the largest impact basins in the Solar System and the lowest point on Mars; its floor may once have held a lake and shows possible glacial and fluvial landforms.",
    },
    {
        "id": "jezero_crater", "name": "Jezero Crater", "lat": 18.4446, "lon_east": 77.4508,
        "elevation_m": -2570, "category": "impact_crater", "diameter_km": 49,
        "figure": "jezero_place",
        "significance": "A 49 km Noachian crater with a well-preserved western river delta, shoreline deposits, and hydrated clay/carbonate minerals. Perseverance is exploring it as a prime astrobiology site.",
    },
    {
        "id": "gale_crater", "name": "Gale Crater / Aeolis Mons", "lat": -4.5895, "lon_east": 137.4417,
        "elevation_m": -4501, "category": "impact_crater", "diameter_km": 154,
        "figure": "walter_gale",
        "significance": "A 154 km crater containing a 5 km-high sedimentary mound (Mount Sharp) that records a transition from lake environments to drier, sulfate-rich conditions.",
    },
    {
        "id": "gusev_crater", "name": "Gusev Crater", "lat": -14.5684, "lon_east": 175.4726,
        "elevation_m": -1910, "category": "impact_crater", "diameter_km": 160,
        "figure": "gusev",
        "significance": "A crater once fed by Ma'adim Vallis; Spirit found evidence for explosive volcanism, hydrothermal silica, and past water in the Columbia Hills.",
    },
    {
        "id": "holden_crater", "name": "Holden Crater", "lat": -26.0, "lon_east": 326.0,
        "elevation_m": -2000, "category": "impact_crater", "diameter_km": 140,
        "figure": "john_holden",
        "significance": "Exposes clay-bearing lacustrine sediments and a breached rim; a high-priority Mars sample-return and astrobiology candidate.",
    },
    {
        "id": "endeavour_crater", "name": "Endeavour Crater", "lat": -2.33, "lon_east": 354.8,
        "elevation_m": -1300, "category": "impact_crater", "diameter_km": 22,
        "namesake": {"name": "HMS Endeavour", "role": "Captain James Cook's 18th-century exploration ship", "bio": "HMS Endeavour carried James Cook on his first Pacific voyage (1768-1771), charting New Zealand and the east coast of Australia."},
        "significance": "Opportunity's final destination; rim outcrops contain gypsum veins and clay minerals indicating ancient groundwater.",
    },
    {
        "id": "victoria_crater", "name": "Victoria Crater", "lat": -2.05, "lon_east": 354.5,
        "elevation_m": -1350, "category": "impact_crater", "diameter_km": 0.75,
        "namesake": {"name": "Victoria", "role": "Historic ship of exploration", "bio": "Victoria was the only ship of Ferdinand Magellan's fleet to complete the first circumnavigation of the globe (1519-1522)."},
        "significance": "A small, fresh crater explored by Opportunity; its walls expose layered sulfate-bearing sandstone and cross-bedding from ancient dunes.",
    },
    {
        "id": "eagle_crater", "name": "Eagle Crater", "lat": -1.9462, "lon_east": 354.4734,
        "elevation_m": -1390, "category": "impact_crater", "diameter_km": 0.022,
        "namesake": {"name": "Eagle", "role": "Apollo 11 lunar module", "bio": "Eagle was the lunar module that carried Neil Armstrong and Buzz Aldrin to the Moon's Sea of Tranquility in July 1969."},
        "significance": "Opportunity's landing crater; its outcrop provided the first in-situ evidence of ancient acidic, salty water on Mars.",
    },
    {
        "id": "columbia_hills", "name": "Columbia Hills", "lat": -14.62, "lon_east": 175.53,
        "elevation_m": -1800, "category": "hills", "diameter_km": 10,
        "figure": "sts107",
        "significance": "A range of low hills inside Gusev Crater where Spirit found hydrothermal silica, carbonate, and evidence of ancient water-rock interaction.",
    },
    {
        "id": "home_plate", "name": "Home Plate", "lat": -14.645, "lon_east": 175.55,
        "elevation_m": -1850, "category": "volcanic_feature", "diameter_km": 0.1,
        "namesake": {"name": "Home Plate", "role": "Descriptive baseball term", "bio": "The feature is named for its resemblance to a baseball home plate, a flat-topped, layered volcanic plateau."},
        "significance": "A pyroclastic deposit with hydrated silica and possible hydrothermal alteration, studied by Spirit.",
    },
    {
        "id": "vera_rubin_ridge", "name": "Vera Rubin Ridge", "lat": -4.69, "lon_east": 137.36,
        "elevation_m": -4150, "category": "ridge", "diameter_km": 6,
        "figure": "vera_rubin",
        "significance": "A hematite-rich ridge on Mount Sharp's lower slope, recording a period of changing lake chemistry and diagenesis.",
    },
    {
        "id": "gediz_vallis", "name": "Gediz Vallis", "lat": -4.78, "lon_east": 137.30,
        "elevation_m": -3680, "category": "valley", "diameter_km": 9,
        "namesake": {"name": "Gediz River", "role": "River in western Anatolia, Turkey", "bio": "The Gediz flows through western Turkey to the Aegean; its name was given to a Martian valley carved by water and debris flows."},
        "significance": "A debris-flow channel and ridge system on Mount Sharp with sulfate-bearing deposits; a key Curiosity exploration target.",
    },
    {
        "id": "seitah", "name": "Seitah Dunes", "lat": 18.42, "lon_east": 77.52,
        "elevation_m": -2500, "category": "dune_field", "diameter_km": 4,
        "namesake": {"name": "Seitah", "role": "Navajo word meaning 'among the sand'", "bio": "Seitah is a Navajo term meaning 'among the sand', chosen by the Perseverance team with the Navajo Nation."},
        "significance": "A layered olivine-rich dune field and fractured bedrock unit in Jezero; the rover's first major science campaign.",
    },
    {
        "id": "kodiak_butte", "name": "Kodiak Butte", "lat": 18.42, "lon_east": 77.51,
        "elevation_m": -2480, "category": "delta", "diameter_km": 1.5,
        "namesake": {"name": "Kodiak Island", "role": "Island in the Gulf of Alaska", "bio": "Kodiak Island is a rugged Alaskan island known for its brown bears and fishing culture; the butte's name reflects its deltaic shape."},
        "significance": "An isolated remnant of Jezero's western delta with foreset beds that record a standing lake and sediment transport.",
    },
    {
        "id": "neretva_vallis", "name": "Neretva Vallis", "lat": 18.47, "lon_east": 77.41,
        "elevation_m": -2380, "category": "valley", "diameter_km": 20,
        "namesake": {"name": "Neretva River", "role": "River in Bosnia and Herzegovina and Croatia", "bio": "The Neretva is a clear, karst-fed river of the Dinaric Alps, famous for its canyon and historic Mostar bridge."},
        "significance": "The ancient river inlet that fed Jezero's lake; its channel deposits include sandstones and possible flood-transported boulders.",
    },
    {
        "id": "belva_crater", "name": "Belva Crater", "lat": 18.51, "lon_east": 77.35,
        "elevation_m": -2310, "category": "impact_crater", "diameter_km": 0.8,
        "namesake": {"name": "Belva", "role": "Descriptive/IAU approved name", "bio": "Belva is an IAU-approved name for this small crater in the Jezero region."},
        "significance": "A small fresh crater exposing deep stratigraphy; Perseverance climbed its rim to read Jezero's subsurface geology.",
    },
    {
        "id": "mawrth_vallis", "name": "Mawrth Vallis", "lat": 22.3, "lon_east": 343.5,
        "elevation_m": -2000, "category": "valley", "diameter_km": 600,
        "namesake": {"name": "Mawrth", "role": "Welsh word for Mars", "bio": "Mawrth is the Welsh name for Mars, the red planet."},
        "significance": "One of the largest exposures of ancient phyllosilicates on Mars, with Al-smectite over Fe/Mg-smectite stratigraphy; a prime astrobiology target.",
    },
    {
        "id": "nili_fossae", "name": "Nili Fossae", "lat": 21.0, "lon_east": 74.0,
        "elevation_m": -1000, "category": "fossae", "diameter_km": 600,
        "namesake": {"name": "Nili", "role": "Latin name for the Nile", "bio": "Nili is the Latin genitive of Nilus, the Nile, used in classical geography."},
        "significance": "A fracture system exposing Fe/Mg-smectite, carbonate, and olivine; a leading candidate for ancient hydrothermal habitability.",
    },
    {
        "id": "syrtis_major", "name": "Syrtis Major", "lat": 8.0, "lon_east": 70.0,
        "elevation_m": -1500, "category": "volcanic_plain", "diameter_km": 1350,
        "namesake": {"name": "Syrtis Major", "role": "Classical name for the Gulf of Sidra, Libya", "bio": "Syrtis Major is the classical name of the Gulf of Sidra on the Libyan coast; the dark Martian feature was one of the first surface markings mapped by Huygens."},
        "significance": "A low-relief volcanic province with clay and silica signatures, and one of the earliest telescopically mapped Martian features.",
    },
    {
        "id": "oxia_planum", "name": "Oxia Planum", "lat": 18.2, "lon_east": 335.6,
        "elevation_m": -2000, "category": "landing_site", "diameter_km": 80,
        "namesake": {"name": "Oxia", "role": "Classical place name", "bio": "Oxia is a classical Greek place name used for a region of the ancient world."},
        "significance": "The ExoMars Rosalind Franklin landing site; exposes ancient Fe/Mg-clay-bearing plains and channel deposits.",
    },
    {
        "id": "airy_0", "name": "Airy-0", "lat": -5.0, "lon_east": 0.0,
        "elevation_m": -400, "category": "prime_meridian", "diameter_km": 0.5,
        "figure": "george_airy",
        "significance": "The small crater that defines Mars' prime meridian (0 degrees longitude), chosen because it lies inside the larger Airy Crater.",
    },
    {
        "id": "sagan_crater", "name": "Sagan Crater", "lat": 10.8, "lon_east": 329.3,
        "elevation_m": -3000, "category": "impact_crater", "diameter_km": 90,
        "figure": "carl_sagan",
        "significance": "A Noachian crater named for Carl Sagan; its surroundings expose ancient cratered terrain.",
    },
    {
        "id": "burroughs_crater", "name": "Burroughs Crater", "lat": 7.8, "lon_east": 327.0,
        "elevation_m": -3000, "category": "impact_crater", "diameter_km": 125,
        "figure": "edgar_burroughs",
        "significance": "An ancient crater in the Sinus Sabaeus region, named for the creator of John Carter.",
    },
    {
        "id": "wells_crater", "name": "Wells Crater", "lat": 60.2, "lon_east": 237.9,
        "elevation_m": 0, "category": "impact_crater", "diameter_km": 100,
        "figure": "hg_wells",
        "significance": "A northern highland crater named for H. G. Wells.",
    },
    {
        "id": "clarke_crater", "name": "Clarke Crater", "lat": -63.6, "lon_east": 28.0,
        "elevation_m": 0, "category": "impact_crater", "diameter_km": 50,
        "figure": "arthur_clarke",
        "significance": "A southern crater named for Arthur C. Clarke, near the boundary of the south polar region.",
    },
    {
        "id": "heinlein_crater", "name": "Heinlein Crater", "lat": 64.6, "lon_east": 243.0,
        "elevation_m": 0, "category": "impact_crater", "diameter_km": 90,
        "figure": "robert_heinlein",
        "significance": "A northern crater named for Robert A. Heinlein.",
    },
    {
        "id": "roddenberry_crater", "name": "Roddenberry Crater", "lat": 49.0, "lon_east": 4.5,
        "elevation_m": 0, "category": "impact_crater", "diameter_km": 139,
        "figure": "gene_roddenberry",
        "significance": "A crater named for Gene Roddenberry, creator of Star Trek.",
    },
    {
        "id": "becquerel_crater", "name": "Becquerel Crater", "lat": 22.1, "lon_east": 352.0,
        "elevation_m": -2000, "category": "impact_crater", "diameter_km": 167,
        "figure": "henri_becquerel",
        "significance": "Contains layered light-toned deposits with hydrated sulfates, interpreted as a former lake or groundwater-fed basin.",
    },
    {
        "id": "schiaparelli_crater", "name": "Schiaparelli Crater", "lat": -2.7, "lon_east": 344.3,
        "elevation_m": -2000, "category": "impact_crater", "diameter_km": 461,
        "figure": "schiaparelli",
        "significance": "A large ancient crater in Terra Meridiani with layered deposits and channels; ESA's Schiaparelli lander targeted the nearby Meridiani plains.",
    },
    {
        "id": "lowell_crater", "name": "Lowell Crater", "lat": -52.3, "lon_east": 278.0,
        "elevation_m": 0, "category": "impact_crater", "diameter_km": 203,
        "figure": "lowell",
        "significance": "A large southern crater named for Percival Lowell.",
    },
    {
        "id": "huygens_crater", "name": "Huygens Crater", "lat": -42.0, "lon_east": 304.0,
        "elevation_m": 0, "category": "impact_crater", "diameter_km": 470,
        "figure": "huygens",
        "significance": "One of the largest craters in the southern highlands, named for Christiaan Huygens.",
    },
    {
        "id": "maadim_vallis", "name": "Ma'adim Vallis", "lat": -13.0, "lon_east": 177.0,
        "elevation_m": -1500, "category": "valley", "diameter_km": 900,
        "namesake": {"name": "Ma'adim", "role": "Hebrew word for Mars", "bio": "Ma'adim is the Hebrew name for Mars. The valley is one of the largest ancient outflow channels on the planet."},
        "significance": "A 900 km valley that drained into Gusev Crater; its terraces and tributaries record sustained ancient flow.",
    },
    {
        "id": "ares_vallis", "name": "Ares Vallis", "lat": 19.13, "lon_east": 326.78,
        "elevation_m": -3682, "category": "valley", "diameter_km": 1700,
        "namesake": {"name": "Ares", "role": "Greek god of war", "bio": "Ares is the Greek god of war, counterpart of the Roman Mars."},
        "significance": "A catastrophic outflow channel with streamlined islands and rounded boulders; Pathfinder landed at its mouth in Chryse Planitia.",
    },
    {
        "id": "chryse_planitia", "name": "Chryse Planitia", "lat": 22.48, "lon_east": 312.03,
        "elevation_m": -3627, "category": "plain", "diameter_km": 1600,
        "namesake": {"name": "Chryse", "role": "Greek for 'golden land'", "bio": "Chryse is Greek for a golden land or region, a classical name applied to this low plain."},
        "significance": "A low basin at the mouths of Ares and Tiu Valles; Viking 1 landed here in 1976.",
    },
    {
        "id": "utopia_planitia", "name": "Utopia Planitia", "lat": 25.0833, "lon_east": 109.9084,
        "elevation_m": -4099, "category": "plain", "diameter_km": 3300,
        "namesake": {"name": "Utopia", "role": "Greek for 'no place'; Thomas More's ideal society", "bio": "Utopia is the title of Thomas More's 1516 book describing an ideal society; the Greek word means 'no place'."},
        "significance": "A vast northern lowland with polygonal terrain, mud volcanism, and buried ice; Zhurong landed in its southern part.",
    },
    {
        "id": "planum_boreum", "name": "Planum Boreum (North Polar Cap)", "lat": 84.5, "lon_east": 0.0,
        "elevation_m": -2000, "category": "polar_cap", "diameter_km": 1000,
        "namesake": {"name": "Boreas", "role": "Greek god of the north wind", "bio": "Boreas is the Greek personification of the north wind; planum boreum means the northern plain."},
        "significance": "A perennial water-ice cap with spiral troughs and layered deposits recording millions of years of climate history.",
    },
    {
        "id": "planum_australe", "name": "Planum Australe (South Polar Cap)", "lat": -85.0, "lon_east": 0.0,
        "elevation_m": 1500, "category": "polar_cap", "diameter_km": 1000,
        "namesake": {"name": "Auster", "role": "Roman god of the south wind", "bio": "Auster is the Roman personification of the south wind; planum australe means the southern plain."},
        "significance": "A residual CO2 ice cap over water ice, with layered deposits and subglacial lakes hypothesized from radar.",
    },
]


# ---------------------------------------------------------------------------
# Aqueous mineral classes and CRISM/OMEGA target catalogue
# ---------------------------------------------------------------------------

MINERAL_CLASSES = {
    "fe_mg_clay": {"label": "Fe/Mg Phyllosilicates", "color": "#38bdf8", "group": "clay", "description": "Iron/magnesium smectites and chlorites; neutral-to-alkaline water, high habitability potential."},
    "al_clay": {"label": "Al Phyllosilicates", "color": "#a78bfa", "group": "clay", "description": "Kaolinite-group clays formed by intense leaching; evidence of sustained warm, wet conditions."},
    "sulfate_poly": {"label": "Polyhydrated Sulfates", "color": "#fbbf24", "group": "sulfate", "description": "Mg/Fe sulfates such as epsomite and starkeyite; evaporitic or groundwater alteration."},
    "sulfate_mono": {"label": "Monohydrated Sulfates", "color": "#f59e0b", "group": "sulfate", "description": "Kieserite-group sulfates; drier, more acidic evaporative settings."},
    "carbonate": {"label": "Carbonates", "color": "#34d399", "group": "carbonate", "description": "Mg/Fe/Ca carbonates; CO2 sequestration and possible biosignature preservation."},
    "silica": {"label": "Hydrated Silica", "color": "#f472b6", "group": "silica", "description": "Opaline silica and hydrated glass; hydrothermal or pedogenic alteration, excellent biosignature preservation."},
    "hematite": {"label": "Hematite / Iron Oxides", "color": "#ef4444", "group": "oxide", "description": "Ferric oxides marking oxidizing, water-limited weathering and diagenesis."},
    "chloride": {"label": "Chloride Salts", "color": "#e2e8f0", "group": "salt", "description": "Halite and chloride evaporites; evidence of closed-basin evaporation and brine evolution."},
}

MINERAL_SITES = [
    {
        "id": "jezero_west_fan", "name": "Jezero Western Fan Delta", "lat": 18.44, "lon_east": 77.45,
        "classes": ["fe_mg_clay", "carbonate", "silica"], "confidence": 0.95, "source": "CRISM TRDR / Perseverance SHERLOC & PIXL",
        "radius_deg": 0.06,
        "description": "A paleolake delta with Fe/Mg-smectite, carbonate, and hydrated silica in layered fan deposits; the primary Perseverance astrobiology campaign.",
    },
    {
        "id": "jezero_neretva", "name": "Neretva Vallis Inlet", "lat": 18.47, "lon_east": 77.41,
        "classes": ["fe_mg_clay", "sulfate_poly"], "confidence": 0.88, "source": "CRISM TRDR / Mastcam-Z",
        "radius_deg": 0.05,
        "description": "Fluvial sandstones and clay-bearing channel deposits recording the river that fed Jezero's lake.",
    },
    {
        "id": "nili_fossae", "name": "Nili Fossae", "lat": 21.0, "lon_east": 74.0,
        "classes": ["fe_mg_clay", "carbonate", "silica"], "confidence": 0.96, "source": "CRISM MRDR / OMEGA DDR",
        "radius_deg": 0.35,
        "description": "One of the largest clay-carbonate exposures on Mars, with olivine and possible hydrothermal silica; a top astrobiology target.",
    },
    {
        "id": "mawrth_vallis", "name": "Mawrth Vallis", "lat": 22.3, "lon_east": 343.5,
        "classes": ["al_clay", "fe_mg_clay", "silica"], "confidence": 0.97, "source": "CRISM TRDR / OMEGA DDR",
        "radius_deg": 0.3,
        "description": "A classic inverted stratigraphy of Al-smectite over Fe/Mg-smectite, recording intense aqueous alteration of the ancient crust.",
    },
    {
        "id": "gale_mount_sharp", "name": "Gale Crater / Mount Sharp", "lat": -4.65, "lon_east": 137.38,
        "classes": ["fe_mg_clay", "sulfate_poly", "hematite", "silica"], "confidence": 0.93, "source": "CRISM TRDR / Curiosity CheMin & SAM",
        "radius_deg": 0.09,
        "description": "Layered clay, sulfate, and hematite units recording the transition from a habitable lake to a drier, oxidizing environment.",
    },
    {
        "id": "valles_marineris_sulfates", "name": "Valles Marineris Layered Sulfates", "lat": -9.8, "lon_east": 283.6,
        "classes": ["sulfate_poly", "sulfate_mono", "fe_mg_clay"], "confidence": 0.9, "source": "CRISM MRDR / OMEGA",
        "radius_deg": 0.28,
        "description": "Kilometre-scale layered sulfate and clay deposits on the chasma floor, consistent with a past lake or groundwater-fed basin.",
    },
    {
        "id": "meridiani_hematite", "name": "Meridiani Planum Hematite", "lat": -1.95, "lon_east": 354.47,
        "classes": ["hematite", "sulfate_poly", "chloride"], "confidence": 0.98, "source": "CRISM / Opportunity MB & APXS",
        "radius_deg": 0.16,
        "description": "The hematite-bearing plains explored by Opportunity, with jarosite and sulfate sandstone recording acidic surface water.",
    },
    {
        "id": "syrtis_major", "name": "Syrtis Major", "lat": 8.0, "lon_east": 70.0,
        "classes": ["al_clay", "fe_mg_clay", "silica"], "confidence": 0.84, "source": "CRISM TRDR / OMEGA",
        "radius_deg": 0.5,
        "description": "A volcanic province with clay and hydrated-silica signatures, including possible hydrothermal alteration near faults.",
    },
    {
        "id": "terra_sirenum", "name": "Terra Sirenum Chloride Basins", "lat": -35.0, "lon_east": 200.0,
        "classes": ["chloride", "fe_mg_clay"], "confidence": 0.82, "source": "CRISM / OMEGA",
        "radius_deg": 0.4,
        "description": "Widespread chloride salt deposits in closed basins, recording evaporation of ancient brines.",
    },
    {
        "id": "columbus_crater", "name": "Columbus Crater Carbonates", "lat": -29.8, "lon_east": 194.0,
        "classes": ["carbonate", "fe_mg_clay", "silica"], "confidence": 0.87, "source": "CRISM TRDR",
        "radius_deg": 0.18,
        "description": "A crater floor with Mg-carbonate and clay-bearing deposits, interpreted as a former closed-basin lake.",
    },
    {
        "id": "cross_crater", "name": "Cross Crater Silica", "lat": -2.0, "lon_east": 5.5,
        "classes": ["silica", "sulfate_poly"], "confidence": 0.85, "source": "CRISM TRDR",
        "radius_deg": 0.12,
        "description": "Hydrated silica and sulfate deposits in a crater floor, a possible hydrothermal or evaporitic setting.",
    },
    {
        "id": "juventae_chasma", "name": "Juventae Chasma Sulfates", "lat": -4.5, "lon_east": 298.5,
        "classes": ["sulfate_poly", "sulfate_mono", "hematite"], "confidence": 0.88, "source": "CRISM MRDR / OMEGA",
        "radius_deg": 0.22,
        "description": "Light-toned layered sulfate deposits in an outflow chasma, recording evaporation and groundwater upwelling.",
    },
    {
        "id": "aram_chaos", "name": "Aram Chaos", "lat": 2.5, "lon_east": 338.5,
        "classes": ["sulfate_poly", "hematite", "fe_mg_clay"], "confidence": 0.86, "source": "CRISM / OMEGA",
        "radius_deg": 0.2,
        "description": "A chaotic terrain basin with polyhydrated sulfates and hematite, evidence of past water and collapse.",
    },
    {
        "id": "holden_crater", "name": "Holden Crater Lacustrine Clays", "lat": -26.0, "lon_east": 326.0,
        "classes": ["fe_mg_clay", "carbonate", "silica"], "confidence": 0.9, "source": "CRISM TRDR / HiRISE",
        "radius_deg": 0.16,
        "description": "Exposed lacustrine clay and carbonate sediments in a breached crater; a high-priority sample-return site.",
    },
    {
        "id": "eberswalde_crater", "name": "Eberswalde Delta", "lat": -23.9, "lon_east": 326.8,
        "classes": ["fe_mg_clay", "silica"], "confidence": 0.89, "source": "CRISM TRDR / HiRISE",
        "radius_deg": 0.12,
        "description": "A well-preserved ancient river delta with clay-bearing sediments and meandering distributary channels.",
    },
    {
        "id": "jepson_delta", "name": "Jepson Delta (Jezero)", "lat": 18.42, "lon_east": 77.50,
        "classes": ["fe_mg_clay", "carbonate"], "confidence": 0.91, "source": "CRISM / Perseverance",
        "radius_deg": 0.03,
        "description": "A secondary delta remnant in Jezero with clay and carbonate-bearing sediments.",
    },
]


def get_figure(key):
    return FIGURES.get(key)


def mission_payload():
    """Return missions enriched with figure bios and signed longitudes."""
    out = []
    for m in HISTORICAL_MISSIONS:
        item = dict(m)
        item["lon"] = _lon180(m["lon_east"])
        fig = FIGURES.get(m.get("figure"))
        if fig:
            item["namesake"] = fig
        item["hover_title"] = m.get("station") or m["name"]
        out.append(item)
    return out


def landmark_payload():
    out = []
    for lm in LANDMARKS:
        item = dict(lm)
        item["lon"] = _lon180(lm["lon_east"])
        fig = FIGURES.get(lm.get("figure"))
        if fig:
            item["namesake"] = fig
        out.append(item)
    return out


def mineral_payload():
    return {
        "classes": MINERAL_CLASSES,
        "sites": MINERAL_SITES,
        "instruments": [
            {"id": "CRISM", "host": "MRO", "products": ["TRDR", "DDR", "MRDR"], "description": "Compact Reconnaissance Imaging Spectrometer for Mars (0.36-3.92 um)."},
            {"id": "OMEGA", "host": "MEX", "products": ["EDR", "DDR"], "description": "Observatoire pour la Mineralogie, l'Eau, les Glaces et l'Activite (0.35-5.1 um)."},
        ],
    }
