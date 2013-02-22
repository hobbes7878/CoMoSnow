###################################################################################
# A twitter API scraper that formats query results for d3 visualization...
###################################################################################


from __future__ import division #forces float numbers for division. must be at beginning...
import json
import simplejson
import urllib2
#import psycopg2
import csv
from string import punctuation
from itertools import groupby
from operator import itemgetter
import datetime
import time
import re
import math
from collections import Counter
from collections import defaultdict
from random import choice



#### INPUT QUESTIONS ###
#The formulas the answers to these questions direct are borrowed from my interpretation of (Austrian Sociologists paper)



Query_List=[]
query_input=""
geocode_lat=""
geocode_lon=""
geocode_rad=""


print ""
print "TWITTER API QUERY with json output for D viz"
print ""
print 'Enter query terms one at a time. Enter "QUERY" to begin tweet fetching.'
print "   Examples: '#newsnight', 'from:bbcnewsnight', 'to:bbcnewsnight'"
while query_input.lower() != "query":
    query_input=raw_input("Query term: ")
    if query_input.lower() != "query":
        Query_List.append(query_input)
print ""

geo_input = raw_input('Would you like to search from a geo point? Y or N: ')

if geo_input.lower()=="y":
    print "Give lat and lon in decimal format."
    print "     (use http://itouchmap.com/latlong.html)"
    lat_input=str(raw_input('    Latitude (num):'))
    lon_input=str(raw_input('   Longitude (num):'))
    rad_input=str(raw_input('Give a radius from point in miles (num):'))
print ""
print "EDGE PAIRING PARAMETERS"
print""
adj_input=raw_input('Would you like to weight pairs according to adjacent words? Y or N: ')
if adj_input.lower()=='y':
    direct_input=raw_input('Would you like directed pairs? Y or N: ')
node_input=int(raw_input('How many nodes would you like (num): '))





#qsample_input=int(raw_input('Max random tweets to sample for analysis (num): '))

opener=urllib2.build_opener() #html handler



### QUERYING THE TWITTER API ###
print "Query Twitter"

#Query_List=['flegs','ira','uda']#,'belfast','takebackthecity','operation standstill','operationsitin','kegsnotflegs','Nolan Show']
# Change QUERY to your search term of choice. 
# Examples: 'newsnight', 'from:bbcnewsnight', 'to:bbcnewsnight'

Query_Groups=dict(zip(Query_List,range(1,len(Query_List)+1))) #creates numbered list of query groups for use in D3



parse_list=[]
no_parse_list=[]

for q in Query_List:
    print "   query: ",q
    QUERY = q
    RESULTS_PER_PAGE = '100'
    LANGUAGE = 'all'
    NUM_PAGES = 100
    geocode_lat=lat_input
    geocode_lon=lon_input
    geocode_rad=rad_input
        #For geo coded results must insert the following code in base_url after "q=%s":
            # &geocode=%s,%s,%smi   #can change mi/miles to km/kilometers.
        #Also add following after urllib2.quote(Query),:
            # geocode_lat,geocode_lon,geocode_rad,

    for p in range(1, NUM_PAGES+1):
        
        if geo_input.lower()=="y":
            base_url = 'http://search.twitter.com/search.json?q=%s&geocode=%s,%s,%smi&rpp=%s&lang=%s&page=%s' \
             % (urllib2.quote(QUERY),geocode_lat,geocode_lon,geocode_rad, RESULTS_PER_PAGE, LANGUAGE, p)
        else:
            base_url = 'http://search.twitter.com/search.json?q=%s&rpp=%s&lang=%s&page=%s' \
             % (urllib2.quote(QUERY),RESULTS_PER_PAGE, LANGUAGE, p)
        
        try:
            page=opener.open(base_url)
        except urllib2.HTTPError,e:
            if e.code==420:  #Twitter API limit hit. Rests for 15 minutes to reset.
                print "Feed limit!"
                print "Zzz.."
                time.sleep(15*60)
                print "Awake!"
                continue
            elif e.code==403: #I forget what code this was, but I wanted it captured for some reason...
                pass
            elif e.code>0:
                pass
                #print e
            else:
                pass

        try:
            results_json = simplejson.load(page)
            for result in results_json['results']:


                ### CREATE TWEET DICTS ###
                ### 1 Dict for parsing ###
                parse_dict={"query":Query_Groups[q],"tweet":result['text'].encode('utf-8'),"tweeter":result['from_user']}
                parse_list.append(parse_dict)
                ### 1 Dict for appending full tweets ###
                no_parse_dict={"query":Query_Groups[q],"tweet":result['text'].encode('utf-8'),"tweeter":result['from_user']}
                no_parse_list.append(no_parse_dict)
               



        except ValueError,e:
            pass #pass for pages in p range beyond twitter API result pages
            #print "Err: ",e




