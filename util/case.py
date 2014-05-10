import data, linguistics, nltk, learning, wordVector
import numpy as np

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
            trainer = nltk.tokenize.punkt.PunktSentenceTokenizer()
            trainer.train("GoogleCases.txt")
            self.tokens = trainer.tokenize(self.string)
            self.summary = {1:[], 2:[], 3:[], 4:[]}
            learning.readLabels([self])
            #if wordVec:
            #    self.representation = wordVector.getRepresentation(self)
            if senna:
                self.sennaMatrix = linguistics.getSennaMatrix(self)
                self.sentences = linguistics.getSennaAlignedSentences(self)
                self.srlSentences = linguistics.getSrlSentences(self)
                self.indicators = linguistics.resolveAnaphora(self)
    
    def visualize(self, size=200):
        from matplotlib import pyplot as plt
        import matplotlib.cm as cm
        altRepresentation = wordVector.getRepresentation(self, intensity=True, binarize=True)
        for i, sentence in enumerate(altRepresentation):
            if self.inSummary(i):
                print self.tokens[i]
                print
                if size < 200:
                    from sklearn.decomposition import PCA
                    pca = PCA(n_components=size)
                    smallerVersion = pca.fit_transform(sentence) #Needs to be renormalized 0-255
                    plt.imshow(smallerVersion, cmap = cm.Greys_r)
                    plt.show()
                else:
                    plt.imshow(sentence, cmap = cm.Greys_r)
                    plt.show()
    
    def inSummary(self, index):
        for person, summarySentences in self.summary.iteritems():
            for summ in summarySentences:
                if index == summ:
                    return True
        return False

if __name__ == "__main__":
    cas = Case('6850872635911328292')
    cas.visualize()
