# Baseball Roster App
This web app is a project for the Udacity [FSND Course](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).

## About
This app utilizes the Flask framework which accesses a SQL database that populates categories and their items. OAuth2 provides authentication for further CRUD functionality on the application. Currently OAuth2 is implemented for Google Accounts.

## In This Repo
The main program for this is application is app.py and it runs the Flask application. A SQL database is created using the database_setup.py code.  The initial population of the database is done via the teamrosters.py program.  The Flask application uses stored HTML templates in the templates folder to build the front-end of the application. The static directory stores javascript, css and images used to enhance the user experience.

## Installation
There are some dependancies and a few instructions on how to run the application.
Seperate instructions are provided to get GConnect working also.

## Dependencies
- [Vagrant](https://www.vagrantup.com/)
- [Udacity Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm)
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

## How to Install
1. Install Vagrant & VirtualBox
2. Clone the Udacity Vagrantfile
3. Go to Vagrant directory and either clone this repo or download and place zip here
3. Launch the Vagrant VM (`vagrant up`)
4. Log into Vagrant VM (`vagrant ssh`)
5. Navigate to /vagrant as instructed in terminal window
6. The app imports requests which is not on this vm. Run sudo pip install requests
7. Setup application database `python database_setup.py`
8. Insert initial rosters by typing python teamrosters.py`
9. Run application using `python app.py`
10. Access the application locally using http://localhost:5000
