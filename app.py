#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate=Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = "venue"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  genres = db.Column(db.ARRAY(db.String(120)), nullable=False)
  address = db.Column(db.String(200), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  website = db.Column(db.String(500), nullable=True)
  facebook_link = db.Column(db.String(500), nullable=True)
  image_link = db.Column(db.String(500), nullable=True)
  seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.String(), nullable=True)

  def __repr__(self):
    return (f"<Venue id: {self.id}, name: {self.name}, genres: {self.genres}, address: {self.address}, "
            f"city: {self.city }, state: {self.state}, phone: {self.phone}, website: {self.website}, "
            f"facebook_link: {self.facebook_link}, image_link: {self.image_link}, seeking_talent: {self.seeking_talent}, "
            f"seeking_description: {self.seeking_description} >")

class Artist(db.Model):
  __tablename__ = "artist"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  genres = db.Column(db.ARRAY(db.String(120)), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  website = db.Column(db.String(500), nullable=True)
  facebook_link = db.Column(db.String(500), nullable=True)
  image_link = db.Column(db.String(500), nullable=True)
  seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.String(), nullable=True)

  def __repr__(self):
    return (f"<Venue id: {self.id}, name: {self.name}, genres: {self.genres}, "
            f"city: {self.city }, state: {self.state}, phone: {self.phone}, website: {self.website}, "
            f"facebook_link: {self.facebook_link}, image_link: {self.image_link}, seeking_venue: {self.seeking_venue}, "
            f"seeking_description: {self.seeking_description} >")

