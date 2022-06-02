import random

import pandas as pd
from flask import flash, request
from flask import jsonify
import geocoder
from app import app
from app.models import *


@app.route('/')
def index():
    ##main route
    all_artists = Artist.query.order_by(Artist.name.asc()).all()
    artists_list = []
    for artist in all_artists:
        artists_list.append(artist.to_dict())
    return jsonify({"status": True})


@app.route('/genres')
def genres():
    all_genres = Genre.query.order_by(Genre.name.asc()).all()
    genre_list = []
    for genre in all_genres:
        genre_list.append(genre.to_dict())
    return jsonify(genre_list)


@app.route('/porch')
def porch():
    all_porches = ArtistToPorch.query.order_by(ArtistToPorch.time.asc()).all()
    porch_list = []
    for porches in all_porches:
        porch_list.append(porches.to_dict())
    return jsonify(porch_list)


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_input = request.json['entry']

    exact_artist = Artist.query.filter(Artist.name == search_input).limit(4).all()

    if len(exact_artist) < 4:
        more_artists = Artist.query.filter(Artist.name.like("%" + search_input + "%")).limit(
            4 - len(exact_artist)).all()
    else:
        more_artists = None

    if exact_artist:
        artist_like = exact_artist
        if more_artists:
            # checks to see if exact artist matches any similar artists
            same = 0
            for artist in more_artists:
                for a in exact_artist:
                    if artist == a:
                        same = 1
                if same == 0:
                    artist_like.append(artist)
    elif more_artists:
        artist_like = more_artists
    else:
        artist_like = []

    artist_search_results = []
    for i in range(0, len(artist_like)):
        artist_data = artist_like[i].to_dict()
        artist_search_results.append({"artist": artist_data})

    exact_genre = Genre.query.filter(Genre.name == search_input).limit(4).all()

    if len(exact_genre) < 4:
        more_genres = Genre.query.filter(Genre.name.like("%" + search_input + "%")).limit(
            4 - len(exact_genre)).all()
    else:
        more_genres = None

    if exact_genre:
        genre_like = exact_genre
        if more_genres:
            # checks to see if exact genre matches any similar genres
            same = 0
            for genre in more_genres:
                for g in exact_genre:
                    if genre == g:
                        same = 1
                if same == 0:
                    genre_like.append(genre)
    elif more_genres:
        genre_like = more_genres
    else:
        genre_like = []

    genre_search_results = []
    for i in range(0, len(genre_like)):
        genre_data = genre_like[i].to_dict()
        genre_search_results.append({"genre": genre_data})

    return jsonify({"artists": artist_search_results, "genres": genre_search_results})


# @app.route('/reset_db')
# def reset_db():
# flash("Resetting database: deleting old data and repopulating with dummy data")
# # clear all data from all tables
# meta = db.metadata
# for table in reversed(meta.sorted_tables):
#     print('Clear table {}'.format(table))
#     db.session.execute(table.delete())
# db.session.commit()
# populate_db()
# return jsonify({"status": True})


