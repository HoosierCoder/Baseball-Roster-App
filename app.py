from flask import Flask, render_template, request, redirect, jsonify
from flask import url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool
from database_setup import Base, Team, Player, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Team Menu Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///teamwithusers.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# Open a facebook connection for login
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print("access token received %s " % access_token)

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type= \
            fb_exchange_token&client_id=%s&client_secret= \
            %s&fb_exchange_token=%s' % ( \
            app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange
        we have to split the token first on commas and select the first index
        which gives us the key : value for the server access token then we
        split it on colons to pull out the actual token value and replace the
        remaining quotes with nothing so that it can be used directly in the
        graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token= \
            %s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token= \
        %s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;'
    output += 'border-radius: 150px;-webkit-border-radius: 150px;'
    output += '-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

# Logout and disconnect the facebook connection
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# Connect via Google using google tokens
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                        'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;'
    output += 'border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

# User Helper Functions


# Create a new application user
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# From session infomration, grab the user info
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Grab user id
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
                                'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Team Information
@app.route('/team/<int:team_id>/roster/JSON')
def teamRosterJSON(team_id):
    team = session.query(Team).filter_by(id=team_id).one()
    items = session.query(Player).filter_by(
        team_id=team_id).all()
    return jsonify(Player=[i.serialize for i in items])


# Grab the player info and use JSON to format the information
@app.route('/team/<int:team_id>/roster/<int:player_id>/JSON')
def playerJSON(team_id, player_id):
    Roster_Item = session.query(Player).filter_by(id=player_id).one()
    return jsonify(Roster_Item=Roster_Item.serialize)


# JSON formatting of the team info to return in the response
@app.route('/team/JSON')
def teamsJSON():
    teams = session.query(Team).all()
    return jsonify(teams=[r.serialize for r in teams])


# Show all restaurants
@app.route('/')
@app.route('/team/')
def showTeams():
    teams = session.query(Team).order_by(asc(Team.name))
    if 'username' not in login_session:
        return render_template('publicteams.html', teams=teams)
    else:
        return render_template('teams.html', teams=teams)

# Create a new team
@app.route('/team/new/', methods=['GET', 'POST'])
def newTeam():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if not request.form['name']:
	    flash('Please add team name')
            return redirect(url_for('newTeam'))
        
        newTeam = Team(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newTeam)
        flash('Team %s Successfully Created' % newTeam.name)
        session.commit()
        return redirect(url_for('showTeams'))
    else:
        return render_template('newTeam.html')

# Edit a team
@app.route('/team/<int:team_id>/edit/', methods=['GET', 'POST'])
def editTeam(team_id):
    editedTeam = session.query(
        Team).filter_by(id=team_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedTeam.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized \
                to edit this roster. Please create your own team in order to \
                edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedTeam.name = request.form['name']
            flash('Team Successfully Edited %s' % editedTeam.name)
            return redirect(url_for('showTeams'))
    else:
        return render_template('editTeam.html', team=editedTeam)


# Delete a team
@app.route('/team/<int:team_id>/delete/', methods=['GET', 'POST'])
def deleteTeam(team_id):
    teamToDelete = session.query(
        Team).filter_by(id=team_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if teamToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized \
                to delete this team. Please create your own team in order to \
                delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(teamToDelete)
        flash('%s Successfully Deleted' % teamToDelete.name)
        session.commit()
        return redirect(url_for('showTeams', team_id=team_id))
    else:
        return render_template('deleteTeam.html', team=teamToDelete)


# Show a team roster
@app.route('/team/<int:team_id>/')
@app.route('/team/<int:team_id>/roster/')
def showRoster(team_id):
    team = session.query(Team).filter_by(id=team_id).one()
    creator = getUserInfo(team.user_id)
    print("Team: " + str(team_id ) )
    items = session.query(Player).filter_by(
        team_id=team_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template(
            'publicroster.html', items=items, team=team, creator=creator)
    else:
        return render_template(
            'roster.html', items=items, team=team, creator=creator)


# Create a new player
@app.route('/team/<int:team_id>/roster/new/', methods=['GET', 'POST'])
def newPlayer(team_id):
    if 'username' not in login_session:
        return redirect('/login')
    team = session.query(Team).filter_by(id=team_id).one()
    if login_session['user_id'] != team.user_id:
        return "<script>function myFunction() {alert('You are not authorized \
                to add players to this team. Please create your own team in \
                order to add players.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if not request.form['name']:
	    flash('Please add player name')
            return redirect(url_for('newPlayer', team_id=team_id))

        playerPosition = request.form.get("position","")
        if playerPosition == "":
            flash('Please select player position')
            return redirect(url_for('newPlayer', team_id=team_id))
            
        if not request.form['games_played']:
	    flash('Please enter games played')
            return redirect(url_for('newPlayer', team_id=team_id))
        
        newItem = Player(
                name=request.form['name'], position=request.form['position'],
                            games_played=request.form['games_played'],
                            team_id=team_id, user_id=team.user_id)
        session.add(newItem)
        session.commit()
        flash('New Player %s Successfully added to roster' % (newItem.name))
        return redirect(url_for('showRoster', team_id=team_id))
    else:
        return render_template('newplayer.html', team_id=team_id)

# Edit a player
@app.route('/team/<int:team_id>/roster/<int:player_id>/edit', methods=['GET', 'POST'])
def editPlayer(team_id, player_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Player).filter_by(id=player_id).one()
    team = session.query(Team).filter_by(id=team_id).one()
    if login_session['user_id'] != team.user_id:
        return "<script>function myFunction() {alert('You are not \
                authorized to edit the roster of this team. Please \
                create your own team to update the roster.');}\
                </script><body onload='myFunction()'>"
    if request.method == 'POST':
        if not request.form['name']:
	    flash('Please add player name')
            return redirect(url_for('editPlayer', team_id=team_id, \
                                    player_id=player_id))

        playerPosition = request.form.get("position","")
        if playerPosition == "":
            flash('Please select player position')
            return redirect(url_for('editPlayer', team_id=team_id, \
                                    player_id=player_id))

        gamesPlayed = request.form.get("gamesplayed","")   
        if gamesPlayed == "":
	    flash('Please enter games played')
            return redirect(url_for('editPlayer', team_id=team_id, \
                                    player_id=player_id))
        
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['position']:
            editedItem.position = request.form['position']
        if request.form['gamesplayed']:
            editedItem.games_played = request.form['gamesplayed']
        session.add(editedItem)
        session.commit()
        flash('Player Successfully Edited')
        return redirect(url_for('showRoster', team_id=team_id))
    else:
        return render_template('editplayer.html', team_id=team_id,
                               player_id=player_id, item=editedItem)

# Delete a player
@app.route('/team/<int:team_id>/roster/<int:player_id>/delete',
                                           methods=['GET', 'POST'])
def deletePlayer(team_id, player_id):
    if 'username' not in login_session:
        return redirect('/login')
    team = session.query(Team).filter_by(id=team_id).one()
    itemToDelete = session.query(Player).filter_by(id=player_id).one()
    if login_session['user_id'] != team.user_id:
        return "<script>function myFunction() {alert('You are not authorized \
                to delete players from this team. Please create your own team \
                in order to delete players.');}\
                </script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Player Successfully Deleted')
        return redirect(url_for('showRoster', team_id=team_id))
    else:
        return render_template('deleteplayer.html', item=itemToDelete)

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showTeams'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showTeams'))

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
