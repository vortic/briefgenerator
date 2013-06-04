import numpy as np
from opinionsToGraph import getNodes as get_nodes
import nltk
from matplotlib.pyplot import clf, bar, xticks

def count_docs(filename):
    docs = [doc['text'].lower() for doc in get_nodes(filename)]
    with open('data/english.stop.txt', 'r') as f:
        stop_words = f.readlines()
    stop_words = [s[:-1] for s in stop_words]
    tokenized_docs = [nltk.word_tokenize(doc) for doc in docs]
    stemmed_docs = []
    for doc in tokenized_docs:
        stemmed_docs.append([word for word in doc if word not in stop_words])
    return [sorted_words(count(doc, False)) for doc in stemmed_docs]

def plot_words(word_tuples):
    def plot_dist(types, color='b', labels=None, bottom=0, clear=True):
        """Plots a distribution as a bar graph.
        
        Given a distribution, plots a bar graph. Each bar is an element in the
        distribution, and its value is the element's probability.
        
        Args:
            types:
                a distribution, represented as a list
        Returns:
            none, but plots the distribution
        """
        if clear:
            clf()
        offset = 0
        width = 0.01
        if labels == None:
            labels = range(len(types))
        for dist in types:
            bar(offset, dist, width, bottom, color=color)
            offset += width
        xticks(np.arange(width / 2, width * len(types), .01), labels,
               rotation='vertical')
    plot_dist([w[1] for w in word_tuples], labels=[w[0] for w in word_tuples])

def sorted_words(word_count):
    counts = [(word, word_count[word]) for word in word_count]
    return sorted(counts, cmp=lambda x,y: cmp(x[1], y[1]), reverse=True)

def count(words, stats=True):
    """Creates a histogram of occurrences in an array.
    
    Given a list, counts how many times each instance occurs.
    
    Args:
        words:
            a list of values
    Returns:
        a dictionary with keys as the values that appear in words and values
        as the number of times they occur 
    """
    word_count = {}
    num_words = 0
    unique_words = 0
    for word in words:
        num_words += 1
        if word_count.has_key(word):
            word_count[word] += 1
        else:
            word_count[word] = 1
            unique_words += 1
    if stats:
        word_count["total"] = num_words
        word_count["unique"] = unique_words
    return word_count