@app.route('/artist_info_all_add')
def add_five_artist():
    # Clear the current tables of data
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print('Clear table {}'.format(table))
        db.session.execute(table.delete())
    db.session.commit()

    flash("Adding five artists with all data to the database...")

    porches = ['105 Farm St', '106 2nd St', '130 Linn St', '202 E Falls St', '204 E Yates St']
    for i in range(5):
        g = geocoder.osm(porches[i] + " Ithaca, NY")
        porch = Porch(address=porches[i], latitude=g.latlng[0], longitude=g.latlng[1])
        db.session.add(porch)
        db.session.commit()

    genres = ["Rock", "Musical theatre", "Soul music", "Pop music", "Folk music", "Blues", "Electronic "
                                                                                           "dance music", "Jazz",
              "Country music", "Punk rock"]
    for genre in genres:
        genre = Genre(name=genre)
        db.session.add(genre)
        db.session.commit()

    artist_name = ["Daniel Kaiya", "The Flywheels", "The Grady Girls", "Northside Stringband",
                   "Bob Keefe and the Surf Renegades"]
    hometown = ["Ithaca, NY", "Ithaca, NY", "Ithaca, NY", "Ithaca, NY", "Ithaca, NY"]
    about = [
        "I'm surrendering my expectations to the dance of it, the ride of the vibes, the will to live deeply from within, guided by true emotion, in devotion to the Earth and the Birth of possibility just beyond the edge of what I see.",
        "Bluegrass with grit in the southern Finger Lakes region of New York.",
        "Toe tapping, heart lifting, subtle and smiling, The Grady Girls breathe new life into timeless Irish dance tunes!",
        "Northside neighbors, Laura (fiddle/guitar), Deb (guitar/banjo), Marc Faris (guitar/banjo) and Scott (bass) enjoy playing Southern old time music together and with friends.",
        "The Surf Renegades are the only authentic surf band in Central New York. Their repertoire includes standard surf tunes by the Ventures, Dick Dale (and other So. Cal. surf bands) and surf originals by Bob Keefe."
    ]
    photo_url = [
        "https://scontent-lga3-2.xx.fbcdn.net/v/t1.6435-9/55525887_2096958433757908_600752795271823360_n.jpg?_nc_cat=110&ccb=1-5&_nc_sid=09cbfe&_nc_ohc=SgegyjXIak8AX8fss7R&_nc_ht=scontent-lga3-2.xx&oh=00_AT80IvRBVR2OhmH3uiVUQcSgpo8P2mYQ3fVCvETTM0q1dA&oe=6260560D",
        "https://scontent-lga3-2.xx.fbcdn.net/v/t1.6435-9/60347829_404865583446217_7485028511070027776_n.jpg?_nc_cat=100&ccb=1-5&_nc_sid=09cbfe&_nc_ohc=CEzpCh2VRooAX_93qx2&_nc_ht=scontent-lga3-2.xx&oh=00_AT9Sx87s4sHFAZ0D1fcaJqVDc7inrhajTvptEt6_CqNbVw&oe=62604C2D",
        "https://scontent-lga3-2.xx.fbcdn.net/v/t1.18169-9/29542062_10155319538882765_4416304449885024713_n.jpg?_nc_cat=108&ccb=1-5&_nc_sid=09cbfe&_nc_ohc=JGIUsgEjiOgAX9EfKjg&_nc_ht=scontent-lga3-2.xx&oh=00_AT_qn8DzS0ECQFnoNVqmMcDkIK_b8oXwLT0KY7dITK5NQQ&oe=625F629E",
        "https://scontent-lga3-2.xx.fbcdn.net/v/t1.6435-9/51349617_536239003538676_5810532190991155200_n.jpg?_nc_cat=109&ccb=1-5&_nc_sid=09cbfe&_nc_ohc=KGp7nIhM4RcAX8OKGKq&_nc_ht=scontent-lga3-2.xx&oh=00_AT8UUbp33tFZZ8zCIUDjnFcwQtZnQOz009zMqDVEXs2lSQ&oe=625F9D69",
        "https://www.surf-renegades.com/s/cc_images/teaserbox_2435443.jpg?t=1559514607"
    ]
    spotify_url = ["https://open.spotify.com/artist/3Nrfpe0tUJi4K4DXYWgMUX",
                   "https://open.spotify.com/artist/06HL4z0CvFAxyc27GXpf02",
                   "https://open.spotify.com/artist/3TVXtAsR1Inumwj472S9r4",
                   "https://open.spotify.com/artist/1Xyo4u8uXC1ZmMpatF05PJ",
                   "https://open.spotify.com/artist/6qqNVTkY8uBg9cP3Jd7DAH"
                   ]

    website_url = ["https://wildflowerfire.com/",
                   "https://flywheels.bandcamp.com/",
                   "https://soundcloud.com/the-grady-girls",
                   "https://www.deborahjustice.org/northside-stringband",
                   "https://www.surf-renegades.com/"
                   ]
    facebook_url = ["https://www.facebook.com/kaiyamusic/",
                    "https://www.facebook.com/FlywheelsBluegrass/",
                    "https://www.facebook.com/thegradygirls/",
                    "https://www.facebook.com/Northside-Stringband-536218100207433/",
                    "https://www.facebook.com/BobKeefeSurf/"
                    ]
    # Add artists
    for i in range(5):
        artist = Artist(name=artist_name[i], hometown=hometown[i], about=about[i], photo=photo_url[i],
                        spotify=spotify_url[i], website=website_url[i], facebook=facebook_url[i])
        db.session.add(artist)
        db.session.commit()

    # Add eventToArtists
    for i in range(5):
        artist = db.session.query(Artist).filter_by(name=artist_name[i]).first()
        porch = db.session.query(Porch).filter_by(address=porches[i]).first()
        time = datetime(2019, 9, 22, random.randint(1, 12))
        event = ArtistToPorch(time=time, artist_id=artist.id, porch_id=porch.id)
        db.session.add(event)
        db.session.commit()

    # Add genresToArtists
    genres_from_db = db.session.query(Genre).all()
    for i in range(5):
        num = random.randint(1, 6)
        randGenre = random.sample(genres_from_db, num)
        artist = db.session.query(Artist).filter_by(name=artist_name[i]).first()
        for i in range(num):
            genreToArtist = ArtistToGenre(artist_id=artist.id, genre_id=randGenre[i].id)
            db.session.add(genreToArtist)
            db.session.commit()
    return jsonify({"status": True})


