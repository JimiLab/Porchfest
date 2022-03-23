import os
import re
import uuid

import jwt
import pandas as pd
from flask import flash, redirect, url_for, request, render_template
from flask import jsonify
from flask_cors import cross_origin
from flask_login import login_user, logout_user, current_user
from werkzeug.urls import url_parse
from flask_login import login_required
from app import db, create_app
from app import app
from app.forms import *
from app.models import *
from flask_jwt_extended import create_access_token, jwt_required, create_refresh_token, get_jwt_identity


@app.route("/login", methods=["POST"])
def login():
    auth = request.json
    if not auth or not auth.get('email') or not auth.get('password'):
        # returns 401 if any email or / and password is missing
        return jsonify(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="Login required !!"'}
        )
    user = User.query \
        .filter_by(email=auth.get('email')) \
        .first()
    if not user:
        # returns 401 if user does not exist
        return jsonify(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="User does not exist !!"'}
        )

    if check_password_hash(user.password_hash, auth.get('password')):
        # generates the JWT Token
        access_token = create_access_token(identity=user.id, fresh=True)
        refresh_token = create_refresh_token(identity=user.id)
        user.access_token = access_token
        user.refresh_token = refresh_token
        db.session.add(user)
        db.session.commit()
        return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 201
    else:
        return jsonify('Password or email incorrect'), 202


@app.route('/signup', methods=['POST'])
def signup():
    # creates a dictionary of the form data
    info = request.json
    regexEmail = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    regexPassword = '^(?=\S{8,20}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])'
    # gets name, email and password
    email = info.get('email')
    password = info.get('password')
    if not re.fullmatch(regexEmail, email) and not re.fullmatch(regexPassword, password):
        return jsonify('Email is not valid format or password', 202)

    # checking for existing user
    user = User.query \
        .filter_by(email=email) \
        .first()
    if not user:
        username = str(email).split('@')
        # database ORM object
        user = User(
            username=username[0],
            email=email,
            password_hash=generate_password_hash(password)
        )
        # insert user
        print("User created")
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=user.id, fresh=True)
        refresh_token = create_refresh_token(identity=user.id)
        user.access_token = access_token
        user.refresh_token = refresh_token
        db.session.add(user)
        db.session.commit()
        return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 201
    else:
        # returns 202 if user already exists
        return jsonify('User already exists. Please Log in.', 202)


# refresh tokens to access this route.
@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    user = User.query.filter_by(id=identity).first()
    user.access_token = access_token
    db.session.add(user)
    db.session.commit()
    return jsonify(access_token=access_token)


@app.route('/')
def index():
    all_artists = Artist.query.order_by(Artist.name.asc()).all()
    artists_list = []
    for artist in all_artists:
        artists_list.append(artist.to_dict())
    return jsonify({"status": True})
    # return jsonify(artists_list)
    # return jsonify({ "name": "Post Malone", "id": 7297, "hometown": "Grapevine, TX", "about": "Malone was born on July 4, 1995 in Syracuse, New York and moved to Grapevine, Texas at the age of 10. He started playing guitar at the age of 14 because of popular video game Guitar Hero . He later auditioned for band Crowd the Empire in 2010 but was rejected after his guitar string broke during the audition.", "photo": "https://i.scdn.co/image/93fec27f9aac86526b9010e882037afbda4e3d5f", "twitter": "https://twitter.com/postmalone", "spotify": "https://open.spotify.com/artist/246dkjvS1zLTtiykXe5h60", "instagram": "https://www.instagram.com/postmalone/", "merch": "https://shop.postmalone.com" })


@app.route('/artist/<string:slug>', methods=['GET', 'POST'])
def get_slug_artist(slug):
    info = request.json
    user = None
    if info is not None:
        user = User.query.filter_by(access_token=info.get('access_token')).first()
    artist_data = Artist.query.filter_by(url_slug=slug).first_or_404()
    if user:
        favoritedArtist = UserToArtist.query.filter(UserToArtist.artist_id == artist_data.id,
                                                    UserToArtist.user_id == user.id).first()
        if favoritedArtist is not None:
            result = {"artist": artist_data.to_dict()}
            result['liked'] = favoritedArtist.favorite
            return result
    result = {"artist": artist_data.to_dict()}
    return jsonify(result)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    # return jsonify({"status": True})
    return render_template('register.html', title='Register', form=form)


@app.route('/artists', methods=['GET', 'POST'])
def artists():
    sort_type = request.json['type']
    if sort_type == 'alphabetical':
        all_artists = Artist.query.order_by(Artist.name.asc()).all()
        artists_list = []
        for artist in all_artists:
            artists_list.append(artist.to_dict())
        return jsonify(artists_list)
    else:
        genre_artist_results = []
        all_genres = Genre.query.order_by(Genre.name.asc()).all()
        all_artists = Artist.query.order_by(Artist.name.asc()).all()
        count = 0
        for genre in all_genres:
            genre_artists = {genre.name: [], "slug": genre.url_slug}
            artist_to_genre_info = ArtistToGenre.query.filter_by(genre_id=genre.id).all()
            for artist_to_genre in artist_to_genre_info:
                for artist in all_artists:
                    if artist.id == artist_to_genre.artist_id:
                        if count < 3:
                            genre_artists[genre.name].append(artist.to_dict())
                            count += 1
            count = 0
            genre_artist_results.append(genre_artists)
        return jsonify(genre_artist_results)


