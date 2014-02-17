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
from genderator.detector import *

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

def getSrlSentences(cas):
    stemmer = PorterStemmer()
    sennaMatrix = cas.sennaMatrix
    justVerbs = []
    ret = []
    for sentence in sennaMatrix:
        verbSentence = []
        for sennaRow in sentence:
            if sennaRow[1] != '-':
                verbSentence.append(stemmer.stem(sennaRow[1]))
        justVerbs.append(verbSentence)
    for sentence, verbSentence in zip(sennaMatrix, justVerbs):
        numVerbs = len(verbSentence)
        srlSentence = []
        for i in range(0, numVerbs):
            clause = {}
            for sennaRow in sentence:
                if re.match('[SBIE]-(.*)', sennaRow[i+2]):
                    role = re.match('[SBIE]-(.*)', sennaRow[i+2]).group(1)
                    if not role in clause:
                        clause[role] = ''
                    clause[role] = ' '.join([clause[role], sennaRow[0]]).strip()
            srlSentence.append(clause)
        ret.append(srlSentence)
    return ret

def getSennaAlignedSentences(cas):
    sennaMatrix = cas.sennaMatrix
    sentences = []
    for sentence in sennaMatrix:
        stringBuilder = []
        for sennaRow in sentence:
            stringBuilder.append(sennaRow[0])
        sentences.append(' '.join(stringBuilder).strip())
    return sentences

def generateClauseSensitiveSentences(cas):
    clauseCount = Counter()
    srlSentences = cas.srlSentences
    realSentences = cas.sentences
    for sentence in srlSentences:
        #print sentence
        for clause in sentence:
            #clauseCount[clause['V']] = clauseCount[clause['V']] + 1
            if 'A0' in clause:
                clauseCount[(clause['V'], clause['A0'].lower())] = clauseCount[(clause['V'], clause['A0'].lower())] + 1
                break
    for commonClause, count in clauseCount.most_common(20):
        print commonClause
        print count
        for sentence in srlSentences:
            for clause in sentence:
                if 'A0' in clause and commonClause == (clause['V'], clause['A0'].lower()):
                    sentenceIndex = srlSentences.index(sentence)
                    print realSentences[sentenceIndex]
    return clauseCount

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
    try:
        with open('cases/' + cas.googleURL + '/sennaOut.txt', 'r') as f:
            with open('tmp/sennaOut.txt', 'w') as text:
                sennaOut = f.read()
                text.write(sennaOut)
    except IOError:
        writeCase()
        startProcess("./lib/ASRL/senna/senna -path lib/ASRL/senna/ -srl < tmp/sennaIn.txt > tmp/sennaOut.txt")
        with open('cases/' + cas.googleURL + '/sennaOut.txt', 'w') as f:
            with open('tmp/sennaOut.txt', 'r') as text:
                sennaOut = text.read()
                f.write(sennaOut)
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
        thematicRoles = {'A0':[], 'A1':[], 'A2':[], 'A3':[]}
        for sentence in sennaMatrix:
            for sennaRow in sentence:
                if ((stem and stemmer.stem(sennaRow[1]) == verb) or\
                    (not stem and sennaRow[1] == verb)) and 'S-V' in sennaRow:
                    column = sennaRow.index('S-V')
                    A0 = []
                    A1 = []
                    A2 = []
                    A3 = []
                    for sennaRow2 in sentence:
                        role = sennaRow2[column]
                        matchingText = sennaRow2[0]
                        if re.match('[SBIE]-A0', role):#Acceptor
                            A0.append(matchingText)
                        if re.match('[SBIE]-A1', role):#Accepted
                            A1.append(matchingText)
                        if re.match('[SBIE]-A2', role):
                            A2.append(matchingText)
                        if re.match('[SBIE]-A3', role):
                            A3.append(matchingText)
                    thematicRoles['A0'].append(' '.join(A0)*cas.importance)
                    thematicRoles['A1'].append(' '.join(A1)*cas.importance)
                    thematicRoles['A2'].append(' '.join(A2)*cas.importance)
                    thematicRoles['A3'].append(' '.join(A3)*cas.importance)
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
        ret[verb]['A2'] = Counter()
        ret[verb]['A3'] = Counter()
        for usage in usageList:
            for cite in usage['A0']:
                ret[verb]['A0'][cite] = ret[verb]['A0'][cite] + 1
            for cite in usage['A1']:
                ret[verb]['A1'][cite] = ret[verb]['A1'][cite] + 1
            for cite in usage['A2']:
                ret[verb]['A2'][cite] = ret[verb]['A2'][cite] + 1
            for cite in usage['A3']:
                ret[verb]['A3'][cite] = ret[verb]['A3'][cite] + 1
    return ret

