#!/usr/local/bin/python
import cgi, cgitb, json, os
import opinionsToGraph as OTG
cgitb.enable()

print "Content-Type: text/html"
print

print """
<form>
<center><input type="text" name="searchTerm"><input type="submit" value="Go"></center>
</form>
"""

form = cgi.FieldStorage()
try:
    searchTerm = form["searchTerm"].value
    nodes = OTG.getNodes('/Users/andrewgambardella/Sites/data/' + searchTerm + '.txt')
    (allNodes, links) = OTG.getAllNodesAndLinks(nodes)
    os.system('rm /Users/andrewgambardella/Sites/opinions.json')
    with open('/Users/andrewgambardella/Sites/opinions.json', 'w') as out:
        out.write(json.dumps({"nodes":allNodes,"links":links}))
    print """
    <iframe id="graph" width="70%" height="90%" src="http://localhost/~andrewgambardella/graph.html"></iframe>
    <iframe id="info" width="29%" height="90%" src="http://localhost/~andrewgambardella/info.html"></iframe>
    """
except:
    pass
