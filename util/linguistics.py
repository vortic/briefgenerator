import sys, os, re
import opinionsToGraph as otg
from subprocess import *
import time
import pexpect
import nltk
from nltk.tree import *
from nltk.draw import tree
from nltk.stem.porter import PorterStemmer

draw = False

def getSubject(sentence):
    """
    The subject is the noun phrase that is the child of S (the sentence) and the sibling of VP
    """
    treeString = getParseTree(sentence)
    pTree = ParentedTree.convert(treeString)
    print sentence
    for subtree in pTree.subtrees():
        if len(subtree.treeposition()) == 2 and subtree.node == 'NP' and subtree.parent().node == 'S':
            if subtree.right_sibling() and subtree.right_sibling().node == 'VP':
                print subtree
                print subtree.right_sibling()
                return subtree
    if draw:
        pTree.draw()

def getAction(sentence, noun):
    noun = str(noun)
    treeString = getParseTree(sentence)
    pTree = ParentedTree.convert(treeString)
    np,vp = None,None
    print sentence
    for subtree in pTree.subtrees():
        if subtree.node == 'NP' and noun in str(subtree):
            np = subtree
    for subtree in pTree.subtrees():
        if subtree.left_sibling() and subtree.left_sibling() == np:
            vp = subtree
    for subtree in vp.subtrees():
        if subtree.parent() == vp and re.match('V[A-Z]+', subtree.node):
            print subtree
    if draw:
        pTree.draw()

def startProcessPexpect(cmdString, log=True):
    cmd = pexpect.spawn(cmdString)
    if log:
        cmd.logfile = open("tmp/log.txt", "w")
    return cmd

def start30SecProcess(cmdString):
    cmd = Popen(cmdString, shell=True)
    time.sleep(30)
    cmd.terminate()
    return None

def startSRL():
    labeler = startProcessPexpect("./lib/ASRL/senna/senna -path lib/ASRL/senna/ -srl -verbose")
    labeler.expect('\[ready\]\r\n')
    return labeler

def getParseTree(parser, sentence):
    """
    Start the parser with Popen for this function
    """
    #stdoutdata, stderrdata = parser.communicate(sentence)
    print sentence
    parser.stdin.write(sentence + '\n')
    parser.stdin.flush()
    while True:
        line = parser.stdout.readline()
        if line != '':
            print line.rstrip()
        else:
            break
    #return Tree(parser.stdout.read())

def sennaToRoleLabels(sennaOut, stem=True):
    """
    Don't use this one anymore
    """
    verbExtractor = r"\n\s*.*?\s+([-a-zA-Z]*?)\s+"
    allSrlVerbs = []
    stemmer = PorterStemmer()
    for result in re.finditer(verbExtractor, sennaOut):
        for srlVerb in result.groups():
            if srlVerb != '-':
                if stem:
                    allSrlVerbs.append(stemmer.stem(srlVerb))
                else:
                    allSrlVerbs.append(srlVerb)
    print allSrlVerbs 
    return allSrlVerbs

def getRoleLabelsPexpect(senna, sentence):
    """
    Don't use this one anymore
    """
    #print sentence
    def cleanSentence(sentence):
        toBeRemoved = r'[^a-zA-Z0-9,\.\s]'
        ret = re.sub(toBeRemoved, '', sentence)
        ret = ret.strip()
        ret = ret.replace('\n',' ')
        #print 'clean sentence'
        #print ret
        return ret
    sentence = cleanSentence(sentence)
    if len(sentence) > 10 and '\n' not in sentence:
        senna.sendline(sentence)
        time.sleep(2)
        senna.expect('\r\n\r\n')
        time.sleep(2)
        return sennaToRoleLabels(senna.before)
    else:
        print 'Not doing anything.'
        return []

def getRoleLabels(tokens, stem=True):
    ret = []
    stemmer = PorterStemmer()
    sennaMatrix = getSennaMatrix(tokens)
    for sentence in sennaMatrix:
        for sennaRow in sentence:
            word = sennaRow[0]
            verb = sennaRow[1]
            if verb != '-':
                if stem:
                    ret.append(stemmer.stem(verb))
                else:
                    ret.append(verb)
    return ret

def getSennaMatrix(tokens):
    def writeCase():
        with open('tmp/sennaIn.txt', 'w') as out:
            for token in tokens:
                out.write(token + '\n')
    def cleanSennaOut(sennaRow):
        if '' in sennaRow:
            while '' in sennaRow:
                sennaRow.remove('')
        return sennaRow
    ret = []
    writeCase()
    start30SecProcess("./lib/ASRL/senna/senna -path lib/ASRL/senna/ -srl < tmp/sennaIn.txt > tmp/sennaOut.txt")
    with open('tmp/sennaOut.txt', 'r') as text:
        line = text.readline()
        sentence = []
        while line != '':
            while line != '\n':
                sennaRow = re.split('\s+', line)
                sennaRow = cleanSennaOut(sennaRow)
                if len(sennaRow) > 1:
                    sentence.append(sennaRow)
                line = text.readline()
            if sentence != []:
                ret.append(sentence)
            sentence = []
            line = text.readline()
    return ret

