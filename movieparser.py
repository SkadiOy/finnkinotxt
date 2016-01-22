from __future__ import print_function
import xml.sax
import requests


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
  


if ( __name__ == "__main__"):
   
   # create an XMLReader
   parser = xml.sax.make_parser()
   # turn off namepsaces
   parser.setFeature(xml.sax.handler.feature_namespaces, 0)

   # override the default ContextHandler
   Handler = MovieHandler()
   parser.setContentHandler( Handler )

   r = requests.get("http://www.finnkino.fi/xml/Schedule/")
   xml.sax.parseString(r.text.encode("UTF-8"), Handler)
   print (Handler.movies)
