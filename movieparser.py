from __future__ import print_function
import xml.sax
import requests
import datetime
import sys
from fuzzywuzzy import fuzz
import boto3
from base64 import b64decode
from urlparse import parse_qs
import logging

class MovieHandler( xml.sax.ContentHandler ):
   def __init__(self, endtag):
      self.CurrentData = ""
      self.movies = []
      self.current = {}
      self.endtag = endtag

   # Call when an element starts
   def startElement(self, tag, attributes):
      self.CurrentData = tag

   # Call when an elements ends
   def endElement(self, tag):
      if tag == self.endtag:
         self.movies.append(self.current)
         self.current = {}

      self.CurrentData = ""

   # Call when a character is read
   def characters(self, content):
      self.current[self.CurrentData] = content
  
def movies_place(place):
   parser = xml.sax.make_parser()
   parser.setFeature(xml.sax.handler.feature_namespaces, 0)

   Handler = MovieHandler("Show")
   parser.setContentHandler( Handler )

   if place:
      r = requests.get("http://www.finnkino.fi/xml/Schedule/?area=%s" % place)
   else:
      r = requests.get("http://www.finnkino.fi/xml/Schedule/")
   xml.sax.parseString(r.text.encode("UTF-8"), Handler)

   dateformat = "%Y-%m-%dT%H:%M:%S"

   movies = [(datetime.datetime.strptime(x["dttmShowStart"], dateformat),datetime.datetime.strptime(x["dttmShowEnd"], dateformat),x["Title"],x["TheatreAndAuditorium"], x["LengthInMinutes"]) for x in Handler.movies]
   now = datetime.datetime.now()
   return filter(lambda x: x[1] > now,movies)

def areas():
   parser = xml.sax.make_parser()
   parser.setFeature(xml.sax.handler.feature_namespaces, 0)

   # override the default ContextHandler
   Handler = MovieHandler("TheatreArea")
   parser.setContentHandler( Handler )

   r = requests.get("http://www.finnkino.fi/xml/TheatreAreas/")
   xml.sax.parseString(r.text.encode("UTF-8"), Handler)
   areas = [(x["ID"], x["Name"]) for x in Handler.movies]
   return areas

def nice_line(item):
   ts = datetime.datetime.strftime(item[0], "%H.%M")
   return "%s: %s, %s, kesto %s min" % (ts,item[2],item[3],item[4])

def arg_to_place(arg, places):
   try:
      place = str(int(arg))
   except ValueError:
      place = sorted(map(lambda x: (fuzz.ratio(arg,x[1]),x), places))[-1][1][0]
   return place



ENCRYPTED_EXPECTED_TOKEN = "CiCMaLgbIgY1tALBXOBOLadCqNPKt+QxKJGf5FAWfr+cIhKfAQEBAgB4jGi4GyIGNbQCwVzgTi2nQqjTyrfkMSiRn+RQFn6/nCIAAAB2MHQGCSqGSIb3DQEHBqBnMGUCAQAwYAYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAy+8y6StK4ViPcWHV4CARCAMzX7xGBzE0Xpq5eywF3FnnOyQNTkErQ3vx2aWXHY/5I9u1oBgz4UJVkGH6BAOjQaxw0Yeg==" # Enter the base-64 encoded, encrypted Slack command token (CiphertextBlob)

kms = boto3.client('kms')
expected_token = kms.decrypt(CiphertextBlob = b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    req_body = event['body']
    params = parse_qs(req_body)
    token = params['token'][0]
    if token != expected_token:
        logger.error("Request token (%s) does not match expected", token)
        raise Exception("Invalid request token")

    user = params['user_name'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]
    command_text = params['text'][0]

    return "%s invoked %s in %s with the following text: %s" % (user, command, channel, command_text)


if ( __name__ == "__main__"):
   places = areas()
   venues = dict(places)
   if len(sys.argv) < 2:
      print ("One argument stating area is needed.")
      for v in sorted(venues.keys()):
         print ("%s: %s" % (v, venues[v]))
      sys.exit(0)


   l = movies_place(arg_to_place(sys.argv[1], places))
   for item in l:
      print (nice_line(item))