def srlCount(cases):
    from collections import Counter
    srlCount = Counter()
    trainer = nltk.tokenize.punkt.PunktSentenceTokenizer()
    trainer.train("GoogleCases.txt")
    for case in cases:
        if type(case) != type(''):
            print "Something went wrong - the case isn't a string"
            continue
        tokens = trainer.tokenize(case)
        roleLabels = getRoleLabels(tokens, stem=False)
        for role in roleLabels:
            srlCount[role] = srlCount[role] + 1
    return srlCount

def commonRoles(cases, n=50):
    def getThematicRoles(verb, sennaMatrix):
        thematicRoles = {'A0':[], 'A1':[]}
        for sentence in sennaMatrix:
            for sennaRow in sentence:
                if sennaRow[1] == verb and 'S-V' in sennaRow:
                    column = sennaRow.index('S-V')
                    A0 = []
                    A1 = []
                    for sennaRow2 in sentence:
                        role = sennaRow2[column]
                        matchingText = sennaRow2[0]
                        if re.match('[SBIE]-A0', role):#Acceptor
                            A0.append(matchingText)
                        if re.match('[SBIE]-A1', role):#Accepted
                            A1.append(matchingText)
                    thematicRoles['A0'].append(' '.join(A0))
                    thematicRoles['A1'].append(' '.join(A1))
        return thematicRoles
    from collections import Counter
    topSRL = srlCount(cases)
    trainer = nltk.tokenize.punkt.PunktSentenceTokenizer()
    trainer.train("GoogleCases.txt")
    roleDict = {}
    for verb, count in topSRL.most_common(n):
        roleDict[(verb, count)] = []
    for case in cases:
        tokens = trainer.tokenize(case)
        sennaMatrix = getSennaMatrix(tokens)
        for verb, count in topSRL.most_common(n):
            thematicRoles = getThematicRoles(verb, sennaMatrix)
            roleDict[(verb, count)].append(thematicRoles)
    ret = {}
    for (verb, count), usageList in roleDict.iteritems():
        ret[verb] = {}
        ret[verb]['count'] = count
        ret[verb]['A0'] = Counter()
        ret[verb]['A1'] = Counter()
        for usage in usageList:
            for cite in usage['A0']:
                ret[verb]['A0'][cite] = ret[verb]['A0'][cite] + 1
            for cite in usage['A1']:
                ret[verb]['A1'][cite] = ret[verb]['A1'][cite] + 1
    return ret

def writeRoleGraph(cases):
    import json
    roles = commonRoles(cases)
    links = [{"source":1,"target":0,"value":1}]#Have to put an edge in or the graph gets mad
    nodes = []
    for verb, role in roles.iteritems():
        nodes.append({"name":verb, "group":0, "A0":str(role['A0']), "A1":str(role['A1']), "count":role['count']})
    with open('roles.json', 'w') as out:
        out.write(json.dumps({"nodes":nodes,"links":links}))

if __name__ == "__main__":
    import data
    testSet = [u'The parties agreed that the wife would receive the first $214,000 from the sale of the family residence, receipt of which would not constitute a change of circumstances for modification of spousal support.', "It makes no more sense to reduce wife's spousal support because she received her rightful share of the community property than it would to increase wife's spousal support because husband received his rightful share of the community property.", 'In Rabkin, the contested income took the form of $1,800 mortgage payments derived from the sale of the family residence which "constituted the single major asset awarded to wife as her one-half share of the community property."', "The court noted that, in any event, because the parties' agreement expressly provided that the sale of the residence would not constitute a change in circumstances justifying a reduction in support, the trial court's reliance on the sale in ordering a reduction was improper.", "We have concluded that none of these factors furnished a proper basis for the trial court's $250 per month reduction in wife's permanent spousal support.", 'The agreement provided for spousal support amounts established in contemplation of a prompt sale of the family residence.', 'The parties may also agree, as part of a support provision, that specified occurrences will or will not constitute the requisite change of circumstances to allow subsequent modification of that provision.', 'The trial court then reduced her spousal support based in part on the income she was receiving from the note.']
    #testSet = ['I walk the dog.']
    #labeler = startSRL()
    """
    for test in testSet:
        getRoleLabels(labeler, test)
    """
    #"""
    nodes = otg.getNodes('data/spousal_support.txt')
    #for node in nodes:
    cites, titles = data.getGoogleCites(nodes[0].get('name'))
    titles = set(titles)
    cases = []
    for title in titles:
        case = data.getGoogleCase(title)
        cases.append(case)
    #print srlCount(cases)
    #print commonRoles(cases)
    writeRoleGraph(cases)
    #"""
    """parser = startProcessPopen("java -Xmx1024m -jar lib/berkeleyParser.jar -gr lib/eng_sm6.gr")
    for test in testSet:
        print getParseTree(parser, test)
    print getParseTree(parser, testSet[0])"""
    #labeler.close()