@app.route('/genres')
def genres():
    all_genres = Genre.query.order_by(Genre.name.asc()).all()
    genre_list = []
    for genre in all_genres:
        genre_list.append(genre.to_dict())
    return jsonify(genre_list)


@app.route('/genre/<string:slug>', methods=['GET'])
def get_slug_genre(slug):
    genre_artist_results = []
    genre_data = Genre.query.filter_by(url_slug=slug).first_or_404()
    all_artists = Artist.query.order_by(Artist.name.asc()).all()
    genre_artists = {genre_data.name: []}
    artist_to_genre_info = ArtistToGenre.query.filter_by(genre_id=genre_data.id).all()
    for artist_to_genre in artist_to_genre_info:
        for artist in all_artists:
            if artist.id == artist_to_genre.artist_id:
                genre_artists[genre_data.name].append(artist.to_dict())
    genre_artist_results.append(genre_artists)
    return jsonify(genre_artist_results)


@app.route('/update_user_to_artist', methods=['GET', 'POST'])
@jwt_required()
def update_user_to_artist():
    info = request.json
    artist_id = info.get('artist_id')
    if get_jwt_identity() is not None:
        u2a = UserToArtist.query.filter_by(user_id=get_jwt_identity(), artist_id=artist_id).first()
        if u2a is None:
            u2a = UserToArtist(
                user_id=get_jwt_identity(),
                artist_id=artist_id,
                favorite=True
            )
            db.session.add(u2a)
            db.session.commit()
        elif not u2a.favorite:
            u2a.favorite = True
        else:
            u2a.favorite = False
        db.session.add(u2a)
        db.session.commit()
        return jsonify(u2a.favorite)
    return jsonify(None)


@app.route('/user_profile', methods=['GET'])
@jwt_required()
def user_profile():
    if get_jwt_identity() is not None:
        identity = get_jwt_identity()
        user = User.query.filter_by(id=identity).first()
        if user:
            return jsonify({"email": user.email}), 200


@app.route('/get_user_saved_artists', methods=['GET'])
@jwt_required()
def get_saved_artists():
    u2artists = UserToArtist.query.filter_by(user_id=get_jwt_identity(), favorite=True).all()
    fav_artists = []
    if u2artists is not None:
        for artist in u2artists:
            fav_artists.append(Artist.query.filter_by(id=artist.artist_id).first().to_dict())
        return jsonify(fav_artists)
    else:
        return None


# def get_user_favorite_artists:


@app.route('/schedule')
def schedule():
    all_events = ArtistToPorch.query.all()
    events_list = []
    for event in all_events:
        events_list.append(event.to_dict())
    return jsonify(events_list)


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


@app.route('/location')
def location():
    return jsonify({"map": "TODO"})


@app.route('/plan')
def plan():
    return jsonify({"plan": "TODO"})


@app.route('/about')
def about():
    return jsonify({"about": "TODO"})


@app.route('/newArtist', methods=['GET', 'POST'])
def newArtist():
    form = CreateArtistForm()

    if form.validate_on_submit():
        a = Artist.query.filter_by(name=form.name.data).first()
        if a is not None:
            flash('Artist already exist')
        else:
            b = Artist(name=form.name.data, genre=form.genre.data, hometown=form.hometown.data, about=form.about.data,
                       twitter=form.twitter_url.data, instagram=form.instagram_url.data, spotify=form.spotify_url.data)

            flash('New Artist Created!')
            db.session.add(b)
            db.session.commit()

            f = form.photo.data
            if f:
                extension = f.filename.split(".")[-1]
                filename = str(b.id) + '.' + extension
                f.save(os.path.join(
                    app.static_folder, filename
                ))
            else:
                filename = "img_avatar1.png"

            c = Artist.query.filter_by(name=form.name.data).first()
            c.photo = filename
            db.session.commit()

            return redirect(url_for('artists'))
    return jsonify({"status": True})


@app.route('/newPorch', methods=['GET', 'POST'])
def newPorch():
    form = CreatePorchForm()
    if form.validate_on_submit():
        v = Porch.query.filter_by(address=form.address.data).first()
        if v is not None:
            flash('Porch already exists')
        else:
            w = Porch(address=form.address.data)
            flash('New Porch Created!')
            db.session.add(w)
            db.session.commit()
            return redirect(url_for('index'))
    return jsonify({"status": True})