def writeRoleGraph(cases):
    import json
    roles = commonRoles(cases)
    sentences = {}
    for verb, role in roles.iteritems():
        sentences[verb] = sorted(generateSentences(verb, roles),
                                 key = lambda x: x[1] + x[2])
        sentences[verb].reverse()
    links = [{"source":1,"target":0,"value":1}]#Have to put an edge in or the graph gets mad
    nodes = []
    for verb, role in roles.iteritems():
        nodes.append({"name":verb, "group":0, "A0":str(role['A0']), "A1":str(role['A1']), "A2":str(role['A2']), "A3":str(role['A3']), "count":role['count'], "sentences":str(sentences[verb])})
    with open('roles.json', 'w') as out:
        out.write(json.dumps({"nodes":nodes,"links":links}))

def summarizeCase(citingCases):
    roles = commonRoles(citingCases)
    sentences = {}
    summary = []
    for verb, role in roles.iteritems():
        sentences[verb] = sorted(generateSentences(verb, roles),
                                 key = lambda x: x[1] + x[2])
        sentences[verb].reverse()
    for verb, role in roles.iteritems():
        if len(sentences[verb]) > 0:
            summary.append(sentences[verb][0])
    return summary

def generateSentences(verb, roles, countLowerBound=3, noEmpty=True):
    allSentences = []
    acceptors = roles[verb]['A0']
    accepteds = roles[verb]['A1']
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
            if allLines !=[]:
                supportSentences.append(allLines[-1])
    print supportSentences
    """
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
    """
def findTerminationReasons(cas):
    supportSentences = []
    for token in cas.tokens:
        if re.match(r'.*conclud.*', token) != None and len(supportSentences) == 0:
            allLines = []
            for result in re.finditer(r'.*\n(.*)', token):
                for oneLine in result.groups():
                    allLines.append(oneLine)
            if allLines !=[]:
                supportSentences.append(allLines[-1])
    print supportSentences

def getAppellantAndRespondent(cas):
    appellant = ''
    respondent = ''
    for sentence in cas.sentences:
        if appellant != '' and respondent != '':
            break
        if re.match(r'(.*?)\s,\s.*Respondent', sentence):
            respondent = re.findall(r'(.*?)\s,\s.*Respondent', sentence)[0]
        if re.match(r'(.*?)\s,\s.*Appellant', sentence):
            appellant = re.findall(r'(.*?)\s,\s.*Appellant', sentence)[0]
    return (appellant.lower(), respondent.lower())

def whoIsInProPer(cas):
    ret = []
    appellant, respondent = getAppellantAndRespondent(cas)
    regex = r'.*?([^[0-9]*)\s,\sin\spro' #Mismatched [?
    for sentence in cas.sentences:
        if re.match(regex, sentence):
            if appellant == re.findall(regex, sentence)[0].lower().strip():
                ret.append('appellant')
            if respondent == re.findall(regex, sentence)[0].lower().strip():
                ret.append('respondent')
    return ret

def whoWon(cas):
    ret = ''
    for sentence in cas.sentences:
        if 'disposition' in sentence.lower():
            sentIndex = cas.sentences.index(sentence)
            if 'affirmed' in cas.sentences[sentIndex + 1]:
                ret = 'respondent'
            if 'reversed' in cas.sentences[sentIndex + 1]:
                ret = 'appellant'
    if ret != '':
        return ret
    for sentence in cas.srlSentences: #If disposition not clearly marked, decide based on whether affirmed or reversed was used last
        for clause in sentence:
            if 'V' in clause and re.match(r'affirmed', clause['V']):
                #if 'A1' in clause and re.match(r'.*[Oo]rder.*', clause['A1']):
                ret = 'respondent'
            if 'V' in clause and re.match(r'reversed', clause['V']):
                #if 'A1' in clause and re.match(r'.*[Oo]rder.*', clause['A1']):
                ret = 'appellant'
    return ret

def appellantsClaims(cas):
    appellant, respondent = getAppellantAndRespondent(cas)
    print appellant
    realSentences = cas.sentences
    ret = []
    for sentence in cas.srlSentences:
        for clause in sentence:
            if 'V' in clause and re.match(r'claim', clause['V']):
                if 'A0' in clause and (re.match(appellant.split(' ')[0].lower(), clause['A0'].lower())
                    or re.match(appellant.split(' ')[-1].lower(), clause['A0'].lower())
                    or re.match('appellant', clause['A0'].lower())):
                    ret.append(realSentences[cas.srlSentences.index(sentence)])    
    return ret

