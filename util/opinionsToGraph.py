import re

def getNodes(filename, group=0):
    title = False
    body = False
    caseText = ''
    nodeName = ''
    nodes = []
    with open(filename) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if re.match('[0-9]+ of 100 DOCUMENTS', line): #Matches title of a new brief
            if nodeName is not '':
                nodes.append({"name":nodeName,"group":group,"text":caseText})
            caseText = ''
            title = True
            continue
        if re.match('OPINION', line): #Matches body
            title = False
            body = True
        if title:
            reg = '\d+ Cal\..*\d+' #Matches the reference to the case (eg 220 Cal.App.2d 1)
            if re.match(reg, line):
                splitNodeNames = line.split(';')
                nodeName = splitNodeNames[0]
        if body:
            caseText += unicode(line, errors='ignore') + ' '
    return nodes

def getAllNodesAndLinks(nodes, links = []):
    allNodes = nodes
    for op,docNum in zip(nodes,range(0,len(nodes))):
        body = op.get("text")
        reg = '(\d+\s+?Cal\..\s?App\s?.*?\s+\d+)[;|,|\s\[|\.]' #Only gets links with "App" in them
        #reg = '(\d+\s+?Cal\.\s?[a-zA-Z0-9\.]*?\s+?\d+)[;|,|\s\[|\.]+?' #Gets all links
        for result in re.finditer(reg, body):
            for potentialLink in result.groups():
                if not 'at' in potentialLink: #Ignoring things like (55 Cal. App. 4th at p. 1065)
                    foundLink = False
                    for link in allNodes:
                        if link.get("name") == potentialLink:
                            links.append({"source":docNum,\
                                "target":allNodes.index(link),"value":5})
                            foundLink = True
                    if not foundLink:
                        newNodeName = {"name":potentialLink,"group":9,"text":''}
                        allNodes.append(newNodeName)
                        links.append({"source":docNum,\
                            "target":allNodes.index(newNodeName),"value":5})
    return (allNodes, links)

if __name__ == "__main__":
    import argparse, json, os
    parser = argparse.ArgumentParser(description='Get links from a file.')
    parser.add_argument('f', metavar='filename', action='store', help='Directory of files to parse (LexisNexis format)')
    args = parser.parse_args()
    nodes = []
    for aFile,color in zip(os.listdir(args.f),range(0,len(os.listdir(args.f)))):
        nodes += getNodes(args.f + aFile,color)
    (allNodes, links) = getAllNodesAndLinks(nodes)
    with open('opinions.json', 'w') as out:
        out.write(json.dumps({"nodes":allNodes,"links":links}))

