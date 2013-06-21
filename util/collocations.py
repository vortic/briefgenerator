import re, nltk
from nltk.tokenize import punkt
from nltk.collocations import BigramCollocationFinder
import opinionsToGraph as otg

def getBlacklist(filename):
    ret = []
    with open(filename) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        ret.append(line)
    return ret

if __name__ == "__main__":
    import argparse, json, os
    parser = argparse.ArgumentParser(description='Get links from a file.')
    parser.add_argument('f', metavar='filename', action='store', help='Directory of files to parse (LexisNexis format)')
    args = parser.parse_args()
    nodes = []
    for aFile,color in zip(os.listdir(args.f),range(0,len(os.listdir(args.f)))):
        nodes += otg.getNodes(args.f + aFile,color)
    all_text = []
    for node in nodes:
        all_text.append(node.get('text') + ' ')
    all_text = ''.join(all_text)
    trainer = punkt.PunktSentenceTokenizer()
    trainer.train("data/real_estate.txt") #Sentence fragmenter trained on real_estate (arbitrarily)
    sentTokens = trainer.tokenize(all_text)
    wordTokens = [nltk.wordpunct_tokenize(s) for s in sentTokens]
    flatWords = [item.lower() for sublist in wordTokens for item in sublist if item.isalpha()] #puts all words into one list
    finder = BigramCollocationFinder.from_words(flatWords)
    finder.apply_word_filter(lambda w: w in getBlacklist('data/english.stop.txt'))
    bigram_measures = nltk.collocations.BigramAssocMeasures()
    scored = finder.score_ngrams(bigram_measures.likelihood_ratio)
    print scored