class Show(db.Model):
  __tablename__ = "show"

  venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey("artist.id"), primary_key=True)
  start_time = db.Column(db.DateTime, nullable=False, primary_key=True)
  venue = db.relationship(Venue, backref=db.backref("shows", lazy="dynamic",cascade="all, delete-orphan"))
  artist = db.relationship(Artist, backref=db.backref("shows", lazy="dynamic", cascade="all, delete-orphan"))

  def __repr__(self):
    return f"<Show venue_id: {self.venue_id}, artist_id: {self.artist_id}, start_time: {self.start_time} >"

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  for location in Venue.query.group_by(Venue.state, Venue.city).with_entities(Venue.state, Venue.city).order_by("state", "city"):
    location_venues = []
    for v in Venue.query.filter_by(state = location.state, city = location.city).order_by("id"):
      location_venues.append({
        "id" : v.id,
        "name" : v.name,
        "num_upcoming_shows": len(v.shows.filter(Show.start_time >= datetime.now()).all())
      })

    location_data = {
      "city": location.city,
      "state": location.state,
      "venues": location_venues
    }
    data.append(location_data)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # case-insensitive search
  search_term = request.form.get("search_term", "")
  result = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
  response={
    "count": len(result),
    "data": result
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id

  venue = Venue.query.get(venue_id)
  shows = venue.shows
  shows_data = {}
  past_shows = shows.filter(Show.start_time < datetime.now()).order_by(db.desc(Show.start_time)).all()
  shows_data["past_shows_count"] = len(past_shows)
  shows_data["past_shows"] = []
  for s in past_shows:
    shows_data["past_shows"].append({
      "artist_id": s.artist_id,
      "artist_name": s.artist.name,
      "artist_image_link": s.artist.image_link,
      "start_time": str(s.start_time)
    })
  upcoming_shows = shows.filter(Show.start_time >= datetime.now()).order_by(Show.start_time).all()
  shows_data["upcoming_shows_count"] = len(upcoming_shows)
  shows_data["upcoming_shows"] = []
  for s in upcoming_shows:
    shows_data["upcoming_shows"].append({
      "artist_id": s.artist_id,
      "artist_name": s.artist.name,
      "artist_image_link": s.artist.image_link,
      "start_time": str(s.start_time)
  })

  return render_template('pages/show_venue.html', venue=venue, shows=shows_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  name = request.form["name"]
  try:
    venue = Venue(
      name = request.form["name"],
      genres = request.form.getlist("genres"),
      address = request.form["address"],
      city = request.form["city"],
      state = request.form["state"],
      phone = request.form["phone"],
      website = request.form["website"],
      facebook_link = request.form["facebook_link"],
      image_link = request.form["image_link"],
      seeking_talent = True if request.form.get("seeking") == "y" else False,
      seeking_description = request.form["seeking_description"]
    )
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash(f"Venue \"{venue.name}\" with ID: {venue.id} was successfully listed!")
  except:
    db.session.rollback()
    print(sys.exc_info())
    # on unsuccessful db insert, flash an error
    flash(f"An error occurred. Venue \"{name}\" could not be listed.")
  finally:
    db.session.close()

    return redirect(url_for("index"))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  #  delete a record. Handle cases where the session commit could fail.

  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash(f"Venue \"{venue.name}\" with ID: {venue.id} was successfully deleted!")
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(f"An error occurred. Venue could not be deleted.")
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return jsonify({ 'success': True })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.order_by("id").all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # case-insensitive search

  search_term = request.form.get("search_term", "")
  result = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  response={
    "count": len(result),
    "data": result
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  artist = Artist.query.get(artist_id)
  shows = artist.shows
  shows_data = {}
  past_shows = shows.filter(Show.start_time < datetime.now()).order_by(db.desc(Show.start_time)).all()
  shows_data["past_shows_count"] = len(past_shows)
  shows_data["past_shows"] = []
  for s in past_shows:
    shows_data["past_shows"].append({
      "venue_id" : s.venue_id,
      "venue_name": s.venue.name,
      "venue_image_link": s.venue.image_link,
      "start_time": str(s.start_time)
    })
  upcoming_shows = shows.filter(Show.start_time >= datetime.now()).order_by(Show.start_time).all()
  shows_data["upcoming_shows_count"] = len(upcoming_shows)
  shows_data["upcoming_shows"] = []
  for s in upcoming_shows:
    shows_data["upcoming_shows"].append({
      "venue_id" : s.venue_id,
      "venue_name": s.venue.name,
      "venue_image_link": s.venue.image_link,
      "start_time": str(s.start_time)
    })

  return render_template('pages/show_artist.html', artist=artist, shows=shows_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form["name"]
    artist.city = request.form["city"]
    artist.state = request.form["state"]
    artist.phone = request.form["phone"]
    artist.genres = request.form["genres"]
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  #  take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form["name"]
    venue.city = request.form["city"]
    venue.state = request.form["state"]
    venue.address = request.form["address"]
    venue.phone = request.form["phone"]
    venue.genres = request.form["genres"]
    venue.facebook_link = request.form["facebook_link"]
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  name = request.form["name"]
  try:
    artist = Artist(
      name = request.form["name"],
      genres = request.form.getlist("genres"),
      city = request.form["city"],
      state = request.form["state"],
      phone = request.form["phone"],
      website = request.form["website"],
      facebook_link = request.form["facebook_link"],
      image_link = request.form["image_link"],
      seeking_venue = True if request.form.get("seeking") == "y" else False,
      seeking_description = request.form["seeking_description"]
    )
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash(f"Artist \"{artist.name}\" with ID: {artist.id} was successfully listed!")
  except:
    db.session.rollback()
    print(sys.exc_info())
    # on unsuccessful db insert, flash an error instead.
    flash(f"An error occurred. Artist \"{name}\" could not be listed.")
  finally:
    db.session.close()
  return redirect(url_for("index"))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows

  data = []
  for show in Show.query.order_by("start_time"):
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  try:
    # on successful db insert, flash success
    show = Show(
      venue_id = request.form["venue_id"],
      artist_id = request.form["artist_id"],
      start_time = request.form["start_time"]
    )
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    # on unsuccessful db insert, flash an error instead
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

  return redirect(url_for("index"))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
