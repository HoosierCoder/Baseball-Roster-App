from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Team, Base, Player, User

engine = create_engine('sqlite:///teamwithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Dennis", email="djohnstts@gmail.com",
             picture='https://lh3.googleusercontent.com/-dwDzFhtRIjU/U0imUbjLOKI/AAAAAAAABjM/pFxCccg_Nu4YZ79WzQCtEE-PRswAxgR1wCEwYBhgL/w140-h140-p/208037_1023666605893_8276_n.jpg')
session.add(User1)
session.commit()

# Reds team
team1 = Team(user_id=1, name="Reds")

session.add(team1)
session.commit()

player1 = Player(user_id=1, name="Roy Hobbs", position="Outfield",
                     games_played="145",  team=team1)

session.add(player1)
session.commit()


player2 = Player(user_id=1, name="Jake Taylor", position="Catcher",
                     games_played="115", team=team1)

session.add(player2)
session.commit()

player3 = Player(user_id=1, name="Reggie Byrd", position="Shortstop",
                     games_played="162", team=team1)

session.add(player3)
session.commit()


player4 = Player(user_id=1, name="Tim Tiger", position="First Base",
                     games_played="120", team=team1)

session.add(player4)
session.commit()

player5 = Player(user_id=1, name="Joe Gentry", position="Second Base",
                     games_played="151", team=team1)

session.add(player5)
session.commit()

player6 = Player(user_id=1, name="Brooke Nettles", position="Third Base",
                     games_played="144", team=team1)

session.add(player6)
session.commit()

player7 = Player(user_id=1, name="George Dunn", position="Outfield",
                     games_played="130", team=team1)

session.add(player7)
session.commit()

player8 = Player(user_id=1, name="Willie Hamilton", position="Outfield",
                     games_played="76", team=team1)

session.add(player8)
session.commit()

player9 = Player(user_id=1, name="Lightning Bugg", position="Pitcher",
                     games_played="40", team=team1)

session.add(player9)
session.commit()

# Tigers
team2 = Team(user_id=1, name="Tigers")

session.add(team2)
session.commit()

player1 = Player(user_id=1, name="Cesaer Snider", position="Outfield",
                     games_played="145",  team=team2)

session.add(player1)
session.commit()


player2 = Player(user_id=1, name="Crash Davis", position="Catcher",
                     games_played="115", team=team2)

session.add(player2)
session.commit()

player3 = Player(user_id=1, name="Slick Jones", position="Shortstop",
                     games_played="162", team=team2)

session.add(player3)
session.commit()


player4 = Player(user_id=1, name="Boog Killer", position="First Base",
                     games_played="120", team=team2)

session.add(player4)
session.commit()

player5 = Player(user_id=1, name="Brady Fipps", position="Second Base",
                     games_played="151", team=team2)

session.add(player5)
session.commit()

player6 = Player(user_id=1, name="Mike Brett", position="Third Base",
                     games_played="144", team=team2)

session.add(player6)
session.commit()

player7 = Player(user_id=1, name="Stan Williams", position="Outfield",
                     games_played="130", team=team2)

session.add(player7)
session.commit()

player8 = Player(user_id=1, name="Mickey Dee", position="Outfield",
                     games_played="86", team=team2)

session.add(player8)
session.commit()

player9 = Player(user_id=1, name="Walter Carlton", position="Pitcher",
                     games_played="40", team=team2)

session.add(player9)
session.commit()

# Angels
team3 = Team(user_id=1, name="Angels")

session.add(team3)
session.commit()

player1 = Player(user_id=1, name="Duke Davis", position="Outfield",
                     games_played="145",  team=team3)

session.add(player1)
session.commit()


player2 = Player(user_id=1, name="Peter Oliver", position="Catcher",
                     games_played="115", team=team3)

session.add(player2)
session.commit()

player3 = Player(user_id=1, name="Ozzie Wagner", position="Shortstop",
                     games_played="162", team=team3)

session.add(player3)
session.commit()


player4 = Player(user_id=1, name="Lou Votto", position="First Base",
                     games_played="120", team=team3)

session.add(player4)
session.commit()

player5 = Player(user_id=1, name="Roger Reese", position="Second Base",
                     games_played="151", team=team3)

session.add(player5)
session.commit()

player6 = Player(user_id=1, name="Alex Bell", position="Third Base",
                     games_played="124", team=team3)

session.add(player6)
session.commit()

player7 = Player(user_id=1, name="Barry Horton", position="Outfield",
                     games_played="130", team=team3)

session.add(player7)
session.commit()

player8 = Player(user_id=1, name="Edd Stubbs", position="Outfield",
                     games_played="133", team=team3)

session.add(player8)
session.commit()

player9 = Player(user_id=1, name="Warren Johnson", position="Pitcher",
                     games_played="40", team=team3)

session.add(player9)
session.commit()

print "added players!"
