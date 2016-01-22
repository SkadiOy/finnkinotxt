from __future__ import print_function
import xml.sax
import requests
import datetime
import sys

class MovieHandler( xml.sax.ContentHandler ):
   def __init__(self):
      self.CurrentData = ""
      self.movies = []
      self.current = {}

   # Call when an element starts
   def startElement(self, tag, attributes):
      self.CurrentData = tag

   # Call when an elements ends
   def endElement(self, tag):
      if tag == "Show":
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
   Handler = MovieHandler()
   parser.setContentHandler( Handler )
   kinop = place

   r = requests.get("http://www.finnkino.fi/xml/Schedule/?area=%s" % kinop)
   xml.sax.parseString(r.text.encode("UTF-8"), Handler)

   dateformat = "%Y-%m-%dT%H:%M:%S"

   #datetime.datetime.strptime("2016-01-22T23:45:00", "%Y-%m-%dT%H:%M:%S")
   movies = [(datetime.datetime.strptime(x["dttmShowStart"], dateformat),datetime.datetime.strptime(x["dttmShowEnd"], dateformat),x["Title"],x["TheatreAndAuditorium"]) for x in Handler.movies]
   now = datetime.datetime.now()
   return filter(lambda x: x[1] > now,movies)


if ( __name__ == "__main__"):
   if len(sys.argv) < 2:
      print ("One argument stating area is needed.")
      sys.exit(0)

   l = movies_place(sys.argv[1])
   print(l)