@app.route('/newEvent', methods=['GET', 'POST'])
def newEvent():
    porch_list = Porch.query.all()
    locations = [(i.id, i.address) for i in porch_list]
    artists_list = Artist.query.all()
    performers = [(y.id, y.name) for y in artists_list]
    form = CreateEventForm()
    form.porch.choices = locations
    form.artist.choices = performers
    if form.validate_on_submit():
        duplicate = False
        a = Artist.query.filter_by(id=form.artist.data).first()
        p = Porch.query.filter_by(id=form.porch.data).first()
        for j in performers:
            if ArtistToPorch.query.filter_by(artist_id=j[0], porch_id=p.id, time=form.time.data).first():
                flash('An artist is already playing this porch at this time')
                duplicate = True

        for k in locations:
            if ArtistToPorch.query.filter_by(artist_id=a.id, porch_id=k[0], time=form.time.data).first():
                flash('This artist is already playing at this time')
                duplicate = True

        if not duplicate:
            x = ArtistToPorch(time=form.time.data, porch_id=form.porch.data, artist_id=form.artist.data)
            flash('New Event Created!')
            db.session.add(x)
            db.session.commit()
            return redirect(url_for('index'))
    return jsonify({"status": True})


@app.route('/populate_db')
def populate_db():
    flash("Populating database with Porchfest data")

    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print('Clear table {}'.format(table))
        db.session.execute(table.delete())
    db.session.commit()
    df = pd.read_csv('data/2019PerformerSchedule.csv', index_col=0, sep=',')
    # Add porches
    porches = df['Porch Address'].unique()
    for i in range(porches.shape[0]):
        porch = Porch(address=porches[i])
        db.session.add(porch)
        db.session.commit()
    # Add artists
    for i in range(df.shape[0]):
        row = df.iloc[i]
        artist = Artist(name=row['Name'], about=row['Description'])
        db.session.add(artist)
        db.session.commit()
    # Add events
    for i in range(df.shape[0]):
        row = df.iloc[i]
        artist = db.session.query(Artist).filter_by(name=row['Name']).first()
        porch = db.session.query(Porch).filter_by(address=row['Porch Address']).first()
        timing = int(row['Assigned Timeslot'].split('-')[0])
        if not timing == 12:
            timing += 12
        time = datetime(2019, 9, 22, timing)
        event = ArtistToPorch(time=time, artist_id=artist.id, porch_id=porch.id)
        db.session.add(event)
        db.session.commit()
    return jsonify({"status": True})


@app.route('/reset_db')
def reset_db():
    flash("Resetting database: deleting old data and repopulating with dummy data")
    # clear all data from all tables
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print('Clear table {}'.format(table))
        db.session.execute(table.delete())
    db.session.commit()
    populate_db()
    return jsonify({"status": True})


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
        porch = Porch(address=porches[i])
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
    photo_url = ["https://scontent-lga3-2.xx.fbcdn.net/v/t1.6435-9/55525887_2096958433757908_600752795271823360_n.jpg?_nc_cat=110&ccb=1-5&_nc_sid=09cbfe&_nc_ohc=SgegyjXIak8AX8fss7R&_nc_ht=scontent-lga3-2.xx&oh=00_AT80IvRBVR2OhmH3uiVUQcSgpo8P2mYQ3fVCvETTM0q1dA&oe=6260560D",
                 "https://scontent-lga3-2.xx.fbcdn.net/v/t1.6435-9/60347829_404865583446217_7485028511070027776_n.jpg?_nc_cat=100&ccb=1-5&_nc_sid=09cbfe&_nc_ohc=CEzpCh2VRooAX_93qx2&_nc_ht=scontent-lga3-2.xx&oh=00_AT9Sx87s4sHFAZ0D1fcaJqVDc7inrhajTvptEt6_CqNbVw&oe=62604C2D",
                 "https://scontent-lga3-2.xx.fbcdn.net/v/t1.18169-9/29542062_10155319538882765_4416304449885024713_n.jpg?_nc_cat=108&ccb=1-5&_nc_sid=09cbfe&_nc_ohc=JGIUsgEjiOgAX9EfKjg&_nc_ht=scontent-lga3-2.xx&oh=00_AT_qn8DzS0ECQFnoNVqmMcDkIK_b8oXwLT0KY7dITK5NQQ&oe=625F629E",
                 "https://scontent-lga3-2.xx.fbcdn.net/v/t1.6435-9/51349617_536239003538676_5810532190991155200_n.jpg?_nc_cat=109&ccb=1-5&_nc_sid=09cbfe&_nc_ohc=KGp7nIhM4RcAX8OKGKq&_nc_ht=scontent-lga3-2.xx&oh=00_AT8UUbp33tFZZ8zCIUDjnFcwQtZnQOz009zMqDVEXs2lSQ&oe=625F9D69",
                 "https://scontent-lga3-2.xx.fbcdn.net/v/t39.30808-6/273648015_464306975152132_8471843295876990111_n.jpg?_nc_cat=104&ccb=1-5&_nc_sid=09cbfe&_nc_ohc=tWRghIcVfwIAX-cdLoO&_nc_ht=scontent-lga3-2.xx&oh=00_AT-ThCPRzO5zFhFjfRr90M7nmXIc07ieXfghLvfDWcEaTA&oe=623F8C65"
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