@app.route('/add_all_artists_csv')
def add_csv():
    # Clear the current tables of data
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print('Clear table {}'.format(table))
        db.session.execute(table.delete())
    db.session.commit()

    df = pd.read_csv('Trumansburg_Porchfest_Registration.csv').fillna("")

    for i in range(0, len(df)):
        if df.iloc[i, 1] != '':
            # Add artist
            artist = Artist(name=df.iloc[i, 1], hometown="Trumansburg",
                            about=df.iloc[i, 2],
                            photo=df.iloc[i, 3], spotify=df.iloc[i, 13], website=df.iloc[i, 14],
                            facebook=df.iloc[i, 12])
            db.session.add(artist)
            db.session.commit()
            # Google Maps API to get lat and long?
            # Add porch

            date = datetime.strptime('11 June, 2022', '%d %B, %Y')
            addr = df.iloc[i, 4]
            geoLocation = geocoder.osm(addr + " Trumansburg, NY")
            # 6,7,8,9,10 --- 12,1,2,3,4
            timePlaying = -1
            if df.iloc[i, 6] != '':
                timePlaying = 12
            elif df.iloc[i, 7] != '':
                timePlaying = 1
            elif df.iloc[i, 8] != '':
                timePlaying = 2
            elif df.iloc[i, 9] != '':
                timePlaying = 3
            elif df.iloc[i, 10] != '':
                timePlaying = 4
            porch = Porch(address=addr, time=date.replace(hour=timePlaying),
                          latitude=geoLocation.current_result.geometry['coordinates'][1],
                          longitude=geoLocation.current_result.geometry['coordinates'][0])
            db.session.add(porch)
            db.session.commit()
            # Add porch to artist
            artistToPorch = ArtistToPorch(artist_id=artist.id, porch_id=porch.id)
            db.session.add(artistToPorch)
            db.session.commit()

            cur_artist_genres = df.iloc[i, 5]  # List of genres
            if cur_artist_genres != "":
                genres_list = cur_artist_genres.split(",")
                for genre in genres_list:
                    genre = genre.strip().lower()
                    genre_found = db.session.query(Genre).filter_by(name=genre).first()
                    if genre_found:
                        genreToArtist = ArtistToGenre(artist_id=artist.id, genre_id=genre_found.id)
                        db.session.add(genreToArtist)
                        db.session.commit()
                    else:
                        genre_not_found = Genre(name=genre)
                        db.session.add(genre_not_found)
                        db.session.commit()
                        genreToArtist = ArtistToGenre(artist_id=artist.id, genre_id=genre_not_found.id)
                        db.session.add(genreToArtist)
                        db.session.commit()

    return jsonify({"status": True})
