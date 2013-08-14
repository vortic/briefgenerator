import sys, os, re
import opinionsToGraph as otg
from subprocess import *
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
    cmd = Popen(cmdString, shell=True)
    #cmd = pexpect.spawn(cmdString)
    #cmd.logfile = sys.stdout
    return cmd

def getParseTree(parser, sentence):
    #stdoutdata, stderrdata = parser.communicate(sentence)
    import sys
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

def getRoleLabels(sentence):
    with open("tmp/labeler_input.txt", "w") as text_file:
        text_file.write(sentence)
    cmd = "./lib/ASRL/senna/senna -path lib/ASRL/senna/ -srl < tmp/labeler_input.txt > tmp/labeler_output.txt"
    os.system(cmd)
    sennaOut = None
    with open("tmp/labeler_output.txt", "r") as text_file:
        sennaOut = text_file.read()
    sennaOut = '\n' + sennaOut #Appending a newline to the beginning to make the next regex easier
    #print sennaOut
    verbExtractor = r"\n\s*.*?\s+([-a-zA-Z]*?)\s+"
    allSrlVerbs = []
    stemmer = PorterStemmer()
    for result in re.finditer(verbExtractor, sennaOut):
        for srlVerb in result.groups():
            if srlVerb != '-':
                #print stemmer.stem(srlVerb)
                allSrlVerbs.append(srlVerb)
    return allSrlVerbs

if __name__ == "__main__":
    from collections import Counter
    import data
    testSet = [u'The parties agreed that the wife would receive the first $214,000 from the sale of the family residence, receipt of which would not constitute a change of circumstances for modification of spousal support.', "It makes no more sense to reduce wife's spousal support because she received her rightful share of the community property than it would to increase wife's spousal support because husband received his rightful share of the community property.", 'In Rabkin, the contested income took the form of $1,800 mortgage payments derived from the sale of the family residence which "constituted the single major asset awarded to wife as her one-half share of the community property."', "The court noted that, in any event, because the parties' agreement expressly provided that the sale of the residence would not constitute a change in circumstances justifying a reduction in support, the trial court's reliance on the sale in ordering a reduction was improper.", "We have concluded that none of these factors furnished a proper basis for the trial court's $250 per month reduction in wife's permanent spousal support.", 'The agreement provided for spousal support amounts established in contemplation of a prompt sale of the family residence.', 'The parties may also agree, as part of a support provision, that specified occurrences will or will not constitute the requisite change of circumstances to allow subsequent modification of that provision.', 'The trial court then reduced her spousal support based in part on the income she was receiving from the note.']
    #testSet = ['I walk the dog.']
    #labeler = startProcess("./lib/ASRL/senna/senna -path lib/ASRL/senna/ -srl -verbose")
    #labeler = startProcess("./lib/ASRL/senna/senna -path lib/ASRL/senna/ -srl")
    #for test in testSet:
    #    getRoleLabels(test)
    nodes = otg.getNodes('data/spousal_support.txt')
    srlCount = Counter()
    for node in nodes:
        print data.getGoogleCites(node.get('name'))
    """parser = startProcess("java -Xmx1024m -jar lib/berkeleyParser.jar -gr lib/eng_sm6.gr")
    for test in testSet:
        print getParseTree(parser, test)
    print getParseTree(parser, testSet[0])"""
