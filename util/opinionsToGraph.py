import re, nltk
from nltk.tokenize import punkt

def getNodes(filename, group=0):
    """
    Gets nodes for the d3 representation of the graph
    """
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
    """
    Gets edges from the nodes gotten in getNodes and also makes
    nodes for newly-discovered cases (ones for which we don't have the text)
    """
    allNodes = nodes
    for op,docNum in zip(nodes,range(0,len(nodes))):
        body = op.get("text")
        #reg = '(\d+\s+?Cal\..\s?App\s?.*?\s+\d+)[;|,|\s\[|\.]' #Only gets links with "App" in them
        reg = '(\d+\s+?Cal\.\s?[a-zA-Z0-9\.]*?\s+?\d+)[;|,|\s\[|\.]+?' #Gets all links
        for result in re.finditer(reg, body):
            for potentialLink in result.groups():
                if not 'at' in potentialLink: #Ignoring things like (55 Cal. App. 4th at p. 1065)
                    foundLink = False
                    for link in allNodes:
                        if link.get("name") == potentialLink:
                            links.append({"source":docNum,\
                                "target":allNodes.index(link),"value":5,
                                "text":allNodes[docNum].get("text")})
                            foundLink = True
                    if not foundLink:
                        newNodeName = {"name":potentialLink,"group":9,"text":''}
                        allNodes.append(newNodeName)
                        links.append({"source":docNum,\
                            "target":allNodes.index(newNodeName),"value":5,
                            "text":allNodes[docNum].get("text")})
    return (allNodes, links)

def getAltRepresentation(allNodes, links):
    """
    Converts the d3 representation of the graph to a more human-friendly one
    """
    ret = {}
    for node,srcIndex in zip(allNodes,range(0,len(allNodes))):
        name = node.get("name")
        ret[name] = []
        for link in links:
            if link.get("source") == srcIndex:
                targetIndex = link.get("target")
                ret[name].append(allNodes[targetIndex].get("name"))
    return ret

def getGraph(inFile, outFile = 'opinions.json'):
    """
    Given an input file, outputs a d3-friendly output file
    """
    nodes = getNodes(inFile)
    (allNodes, links) = getAllNodesAndLinks(nodes)
    with open(outFile, 'w') as out:
        out.write(json.dumps({"nodes":allNodes,"links":links}))

def getContext(allNodes, links): 
    """
    Gets the sentence before and the sentence after each citation
    """
    trainer = punkt.PunktSentenceTokenizer()
    trainer.train("data/real_estate.txt") #Sentence fragmenter trained on real_estate (arbitrarily)
    for node,srcIndex in zip(allNodes,range(0,len(allNodes))):
        name = node.get("name")
        tokens = trainer.tokenize(node.get("text"))
        for link in links:
            if link.get("source") == srcIndex:
                target = allNodes[link.get("target")].get("name")
                for sentence,sentIndex in zip(tokens,range(0,len(tokens))):
                    if target in sentence:
                        prevSent = ''
                        i = 1
                        while len(prevSent.split(' ')) < 10: #If the previous sentence was too short, add more
                            try:
                                prevSent = tokens[sentIndex-i] + prevSent
                            except:
                                break
                            i += 1
                        print 'PREV SENTENCE: ' + prevSent
                        print 'CURRENT SENTENCE: ' + sentence
                        nextSent = ''
                        while len(nextSent.split(' ')) < 10: #Same with the next sentence
                            try:
                                nextSent += tokens[sentIndex+i]
                            except:
                                break
                            i += 1
                        print 'NEXT SENTENCE: ' + nextSent

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

