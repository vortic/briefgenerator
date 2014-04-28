import data
from case import Case
import random

if __name__ == "__main__":
    cases = data.getAllSavedCases(makeString=False, senna=False)
    while True:
        cas = random.choice(cases)
        moreLinks = data.getAboutCases(cas)
        print moreLinks
        for i, link in enumerate(moreLinks):
            print i
            c = Case(link, senna=False)
