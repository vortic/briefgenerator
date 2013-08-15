import nltk, re, urllib2

def getHeader():
    header = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'ja,en-US;q=0.8,en;q=0.6',
        'Cookie':'GSP=ID=b81c0859da0e87da:S=rMVOHFmgzzJVMEie; NID=67=LEUjnmK2F10Qdn7SYfudyUIjKi7CwvVEVV2OJ_RSuFabWmyUfno8tHI9ivafzlqAhFWUwG4pw47-SC4sqRHo3J_7pIbrsf1tbd-RvyD9-v7rvMq3ICEOGhKOQi6YfxgRY_dCgof5-DuwhLEsY8cnlx1ZQXnWa9CWyGS11FYgZz4Le_Qexzk; PREF=ID=b81c0859da0e87da:U=473d9fcfe638461b:LD=en:CR=2:TM=1369196388:LM=1376429391:GM=1:S=3vwteVXigR7gruqp',
        'Host':'scholar.google.com',
        'Referer':'http://scholar.google.com/scholar?q=224+Cal.+App.+3d+885&btnG=&hl=en&as_sdt=4%2C5',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36',
        'X-Chrome-Variations':'CNO1yQEIl7bJAQiptskBCMS2yQEIqYXKAQi3hcoB'
    }
    return header

def getGoogleURL(caseName):
    url = 'http://scholar.google.com/scholar?hl=en&q=' + caseName.replace(' ', '+') + '&btnG=&as_sdt=4%2C5'
    header = getHeader()
    req = urllib2.Request(url, None, header)
    html = urllib2.urlopen(req).read()
    urlRegex = r'scholar_case\?case=([0-9]+)'
    allLinks = []
    for result in re.finditer(urlRegex, html):
        for link in result.groups():
            allLinks.append(link)
    """
    citeRegex = r'Cited\sby\s(\d+)'
    allNumCites = []
    for result in re.finditer(citeRegex, html):
        for numCites in result.groups():
            allNumCites.append(numCites)
    """
    return allLinks[0] #Assuming the first link is the relevant one, also assuming it was cited

def getGoogleCites(caseName):
    import HTMLParser
    def fixCite(citation):
        """
        Only get one, full sentence out of the cite
        """
        citation = unicode(citation, "utf-8")
        citation = HTMLParser.HTMLParser().unescape(citation)
        sentenceRegex = r'([A-Z].*?\.)'
        finalCitation = ''
        for result in re.finditer(sentenceRegex, citation):
            for sentence in result.groups():
                if len(sentence) > len(finalCitation): #There should only be one "real" sentence
                    finalCitation = sentence
        if finalCitation == '' and citation[-1] != '.':
            return citation + '.'
        elif finalCitation == '':
            return citation
        else:
            return finalCitation
    def fixTitle(title):
        ret = title
        if 'and' in title:
            split = re.split('and', title)
            ret = split[0]
        return ret
    urlNum = getGoogleURL(caseName)
    url = 'http://scholar.google.com/scholar_case?about=' + urlNum
    header = getHeader()
    req = urllib2.Request(url, None, header)
    html = urllib2.urlopen(req).read()
    raw = nltk.clean_html(html)
    #print raw
    citeBegin = '.*?has\sbeen\scited\s+'
    #citations = '(.*?)\s-\sin.*?similar\scitations?\s+'*min(6, numCites) #No more than 9 citations are displayed
    citations = '(.*?)\s-\sin\s(.*?)\s\s'*8 #No more than 9 citations are displayed (sometimes 8)
    citeRegex = r'' + citeBegin + citations
    cites = []
    titles = []
    title = False
    for result in re.finditer(citeRegex, raw):
        for cite in result.groups():
            if title:
                titles.append(fixTitle(cite))
                title = False
            else:
                cites.append(fixCite(cite))
                title = True
    return cites, titles

def getGoogleCase(caseName):
    urlNum = getGoogleURL(caseName)
    url = 'http://scholar.google.com/scholar_case?case=' + urlNum
    header = getHeader()
    req = urllib2.Request(url, None, header)
    html = urllib2.urlopen(req).read()
    raw = nltk.clean_html(html)
    print raw

if __name__ == "__main__":
    cites, titles = getGoogleCites('224 Cal. App. 3d 885')
    for cite, title in zip(cites, titles):
        print
        if re.match('.*\d.*', title):
            getGoogleCase(title)
        else:
            print 'failed on ' + title
    #print getGoogleCites('179 Cal. App. 3d 1071')
    #getGoogleCase('224 Cal. App. 3d 885')
