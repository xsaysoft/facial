import os

# You need to replace the next values with the appropriate values for your configuration

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = True
# Uncomment  if you want to use PostgreSql, 
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'facial.db')
#SQLALCHEMY_DATABASE_URI = "postgresql://username:password@localhost/database_name"