###### CONTENT ANALYSIS ######

###Setting Up###

print "Analyze Content"

#Words not to count in analysis
spares=['a','the','an', 'rt','','and','or','i\'m', 'you\'re','so','its','it\'s','amp','just']
preps = ['aboard','about','above','across','after','against','along','amid','among','anti','around','as','at','before','behind','below','beneath','beside','besides','between','beyond','but','by','concerning','considering','despite','down','during','except','excepting','excluding','following','for','from','in','inside','into','like','minus','near','of','off','on','onto','opposite','outside','over','past','per','plus','regarding','round','save','since','than','through','to','toward','towards','under','underneath','unlike','until','up','upon','versus','via','with','within','without']
verbs = ['am','is','are','was','were','be','being','been','have','has','had','shall','will','do','does','did','may','must','might','can','could','would','should']
pronouns =['all', 'another', 'any', 'anybody', 'anyone', 'anything','both','each', 'other', 'either', 'everybody', 'everyone', 'everything','few','he', 'her', 'hers', 'herself', 'him', 'himself', 'his','i', 'it', 'its', 'itself','many', 'me', 'mine', 'more', 'most', 'much', 'my', 'myself','neither', 'no', 'one', 'nobody', 'none', 'nothing','one', 'one','another', 'other', 'others', 'our','ours', 'ourselves','several', 'she', 'some', 'somebody', 'someone', 'something','that', 'their', 'theirs', 'them', 'themselves', 'these', 'they', 'this', 'those','us','we', 'what', 'whatever', 'which', 'whichever', 'who', 'whoever', 'whom', 'whomever', 'whose','you', 'your', 'yours', 'yourself', 'yourselves']
nix_words = spares+preps+verbs+pronouns

#Punctuation to strip
punc=list(punctuation)
punc.remove('@')#I want these punctuation marks left in.
punc.remove('#')


#Known entities not to be split
known_ents=['stephen nolan','jeremy kyle','sinn fein','jeffrey donaldson','pitt park','short strand','jim wilson','mike nesbitt']


### Creating a Word Network ###

print "   PARSING Tweets"
### PARSING TWEETS ###
for tl in parse_list:
    each_tweet=tl["tweet"]#list of tweet words

    
    for p in punc: #strip out punctuation
        each_tweet=each_tweet.replace(p,"")


    #Exclude known ents from split by linking words with underscore
    for ent in known_ents:
        each_tweet=re.sub(ent,re.sub(" ","_",ent),each_tweet.lower())

    for ql in Query_List:#strip out query term
        each_tweet=re.sub(ql,"",each_tweet.lower())

    tweet_text_split = each_tweet.split() #create list of individual words in tweets
    Word_list=[]
    for tts in tweet_text_split:
        ts=tts.replace("_",' ')#.strip(punctuation).replace("'","").replace("\"","") #should be redundant...
        Word_list.append(ts)
    
    Word_list = [wl for wl in Word_list if wl not in nix_words]

    tl["tweet"]=Word_list

#Returns: [{'query':'fleg','tweet':['apple','banana','cherry']}, 'tweeter':'@joeblow' ... ]



print "   Creating Network Pairs"
### CREATING 2x NETWORK ###

'''
see Wagner/Strohmeier Tweetonomies formulas
cf. Scott Goulder VB Macro
'''

word_pairs_list=[]

