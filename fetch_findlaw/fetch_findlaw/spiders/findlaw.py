from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http import Request, FormRequest
from scrapy.selector import HtmlXPathSelector
import time
import os

class FindlawSpider(CrawlSpider):
    case_listings = 0
    cases = 0
    STUB = 'http://login.findlaw.com/scripts/callaw?dest='
    current_dir = None
    
    name="findlaw"
    start_urls = ["http://www.findlaw.com/cacases/"]
    login_page = 'http://login.findlaw.com/scripts/login'
    rules = [#Rule(SgmlLinkExtractor(allow='http://caselaw.lp.findlaw.com/ca/slip/[0-9_]+.html$',),
             #     'parse_case_listing', follow=True),
             Rule(SgmlLinkExtractor(allow='login.findlaw.com/scripts/callaw\?dest=ca/[0-9a-z]+/slip/[0-9]+/[a-z0-9]+.html$'),
                  'parse_case', follow=True),
             Rule(SgmlLinkExtractor(allow='http://caselaw.lp.findlaw.com/ca/slip/2013_[0-9]+.html'),
                  'parse_case_listing', follow=True),
#             Rule(SgmlLinkExtractor(allow='http://login.findlaw.com/scripts/callaw\?dest=ca/cal4th/slip/2013/s190581.html'),
#                  'parse_case', follow=True)
             ]


    def start_requests(self):
        return [Request(self.login_page, callback=self.login)]
    
    def login(self, response):
        print "===TRYING TO LOGIN===="
        return FormRequest.from_response(response,
                                         formdata={'user': 'srudamaster@yahoo.com', 
                                                   'password': 'p0pp0p'},
                                         callback=self.check_login_response)

    def check_login_response(self, response):
        if 'Welcome Victor Huang!' in response.body:
            print "=====LOGIN SUCCESSFUL======"
            return self.make_requests_from_url(self.start_urls[0])
        else:
            print "====LOGIN FAILED===="

    def parse_case_listing(self, response):
        print "==========FOUND A CASE LISTING==========", FindlawSpider.case_listings
        FindlawSpider.case_listings += 1
        print "url:", response.url
#        name = response.url.split('/')[-1][:-len('.html')].split('_')[0]
#        try:
#            os.mkdir(name)
#        except:
#            pass
#        FindlawSpider.current_dir = name
    
    def parse_case(self, response):
        print "=========FOUND A CASE===========", FindlawSpider.cases
        FindlawSpider.cases += 1
        name = response.url[len(FindlawSpider.STUB):-len('.html')].split('%2F')
        #should be the form [courttype, slip, date, uniquename]
        name = ''.join([field + '.' for field in name])[:-1]
        dest = FindlawSpider.current_dir + '/' + name
        print "writing to file:", dest
        with open(dest, 'w') as f:
            f.write(response.body)
        print "========FINISHED CASE=========="
        time.sleep(1)
