from flask import jsonify
from flask import request

from app import app
from app.models import *


@app.route('/artist/<string:slug>', methods=['GET', 'POST'])
def get_slug_artist(slug):
    info = request.json
    user = None
    if info is not None:
        user = User.query.filter_by(access_token=info.get('access_token')).first()
    artist_data = Artist.query.filter_by(url_slug=slug).first_or_404()
    artist_porch = ArtistToPorch.query.filter_by(artist_id=artist_data.id).first()
    artist_location = Porch.query.filter_by(id=artist_porch.porch_id).first()
    if user:
        favoriteArtist = UserToArtist.query.filter(UserToArtist.artist_id == artist_data.id,
                                                   UserToArtist.user_id == user.id).first()
        if favoriteArtist is not None:
            result = {"artist": artist_data.to_dict(), 'liked': favoriteArtist.favorite, 'location': artist_location}
            return jsonify(result)
    result = {"artist": artist_data.to_dict(), 'location': artist_location.address}
    return jsonify(result)


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
        for genre in all_genres:
            genre_artists = {"genre_slug": genre.url_slug, "artists": [], "genre": genre.name.capitalize()}
            artist_to_genre_info = ArtistToGenre.query.filter_by(genre_id=genre.id).all()
            for artist_to_genre in artist_to_genre_info:
                for artist in all_artists:
                    if artist.id == artist_to_genre.artist_id:
                        genre_artists["artists"].append(artist.to_dict())
            genre_artist_results.append(genre_artists)

        return jsonify(genre_artist_results)


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
