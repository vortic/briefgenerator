import sys, os, re
import opinionsToGraph as otg
import case
import subprocess
import time
from collections import Counter
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

def startProcess(cmdString):
    subprocess.check_call(cmdString, shell=True)
    return None

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

def getRoleLabels(cas, stem=True):
    ret = []
    stemmer = PorterStemmer()
    sennaMatrix = cas.sennaMatrix
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

def getSennaMatrix(cas):
    def writeCase():
        with open('tmp/sennaIn.txt', 'w') as out:
            for token in cas.tokens:
                out.write(token + '\n')
    def cleanSennaOut(sennaRow):
        if '' in sennaRow:
            while '' in sennaRow:
                sennaRow.remove('')
        return sennaRow
    ret = []
    writeCase()
    startProcess("./lib/ASRL/senna/senna -path lib/ASRL/senna/ -srl < tmp/sennaIn.txt > tmp/sennaOut.txt")
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

def srlCount(cases, stem=True):
    srlCount = Counter()
    for cas in cases:
        roleLabels = getRoleLabels(cas, stem=True)
        for role in roleLabels:
            srlCount[role] = srlCount[role] + 1
    return srlCount

def commonRoles(cases, n=50, stem=True):
    stemmer = PorterStemmer()
    def getThematicRoles(verb, cas):
        if stem:
            verb = stemmer.stem(verb)
        sennaMatrix = cas.sennaMatrix
        thematicRoles = {'A0':[], 'A1':[]}
        for sentence in sennaMatrix:
            for sennaRow in sentence:
                if ((stem and stemmer.stem(sennaRow[1]) == verb) or\
                    (not stem and sennaRow[1] == verb)) and 'S-V' in sennaRow:
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
                    thematicRoles['A0'].append(' '.join(A0)*cas.importance)
                    thematicRoles['A1'].append(' '.join(A1)*cas.importance)
        return thematicRoles
    topSRL = srlCount(cases, stem=True)
    roleDict = {}
    for verb, count in topSRL.most_common(n):
        roleDict[(verb, count)] = []
    for cas in cases:
        for verb, count in topSRL.most_common(n):
            thematicRoles = getThematicRoles(verb, cas)
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
    sentences = {}
    for verb, role in roles.iteritems():
        sentences[verb] = sorted(generateSentences(verb, role['A0'], role['A1']),
                                 key = lambda x: x[1] + x[2])
        sentences[verb].reverse()
    links = [{"source":1,"target":0,"value":1}]#Have to put an edge in or the graph gets mad
    nodes = []
    for verb, role in roles.iteritems():
        nodes.append({"name":verb, "group":0, "A0":str(role['A0']), "A1":str(role['A1']), "count":role['count'], "sentences":str(sentences[verb])})
    with open('roles.json', 'w') as out:
        out.write(json.dumps({"nodes":nodes,"links":links}))

def summarizeCase(citingCases):
    roles = commonRoles(citingCases)
    sentences = {}
    summary = []
    for verb, role in roles.iteritems():
        sentences[verb] = sorted(generateSentences(verb, role['A0'], role['A1']),
                                 key = lambda x: x[1] + x[2])
        sentences[verb].reverse()
    for verb, role in roles.iteritems():
        if len(sentences[verb]) > 0:
            summary.append(sentences[verb][0])
    return summary

def generateSentences(verb, acceptors, accepteds, countLowerBound=3, noEmpty=True):
    allSentences = []
    for acceptor, acceptorcount in acceptors.iteritems():
        for accepted, acceptedcount in accepteds.iteritems():
            if noEmpty and (accepted == '' or acceptor == ''):
                continue
            generatedSentence = ' '.join([acceptor, verb, accepted])
            if acceptorcount >= countLowerBound and acceptedcount >= countLowerBound:
                allSentences.append((generatedSentence, acceptorcount, acceptedcount))
    return allSentences

def resolveAnaphora(cas):
    def makeJavarapInput():
        with open('tmp/javarapIn.txt', 'w') as f:
            for token in cas.tokens:
                f.write(token + '\n\n')
    makeJavarapInput()
    os.system('java -Xmx1024m -jar lib/JavaRAP_1.13/AnaphoraResolution.jar tmp/javarapIn.txt > tmp/javarapOut.txt')

def findWhatIsAskedFor(cas):
    def writeSentence(sentence):
        with open('tmp/sennaIn.txt', 'w') as out:
            out.write(sentence + '\n')
    def cleanSennaOut(sennaRow):
        if '' in sennaRow:
            while '' in sennaRow:
                sennaRow.remove('')
        return sennaRow
    supportSentences = []
    for token in cas.tokens:
        if 'support' in token and len(supportSentences) == 0:
            allLines = []
            for result in re.finditer(r'.*\n(.*)', token):
                for oneLine in result.groups():
                    allLines.append(oneLine)
            supportSentences.append(allLines[-1])
    print supportSentences[0]
    writeSentence(supportSentences[0])
    startProcess("./lib/ASRL/senna/senna -path lib/ASRL/senna/ -srl < tmp/sennaIn.txt > tmp/sennaOut.txt")
    ret = []
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

if __name__ == "__main__":
    import data
    """
    for test in testSet:
        getRoleLabels(labeler, test)
    """
    #for node in nodes:
    #cites, titles = data.getGoogleCites('139 Cal.App.4th 1225')
    originalCase = case.Case('139 Cal.App.4th 1225', senna=False)
    """
    titles = data.getMoreGoogleCites(originalCase)
    titles = set(titles)
    """
    cases = []
    cases.append(originalCase)
    """
    for title in titles:
        cas = case.Case(title, senna=False)
        cases.append(cas)
    """
    #print srlCount(cases)
    #print commonRoles(cases)
    #writeRoleGraph(cases)
    print findWhatIsAskedFor(originalCase)
    #print summarizeCase(cases)
    #originalCase = case.Case('139 Cal.App.4th 1225', senna=False)
    #resolveAnaphora(originalCase)
    #generateSentences('walk', Counter({'': 6, 'the court': 5, 'she': 2}), Counter({'the dog': 5, 'the cat': 2}))
    """parser = startProcessPopen("java -Xmx1024m -jar lib/berkeleyParser.jar -gr lib/eng_sm6.gr")
    for test in testSet:
        print getParseTree(parser, test)
    print getParseTree(parser, testSet[0])"""
    #labeler.close()
