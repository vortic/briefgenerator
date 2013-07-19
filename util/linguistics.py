import os
import opinionsToGraph
from nltk.tree import *
from nltk.draw import tree

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
    #getSubject('I went to the store.')
    getSubject('In only three of these may the court grant a divorce after proof of recrimination.')
    #getSubject('In only three of these may the court, in its discretion, grant a divorce after proof of recrimination.')
