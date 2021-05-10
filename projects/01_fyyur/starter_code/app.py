#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
# moment is used for date and time rendering
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
from models import db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
# .from_object() allows us to separate the config elements out to another file
app.config.from_object('config')
db.init_app(app)

# TODO: connect to a local postgresql database - DONE
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

# registering filters in Jinja2: https://flask.palletsprojects.com/en/1.1.x/templating/#registering-filters
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
  # TODO: replace with real venues data. - DONE
  #       num_shows should be aggregated based on number of upcoming shows per venue. - DONE
  # SELECT the list of venues DISTINCT ON city and state
  areas = Venue.query.distinct(Venue.city, Venue.state).order_by('state').all()
  # empty list to store the output to the view
  data = []
  # loop through the query result
  for area in areas:
    # filter for venues WHERE state == area.state AND city == area.city
    venue_filter = Venue.query.\
      filter_by(state=area.state).\
        filter_by(city=area.city).\
          order_by('name').\
            all()
    # empty list to store the venue dictionary ready to be appended into the data list variable
    venue_data = []
    # I think data.append is setting the key/value from each list-type 'area' iterable in the for loop
    # 'venues' value is initialised to the venue_data empty list, but gets appeneded in the nested loop
    data.append({
        'city':area.city,
        'state':area.state,
        'venues':venue_data
      })
    # nested loop goes through the venue_filter and appends the venue_data dictionary details
    for venue in venue_filter:
      venue_data.append({
        'id':venue.id,
        'name':venue.name,
        # this filter returns a number of records in a list, but we can use len() as a way to count the number of items in that list
        'num_upcoming_shows': len(Show.query.\
          filter(Show.venue_id==venue.id).\
            filter(Show.start_time>datetime.now()).\
              all())
      })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive. - DONE
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  name_search = request.form["search_term"]
  search = "%{}%".format(name_search)
  search_venue = db.session.query(
    Venue.id,
    Venue.name).\
      filter(Venue.name.ilike(search)).\
        all()
  
  venue_data = []
  for venue in search_venue:
    venue_data.append({
      "id": venue.id,
      "name": venue.name
    })

  response = {
    "count": len(search_venue),
    "data": venue_data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id - DONE
  venue = Venue.query.get(venue_id)

  # Past Shows ----------------------------------------- #
  past_shows = db.session.query(
    Artist.id,
    Artist.name,
    Artist.image_link,
    Show.start_time).\
    join(Artist).\
      filter(Show.venue_id==venue_id).\
        filter(Show.start_time<datetime.now()).\
          order_by(Show.start_time).\
            all()
  
  past_show_data = []
  for show in past_shows:
    past_show_data.append({
      "artist_id": show[0],
      "artist_name": show[1],
      "artist_image_link": show[2],
      "start_time": format_datetime(str(show[3]))
    })
  
  # Upcoming Shows ----------------------------------------- #
  upcoming_shows = db.session.query(
    Artist.id,
    Artist.name,
    Artist.image_link,
    Show.start_time).\
    join(Artist).\
      filter(Show.venue_id==venue_id).\
        filter(Show.start_time>datetime.now()).\
          order_by(Show.start_time).\
            all()
  upcoming_show_data = []
  for show in upcoming_shows:
    upcoming_show_data.append({
      "artist_id": show[0],
      "artist_name": show[1],
      "artist_image_link": show[2],
      "start_time": format_datetime(str(show[3]))
    })

  # Venue Data ----------------------------------------- #
  data = {
    "id": venue_id,
    "name": venue.name,
    "address": venue.address,
    "genres": venue.genres,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "upcoming_shows": upcoming_show_data,
    "past_shows": past_show_data,
    "past_shows_count": len(past_show_data),
    "upcoming_shows_count": len(upcoming_show_data)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead - DONE
  error = False
  body = {}
  form = VenueForm(request.form)
  try:
    venue = Venue(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      address=form.address.data,
      phone=form.phone.data,
      genres=form.genres.data,
      facebook_link=form.facebook_link.data,
      image_link=form.image_link.data,
      website_link=form.website_link.data,
      seeking_talent=form.seeking_talent.data,
      seeking_description=form.seeking_description.data
    )
    db.session.add(venue)
    db.session.flush()
    venue_id = venue.id
    db.session.commit()
    body['id'] = venue_id
    body['name'] = venue.name
    body['city'] = venue.city
    body['state'] = venue.state
    body['address'] = venue.address
    body['phone'] = venue.phone
    body['genres'] = venue.genres
    body['facebook_link'] = venue.facebook_link
    body['image_link'] = venue.image_link
    body['seeking_talent'] = venue.seeking_talent
    body['seeking_description'] = venue.seeking_description
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    return render_template('pages/home.html')
  else:
    print('I am body before being returned to the view', body)
  # TODO: modify data to be the data object returned from db insertion
  # on successful db insert, flash success - DONE
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead. - DONE
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using - DONE
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue was successfully deleted!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue could not be deleted.')
  finally:
    db.session.close()
  return redirect(url_for('index'))
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage - DONE
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database - DONE
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive. - DONE
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band". - DONE
  # search for "band" should return "The Wild Sax Band". - DONE
  # get the form data from the "search_term" field
  name_search = request.form["search_term"]
  # wrap the search term text in % ready for ILIKE statement
  search = "%{}%".format(name_search)
  # search query using the resulting search term as an input
  search_artist = db.session.query(
    Artist.id,
    Artist.name).\
      filter(Artist.name.ilike(search)).\
        all()
  
  artist_data = []
  # loop through each result in the list to create the relevant dictionary that can be parsed by the view
  for artist in search_artist:
    artist_data.append({
      "id": artist.id,
      "name": artist.name
    })

  # populate the response dictionary with artist_data
  response = {
    "count": len(search_artist),
    "data": artist_data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id - DONE
  artist = Artist.query.get(artist_id)

  # Past Shows ----------------------------------------- #
  past_shows = db.session.query(
    Venue.id,
    Venue.name,
    Venue.image_link,
    Show.start_time).\
    join(Venue).\
      filter(Show.artist_id==artist_id).\
        filter(Show.start_time<datetime.now()).\
          order_by(Show.start_time).\
            all()
  
  past_show_data = []
  for show in past_shows:
    past_show_data.append({
      "venue_id": show[0],
      "venue_name": show[1],
      "venue_image_link": show[2],
      "start_time": format_datetime(str(show[3]))
    })

  # Upcoming Shows ----------------------------------------- #
  upcoming_shows = db.session.query(
    Venue.id,
    Venue.name,
    Venue.image_link,
    Show.start_time).\
    join(Venue).\
      filter(Show.artist_id==artist_id).\
        filter(Show.start_time>datetime.now()).\
          order_by(Show.start_time).\
            all()
  upcoming_show_data = []
  for show in upcoming_shows:
    upcoming_show_data.append({
      "venue_id": show[0],
      "venue_name": show[1],
      "venue_image_link": show[2],
      "start_time": format_datetime(str(show[3]))
    })


  # Artist Data ----------------------------------------- #
  data = {
    "id": artist_id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_show_data,
    "upcoming_shows": upcoming_show_data,
    "past_shows_count": len(past_show_data),
    "upcoming_shows_count": len(upcoming_show_data)
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  # TODO: populate form with fields from artist with ID <artist_id> - DONE
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing - DONE
  # artist record with ID <artist_id> using the new attributes
  error = False
  form = ArtistForm(request.form)
  try:
    artist = Artist.query.get(artist_id)
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = form.genres.data
    artist.facebook_link = form.facebook_link.data
    artist.image_link = form.image_link.data
    artist.website_link = form.website_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
    return render_template('pages/home.html')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  # TODO: populate form with values from venue with ID <venue_id> - DONE
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing - DONE
  # venue record with ID <venue_id> using the new attributes
  error = False
  form = VenueForm(request.form)
  print("I am form name: ", form.name.data)
  try:
    venue = Venue.query.get(venue_id)
    print("Name: ", venue.name)
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.genres = form.genres.data
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
    return render_template('pages/home.html')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
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
  # TODO: insert form data as a new Venue record in the db, instead - DONE
  # TODO: modify data to be the data object returned from db insertion - DONE
  error = False
  body = {}
  form = ArtistForm(request.form)
  try:
    artist = Artist(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      phone=form.phone.data,
      genres=form.genres.data,
      facebook_link=form.facebook_link.data,
      image_link=form.image_link.data,
      website_link=form.website_link.data,
      seeking_venue=form.seeking_venue.data,
      seeking_description=form.seeking_description.data
    )
    db.session.add(artist)
    db.session.flush()
    artist_id = artist.id
    db.session.commit()
    body['id'] = artist_id
    body['name'] = artist.name
    body['city'] = artist.city
    body['state'] = artist.state
    body['phone'] = artist.phone
    body['genres'] = artist.genres
    body['facebook_link'] = artist.facebook_link
    body['image_link'] = artist.image_link
    body['seeking_venue'] = artist.seeking_venue
    body['seeking_description'] = artist.seeking_description
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    return render_template('pages/home.html')
  else:
    print('I am body before being returned to the view', body)
  # on successful db insert, flash success - DONE
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead. - DONE
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data. - DONE
  #       num_shows should be aggregated based on number of upcoming shows per venue. - DONE
  shows = Show.query.all()
  data = []
  for show in shows:
    # only return shows that happen in the future
    if show.start_time > datetime.now():
      data.append({
        # remember, we can access parent relationships (defined in the model) through the child.some_parent.some_parent_attribute syntax
        # in this case, show.venue.name is leveraging db.relationship defined against Venue() to get the name of the venue
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(str(show.start_time))
      })
    else:
      pass
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead - DONE
  error = False
  body = {}
  form = ShowForm(request.form)
  try:
    show = Show(
      artist_id=form.artist_id.data,
      venue_id=form.venue_id.data,
      start_time=form.start_time.data
    )
    db.session.add(show)
    db.session.flush()
    show_id = show.id
    db.session.commit()
    body['id'] = show_id
    body['artist_id'] = show.artist_id
    body['venue_id'] = show.venue_id
    body['start_time'] = show.start_time
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show could not be listed.')
    return render_template('pages/home.html')
  else:
    print('I am body before being returned to the view', body)
  # on successful db insert, flash success - DONE
    flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead. - DONE
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

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
