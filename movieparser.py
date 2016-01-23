from __future__ import print_function
import xml.sax
import requests
import datetime
import sys
from fuzzywuzzy import fuzz

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
   # create an XMLReader
   parser = xml.sax.make_parser()
   # turn off namepsaces
   parser.setFeature(xml.sax.handler.feature_namespaces, 0)

   # override the default ContextHandler
   Handler = MovieHandler("Show")
   parser.setContentHandler( Handler )

   if place:
      r = requests.get("http://www.finnkino.fi/xml/Schedule/?area=%s" % place)
   else:
      r = requests.get("http://www.finnkino.fi/xml/Schedule/")
   xml.sax.parseString(r.text.encode("UTF-8"), Handler)

   dateformat = "%Y-%m-%dT%H:%M:%S"

   #datetime.datetime.strptime("2016-01-22T23:45:00", "%Y-%m-%dT%H:%M:%S")
   movies = [(datetime.datetime.strptime(x["dttmShowStart"], dateformat),datetime.datetime.strptime(x["dttmShowEnd"], dateformat),x["Title"],x["TheatreAndAuditorium"], x["LengthInMinutes"]) for x in Handler.movies]
   now = datetime.datetime.now()
   return filter(lambda x: x[1] > now,movies)

def areas():
   # create an XMLReader
   parser = xml.sax.make_parser()
   # turn off namepsaces
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

if ( __name__ == "__main__"):
   places = areas()
   venues = dict(places)
   if len(sys.argv) < 2:
      print ("One argument stating area is needed.")
      for v in sorted(venues.keys()):
         print ("%s: %s" % (v, venues[v]))
      sys.exit(0)

   try:
      place = str(int(sys.argv[1]))
   except ValueError:
      place = sorted(map(lambda x: (fuzz.ratio(sys.argv[1],x[1]),x), areas()))[-1][1][0]

   l = movies_place(place)
   for item in l:
      print (nice_line(item))
