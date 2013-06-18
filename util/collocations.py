import re, nltk
from nltk.collocations import *
import opinionsToGraph as OTG

if __name__ == "__main__":
    import argparse, json, os
    parser = argparse.ArgumentParser(description='Get links from a file.')
    parser.add_argument('f', metavar='filename', action='store', help='Directory of files to parse (LexisNexis format)')
    args = parser.parse_args()
    nodes = []
    for aFile,color in zip(os.listdir(args.f),range(0,len(os.listdir(args.f)))):
        nodes += OTG.getNodes(args.f + aFile,color)
    allText = ''
    for node in nodes:
        allText += node.get('text') + ' '
    trainer = nltk.tokenize.punkt.PunktSentenceTokenizer()
    trainer.train("data/real_estate.txt") #Sentence fragmenter trained on real_estate (arbitrarily)
    sentTokens = trainer.tokenize(allText)
    wordTokens = [nltk.wordpunct_tokenize(s) for s in sentTokens]
    flatWords = [item for sublist in wordTokens for item in sublist] #puts all words into one list
    finder = BigramCollocationFinder.from_words(flatWords)
    bigram_measures = nltk.collocations.BigramAssocMeasures()
    scored = finder.score_ngrams(bigram_measures.likelihood_ratio)
    print scored
