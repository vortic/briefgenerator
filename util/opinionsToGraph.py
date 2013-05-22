import re

def getTitles(filename):
    title = False
    nodeCases = []
    with open(filename) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if re.match('[0-9]+ of 100 DOCUMENTS', line): #Matches title of a new brief
            title = True
            continue
        if re.match('PRIOR-HISTORY', line): #Matches end of title
            title = False
        if title:
            reg = '\d+ Cal\..*\d+' #Matches the reference to the case (eg 220 Cal.App.2d 1)
            if re.match(reg, line):
                splitNodeNames = line.split(';')
                nodeCase = splitNodeNames[0]
                nodeCases.append(nodeCase)
    return nodeCases

def getLinks(filename, numDocs):
    body = False
    nodeLinks = [0]*numDocs
    docNum = -1
    previousSentence = ''
    with open(filename) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if re.match('[0-9]+ of 100 DOCUMENTS', line): #Matches title of a new brief
            body = False
            docNum += 1
            nodeLinks[docNum] = []
            continue
        if re.match('OPINION', line): #Matches body
            body = True
        if body:
            reg = '.*([?!\d]*) (\d+ Cal\..* \d+)(;|,| \]).*' #Matches the reference to the case (eg 220 Cal.App.2d 1)
            result = re.match(reg, line)
            if result:
                potentialLink = result.group(2)
                context = previousSentence
                if len(potentialLink.split(' ')) == 3:
                    nodeLinks[docNum].append((potentialLink,context))
        previousSentence = line
    return nodeLinks


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Get links from a file.')
    parser.add_argument('f', metavar='filename', action='store', help='File to parse (LexisNexis format)')
    args = parser.parse_args()
    graph = {}
    titles = getTitles(args.f)
    links = getLinks(args.f, len(titles))
    for node,edges in zip(titles, links):
        graph[node] = edges
    print graph
