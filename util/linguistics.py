import os, re
import opinionsToGraph
from nltk.tree import *
from nltk.draw import tree

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

def getParseTree(sentence):
    with open('tmp/parseTreeInput.txt', 'w') as out:
        out.write(sentence)
    os.system("java -Xmx1024m -jar lib/berkeleyParser.jar -gr lib/eng_sm6.gr -inputFile tmp/parseTreeInput.txt\
    -outputFile tmp/parseTreeOutput.txt")
    ret = ''
    with open('tmp/parseTreeOutput.txt','r') as f:
        ret = Tree(f.read())
    return ret

if __name__ == "__main__":
    realSentences = False
    if realSentences:
        nodes = []
        for aFile,color in zip(os.listdir('data/'),range(0,len(os.listdir('data/')))):
            nodes += opinionsToGraph.getNodes('data/'+aFile,color)
        for sentence in opinionsToGraph.getSentencesWithWord(nodes, "court"):
            getSubject(sentence)
    testSet = [u'The parties agreed that the wife would receive the first $214,000 from the sale of the family residence, receipt of which would not constitute a change of circumstances for modification of spousal support.', "It makes no more sense to reduce wife's spousal support because she received her rightful share of the community property than it would to increase wife's spousal support because husband received his rightful share of the community property.", 'In Rabkin, the contested income took the form of $1,800 mortgage payments derived from the sale of the family residence which "constituted the single major asset awarded to wife as her one-half share of the community property."', "The court noted that, in any event, because the parties' agreement expressly provided that the sale of the residence would not constitute a change in circumstances justifying a reduction in support, the trial court's reliance on the sale in ordering a reduction was improper.", "We have concluded that none of these factors furnished a proper basis for the trial court's $250 per month reduction in wife's permanent spousal support.", 'The agreement provided for spousal support amounts established in contemplation of a prompt sale of the family residence.', 'The parties may also agree, as part of a support provision, that specified occurrences will or will not constitute the requisite change of circumstances to allow subsequent modification of that provision.', 'The trial court then reduced her spousal support based in part on the income she was receiving from the note.']
    for test in testSet:
        getAction(test, getSubject(test))
    #getSubject('I went to the store.')
    #getSubject('In only three of these may the court grant a divorce after proof of recrimination.')
    #getAction('In only three of these may the court grant a divorce after proof of recrimination.', 'court')
    #getAction('The trial court then reduced her spousal support based in part on the income she was receiving from the note.', 'court')
    #getSubject('In only three of these may the court, in its discretion, grant a divorce after proof of recrimination.')