for tl in parse_list:
    each_tweet=tl["tweet"]
    query_num=tl["query"]

    
    vector_range_adj=range(len(each_tweet)-1)
    vector_range_co=range(len(each_tweet))

    #Adjacent pairs weighted
    if adj_input.lower()=='y':
        for vr in vector_range_adj:
            v1=each_tweet[vr]
            v2=each_tweet[vr+1]

            #Non-directed, alphabetize pairs for grouping
            if direct_input.lower()=='y':
                pass
            else:
                if v1>v2:
                    temp_v=v1
                    v1=v2
                    v2=temp_v
            word_pairs_list.append({"source":v1,"target":v2,"query":query_num})

    else:
        #Co-Tweeted weights
        for kr in vector_range_co:
            value_range=range(len(each_tweet))
            value_range.remove(kr)
            for vr in value_range:
                v1=each_tweet[kr]
                v2=each_tweet[vr]
                if v1>v2:  #alphabetize pairs
                    temp_v=v1
                    v1=v2
                    v2=temp_v
                word_pairs_list.append({"source":v1,"target":v2,"query":query_num})



### Reduce list with count ###
'''
Code from stackoverflow. Comments mine.
'''
def canonical_dict(x):  #Orders dictionary items to make hashable.
    return sorted (x.items(), key=lambda x: hash(x[0]))
        #Returns a list of tuples, sorted by lambda key(?), eg: [('query',query_num),('source',v1),('target',v2)]

def unique_and_count(lst): #
    grouper=groupby(sorted(map(canonical_dict, lst))) 
        #MAP applies function to every iterable in object (function,iterable)
        #SORTED, sorts the list of returned lists
    return [dict(k+[('weight',len(list(g)))]) for k, g in grouper]
        #Returns dict of tuple list (cf. canonical_dict) + count dict
        #K is grouped list, G is an itertools object (?)
        #len(list(g)) returns the count of groupby, defined as weight for D3
'''
'''


word_pairs_list=unique_and_count(word_pairs_list)
    #Returns [{"weight":i, "query":query_num, "source":v1,"target":v2}, ...]
    #These are the bases for d3 links.




### Create Nodes List ###

nodes_list_dup=[] #will house nodes but with duplicates, temp dict
for wp in word_pairs_list:
    nodes_list_dup.append({"word":wp['source'],"group":wp['query'],"count":wp['weight']})
    nodes_list_dup.append({"word":wp['target'],"group":wp['query'],"count":wp['weight']})



'''
Stackoverflow solution. Comments mine. Need to look further into defaultdict library...
'''
dd=defaultdict(int)  #group dups on 'word' & 'group' and sum 'count'
for nd in nodes_list_dup:
    dd[nd['word'],nd['group']]+=nd['count']
nodes_list=[{'word':k[0], 'group':k[1],'count':v} for k,v in dd.iteritems()]

'''
'''
### Top nodes ###
nodes_list=sorted(nodes_list, key=lambda k:k['count'])[-node_input:]#Take top (node_input) nodes by count.



### Create D3 links ###
print "Create D3 links"
for wp in word_pairs_list:
    del wp['query']
    #Reset source/target values with the index in nodes_list
    for nl in nodes_list:
        if wp['source']==nl['word']: #and wp['query']==nl['group']:
            wp['source']=nodes_list.index(nl)
        elif wp['target']==nl['word']: #and wp['query']==nl['group']:
            wp['target']=nodes_list.index(nl)



### Remove any links that didn't get indexed ###     
word_pairs_list[:]=[x for x in word_pairs_list if isinstance(x['source'],int) and isinstance(x['target'],int)]





### ADD WHOLE TWEETS TO NODES ###
print "Adding Tweets"
#Adds random whole tweet to nodes list dicts
for nl in nodes_list:
    while True:
        temp_dict=choice(no_parse_list) #get random tweet from unsplit tweet dict
        
        tweet_text=temp_dict['tweet']#clean tweets for match to nl tweet
        tweet_text=tweet_text.lower()
        for p in punc:
            tweet_text=tweet_text.replace(p,"")

        if nl['group'] == temp_dict['query'] and nl['word'] in tweet_text:
            nl['tweet']=temp_dict['tweet']
            break




with open('data.json','w') as outfile:
    json.dump({"nodes":nodes_list,"links":word_pairs_list},outfile)



print len(nodes_list)






