"""Bundled starter catalog so the extension works without a TMDB key."""
import json
from . import db

# Short, original descriptions and editorial tags for a local demo catalog.
TITLES = [
    ("The Matrix", "movie", 1999, "A hacker discovers a simulated reality and joins a rebellion against its machines.", "Science Fiction,Action", "simulation,cyberpunk,rebellion"),
    ("Inception", "movie", 2010, "A skilled thief enters layered dreams to plant an idea in a target's mind.", "Science Fiction,Thriller", "mind bending,dreams,heist"),
    ("Interstellar", "movie", 2014, "Explorers travel through space to find a future home for humanity.", "Science Fiction,Drama", "space,exploration,emotional"),
    ("Arrival", "movie", 2016, "A linguist works to communicate with visitors from another world.", "Science Fiction,Drama", "aliens,language,thoughtful"),
    ("Blade Runner 2049", "movie", 2017, "A future detective uncovers a secret that could change the balance between humans and replicants.", "Science Fiction,Thriller", "cyberpunk,identity,dystopia"),
    ("Dune", "movie", 2021, "A young heir enters a struggle for power on a desert planet.", "Science Fiction,Adventure", "space,politics,epic"),
    ("Ex Machina", "movie", 2014, "A programmer tests an artificial intelligence in a remote laboratory.", "Science Fiction,Thriller", "artificial intelligence,identity,thoughtful"),
    ("The Martian", "movie", 2015, "An astronaut stranded on Mars uses science and ingenuity to survive.", "Science Fiction,Adventure", "space,survival,hopeful"),
    ("Everything Everywhere All at Once", "movie", 2022, "A family finds itself caught in a strange conflict across many possible lives.", "Science Fiction,Comedy", "multiverse,family,emotional"),
    ("The Truman Show", "movie", 1998, "A man slowly discovers that his familiar world is a constructed television set.", "Drama,Comedy", "simulation,identity,thoughtful"),
    ("The Dark Knight", "movie", 2008, "A masked crime fighter faces a chaotic adversary who tests the limits of justice.", "Action,Crime", "hero,crime,dark"),
    ("Spider-Man: Into the Spider-Verse", "movie", 2018, "A young hero meets other spider heroes from parallel worlds.", "Animation,Action", "hero,multiverse,coming of age"),
    ("Knives Out", "movie", 2019, "A detective untangles a wealthy family's secrets after a suspicious death.", "Mystery,Comedy", "detective,whodunit,family"),
    ("Glass Onion", "movie", 2022, "A detective investigates a puzzle among a group of rich friends on an island.", "Mystery,Comedy", "detective,whodunit,satire"),
    ("Parasite", "movie", 2019, "Two households become entangled through a family's elaborate deception.", "Drama,Thriller", "class,family,satire"),
    ("The Grand Budapest Hotel", "movie", 2014, "A hotel concierge and his apprentice are swept into an inheritance mystery.", "Comedy,Adventure", "whimsical,friendship,mystery"),
    ("Spirited Away", "movie", 2001, "A girl must navigate a spirit world to rescue her parents.", "Animation,Fantasy", "coming of age,magic,adventure"),
    ("The Lord of the Rings: The Fellowship of the Ring", "movie", 2001, "A group of companions begins a dangerous quest with a powerful ring.", "Fantasy,Adventure", "quest,magic,friendship"),
    ("Breaking Bad", "tv", 2008, "A chemistry teacher enters the drug trade and faces mounting consequences.", "Crime,Drama", "antihero,crime,dark"),
    ("Better Call Saul", "tv", 2015, "A struggling lawyer's choices draw him into a criminal underworld.", "Crime,Drama", "antihero,crime,character study"),
    ("Stranger Things", "tv", 2016, "Friends confront strange experiments and a dangerous alternate world.", "Science Fiction,Drama", "mystery,friendship,supernatural"),
    ("Dark", "tv", 2017, "Families in a small town confront disappearances and a tangled cycle of time.", "Science Fiction,Mystery", "time travel,mind bending,dark"),
    ("Severance", "tv", 2022, "Office workers undergo a procedure separating their work memories from their lives outside.", "Science Fiction,Thriller", "identity,dystopia,mind bending"),
    ("Black Mirror", "tv", 2011, "Standalone stories examine the uneasy relationship between technology and society.", "Science Fiction,Thriller", "technology,dystopia,thoughtful"),
    ("The Last of Us", "tv", 2023, "Two survivors cross a dangerous landscape after a catastrophic outbreak.", "Drama,Adventure", "survival,found family,emotional"),
    ("The Mandalorian", "tv", 2019, "A lone bounty hunter travels the galaxy while protecting a young companion.", "Science Fiction,Adventure", "space,found family,quest"),
    ("Only Murders in the Building", "tv", 2021, "Three neighbors launch a podcast while investigating a death in their apartment building.", "Mystery,Comedy", "detective,whodunit,friendship"),
    ("The Bear", "tv", 2022, "A chef returns home to run a family sandwich shop under intense pressure.", "Drama,Comedy", "family,workplace,emotional"),
]


def seed_catalog():
    with db.connect() as connection:
        for title, media_type, year, overview, genres, tags in TITLES:
            connection.execute("""INSERT OR IGNORE INTO media
                (source, source_id, media_type, title, overview, genres, tags, year)
                VALUES ('demo', ?, ?, ?, ?, ?, ?, ?)""",
                (title.lower().replace(" ", "-"), media_type, title, overview,
                 json.dumps(genres.split(",")), json.dumps(tags.split(",")), year))
