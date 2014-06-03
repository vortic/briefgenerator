import data, linguistics, nltk, learning, wordVector
import numpy as np
import gensim
model = gensim.models.Word2Vec.load('models/word2vec/unigramModel')

class Case:
    def __init__(self, name, makeString=True, wordVec=True, senna=True):
        if name.isdigit():
            self.name = name
            self.googleURL = name
        else:
            self.name = name
            self.googleURL = data.getGoogleURL(self)
        if makeString:
            self.string = data.getGoogleCase(self)
            tokenizer = linguistics.getTokenizer()
            self.tokens = tokenizer.tokenize(self.string)
            self.tokenSummary = {1:[], 2:[], 3:[], 4:[]}
            learning.readLabels([self], 'tokens')
            #if wordVec:
            #    self.representation = wordVector.getRepresentation(self)
            if senna:
                self.sennaMatrix = linguistics.getSennaMatrix(self)
                self.sentences = linguistics.getSennaAlignedSentences(self)
                self.srlSentences = linguistics.getSrlSentences(self)
                self.indicators = linguistics.resolveAnaphora(self)
                self.srlSummary = {1:[], 2:[], 3:[], 4:[]}
                learning.readLabels([self], 'srl')
    
    def visualize(self, size=200):
        """
        from matplotlib import pyplot as plt
        import matplotlib.cm as cm
        altRepresentation = wordVector.getRepresentation(self, intensity=True, binarize=True)
        for i, sentence in enumerate(altRepresentation):
            if self.inSummary(i):
                print self.tokens[i]
                print
                plt.imshow(sentence, cmap = cm.Greys_r)
                plt.show()
        """
        from matplotlib import pyplot as plt
        import matplotlib.cm as cm
        altRepresentation = wordVector.getSrlRepresentation(self, intensity=True, bnrz=True)
        for i, sentence in enumerate(altRepresentation):
            if self.inSummary(i):
                print self.sentences[i]
                print
                plt.imshow(sentence, cmap = cm.Greys_r)
                plt.show()

    def inSummary(self, index, tokens=False):
        if tokens:
            for person, summarySentences in self.tokenSummary.iteritems():
                for summ in summarySentences:
                    if index == summ:
                        return True
            return False
        else:
            for person, summarySentences in self.srlSummary.iteritems():
                for summ in summarySentences:
                    if index == summ:
                        return True
            return False

if __name__ == "__main__":
    cas = Case('6850872635911328292')
    cas.visualize()