def courtsConclusions(cas):
    realSentences = cas.sentences
    ret = []
    for sentence in cas.srlSentences:
        for clause in sentence:
            if 'A0' in clause and re.match('we', clause['A0'].lower()):
                ret.append(realSentences[cas.srlSentences.index(sentence)])
                continue
            #if 'V' in clause and re.match(r'conclu', clause['V']):
                """if 'A0' in clause and (re.match('we', clause['A0'].lower())
                    or re.match('court', clause['A0'].lower())):"""
    return ret

def mostCommonA0Verbs(cases, A0s):
    ret = Counter()
    #If A0s == [] then just return most common verbs
    if A0s == []:
        for cas in cases:
            for sentence in cas.srlSentences:
                for clause in sentence:
                    if 'V' in clause:
                        ret[clause['V']] += 1
    for A0 in A0s:
        for cas in cases:
            for sentence in cas.srlSentences:
                for clause in sentence:
                    if 'A0' in clause and re.match(A0, clause['A0'].lower()):
                        if 'V' in clause:
                            ret[clause['V']] += 1
    return ret 

def threeBestA0Sentences(cas, cases, A0s):
    commonVerbs = mostCommonA0Verbs(cases, A0s)
    ret = []
    for verb, count in commonVerbs.most_common():
        for A0 in A0s:
            for sentence in cas.srlSentences:
                for clause in sentence:
                    if 'V' in clause and clause['V'] == verb:
                        if 'A0' in clause and re.match(A0, clause['A0'].lower()):
                            ret.append(cas.sentences[cas.srlSentences.index(sentence)])
                            if len(ret) == 3:
                                return ret
                            continue
    return ret

def verbCount(cas, verb):
    ret = 0
    for sentence in cas.srlSentences:
        for clause in sentence:
            if 'V' in clause and clause['V'] == verb:
                ret += 1
    return ret

def getGenderPronoun(cas, person):
    ret = []
    appellant, respondent = getAppellantAndRespondent(cas)
    appellantFirstName = appellant.split(' ')[0].title()
    respondentFirstName = respondent.split(' ')[0].title()
    d = Detector()
    gender = -1
    if person == 'appellant':
        gender = d.getGender(appellantFirstName)
    else:
        gender = d.getGender(respondentFirstName)
    if gender == 0:
        return 'he'
    if gender == 1:
        return 'she'
    else: #Failure: assume the opposite of the other party
        if person == 'appellant':
            gender = d.getGender(respondentFirstName)
        else:
            gender = d.getGender(appellantFirstName)
        if gender == 0:
            return 'she'
        if gender == 1:
            return 'he'
    return 'both unknown'
    
if __name__ == "__main__":
    import data
    """
    for test in testSet:
        getRoleLabels(labeler, test)
    """
    cases = data.getAllSavedCases()
    for cas in cases:
        appellant, respondent = getAppellantAndRespondent(cas)
        print cas.name
        print "court's arguments:"
        print threeBestA0Sentences(cas, cases, ['we'])
        print "trial court's arguments:"
        print threeBestA0Sentences(cas, cases, ['trial court', 'the court'])
        print "respondent's arguments:"
        print threeBestA0Sentences(cas, cases, ['respondent', getGenderPronoun(cas, 'respondent'), respondent.split(' ')[0], respondent.split(' ')[-1]])
        print "appellant's arguments:"
        print threeBestA0Sentences(cas, cases, ['appellant', getGenderPronoun(cas, 'appellant'), appellant.split(' ')[0], appellant.split(' ')[-1]])
    """
    for cas in cases:
        print cas.name
        print "appellant's claims:"
        print appellantsClaims(cas)
        print "court's conclusions:"
        print courtsConclusions(cas)
    """
    """
    #for node in nodes:
    #cites, titles = data.getGoogleCites('139 Cal.App.4th 1225')
    #originalCase = case.Case('139 Cal.App.4th 1225', senna=True)
    originalCase = case.Case('575864357603110085')
    #originalCase = case.Case('77 Cal. Rptr. 2d 463', senna=True)
    #getAppellantAndRespondent(originalCase)
    #generateClauseSensitiveSentences(originalCase)
    titles = data.getNGoogleCites(originalCase, 20)
    cases = []
    cases.append(originalCase)
    for title in titles:
        print title
        cas = case.Case(title, senna=True)
        moreTitles = data.getNGoogleCites(cas, 10)
        for title2 in moreTitles:
            cas2 = case.Case(title2)
            cases.append(cas2)
        cases.append(cas)
    print 'numCases:' + str(len(cases))
    winners = Counter()
    for cas in cases:
        print 'winner:' + str(whoWon(cas))
        winners[whoWon(cas)] += 1
        print 'in pro per:' + str(whoIsInProPer(cas))
    print winners
    #writeRoleGraph(cases)
    """
