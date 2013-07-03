# -*- coding: utf-8 -*
import re, htmlentitydefs

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="8"
PLUGIN_PREFIX	= "/video/svt"

#WLPS
WLPS_SITE = "http://api.welovepublicservice.se"
WLPS_INDEX = WLPS_SITE + "/v1/showsimple/"
WLPS_EPISODES = WLPS_SITE + "/v1/episode/?show=%s&format=json"

# URLs
URL_SITE = "http://www.svtplay.se"
URL_INDEX = URL_SITE + "/program"
URL_LIVE = URL_SITE + "/?tab=live&sida=1"
URL_LATEST_SHOWS = URL_SITE + "/?tab=episodes&sida=1"
URL_LATEST_NEWS = URL_SITE + "/?tab=news&sida=1"
URL_CHANNELS = URL_SITE + "/kanaler"
URL_PROGRAMS = URL_SITE + "/ajax/program.json"
#Öppet arkiv
URL_OA_SITE = "http://www.oppetarkiv.se"
URL_OA_INDEX = "http://www.oppetarkiv.se/kategori/titel"
#Texts
TEXT_CHANNELS = u'Kanaler'
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_PREFERENCES = u'Inställningar'
TEXT_TITLE = u'SVT Play'
TEXT_LATEST_SHOWS = u'Senaste program'
TEXT_LATEST_NEWS = u'Senaste nyhetsprogram'
TEXT_OA = u"Öppet arkiv"
TEXT_CATEGORIES = u"Kategorier"
TEXT_SEARCH_SHOW = u"Sök program"
TEXT_SEARCH_RESULT = u"Sökresultat"
TEXT_SEARCH_FAIL = u"Hittade inga sökresultat för '%s'."
TEXT_CLIP = u"Klipp"

ART = 'art-default.jpg'
ICON = 'icon-default.png'

CACHE_1H = 60 * 60
CACHE_1DAY = CACHE_1H * 24
CACHE_30DAYS = CACHE_1DAY * 30

SHOW_SUM = "showsum"
DICT_V = 1

categories = {u'Barn':'barn', u'Dokumentär':'dokumentar', u'Film & Drama':'filmochdrama', \
              u'Kultur & Nöje':'kulturochnoje', u'Nyheter':'nyheter', \
              u'Samhälle & Fakta':'samhalleochfakta', u'Sport':'sport' }

cat2thumb = {u'Barn':'category_barn.png', \
             u'Dokumentär':'icon-default.png', \
             u'Film & Drama':'category_film_och_drama.png', \
             u'Kultur & Nöje':'category_kultur_och_noje.png', \
             u'Nyheter':'category_nyheter.png', \
             u'Samhälle & Fakta':'category_samhalle_och_fakta.png', \
             u'Sport':'category_sport.png'}

cat2url= {u'Barn':'/ajax/program?category=kids', \
             u'Dokumentär':'/ajax/program?category=documentary', \
             u'Film & Drama':'/ajax/program?category=filmAndDrama', \
             u'Kultur & Nöje':'/ajax/program?category=cultureAndEntertainment', \
             u'Nyheter':'/ajax/program?category=news', \
             u'Regionala':'/ajax/program?category=regionalNews', \
             u'Samhälle & Fakta':'/ajax/program?category=societyAndFacts', \
             u'Sport':'/ajax/program?category=sport'}

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():

    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    EpisodeObject.thumb = R(ICON)

    HTTP.CacheTime = 600

    if not "version" in Dict:
        Log("No version number in dict, resetting")
        Dict.Reset()
        Dict["version"] = DICT_V
        Dict.Save()

    if Dict["version"] != DICT_V:
        Log("Wrong version number in dict, resetting")
        Dict.Reset()
        Dict["version"] = DICT_V
        Dict.Save()

    if not SHOW_SUM in Dict:
        Log("No summary dictionary, creating")
        Dict[SHOW_SUM] = {}
        Dict.Save()

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@handler('/video/svt', TEXT_TITLE, thumb=ICON, art=ART)
def MainMenu():

    menu = ObjectContainer(title1=TEXT_TITLE)
    menu.add(DirectoryObject(key=Callback(GetIndexShows, prevTitle=TEXT_TITLE), title=TEXT_INDEX_SHOWS, thumb=R('main_index.png')))
    menu.add(DirectoryObject(key=Callback(GetChannels, prevTitle=TEXT_TITLE), title=TEXT_CHANNELS,
        thumb=R('main_kanaler.png')))
    menu.add(DirectoryObject(key=Callback(GetLiveShows, prevTitle=TEXT_TITLE), title=TEXT_LIVE_SHOWS, thumb=R('main_live.png')))
    menu.add(DirectoryObject(key=Callback(GetOAIndex, prevTitle=TEXT_TITLE), title=TEXT_OA,
        thumb=R('category_oppet_arkiv.png')))
    menu.add(DirectoryObject(
        key=Callback(GetLatestNews, prevTitle=TEXT_TITLE), title=TEXT_LATEST_NEWS, thumb=R('main_senaste_nyhetsprogram.png')))
    menu.add(DirectoryObject(
        key=Callback(GetLatestShows, prevTitle=TEXT_TITLE), title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png')))
    menu.add(DirectoryObject(key=Callback(GetCategories, prevTitle=TEXT_TITLE), title=TEXT_CATEGORIES,
        thumb=R('main_kategori.png')))
    menu.add(InputDirectoryObject(key=Callback(SearchShow),title = TEXT_SEARCH_SHOW, prompt=TEXT_SEARCH_SHOW,
        thumb = R('search.png')))

    Log(VERSION)

    return menu


#------------ CATEGORY FUNCTIONS ---------------------

def GetCategories(prevTitle):
    catList = ObjectContainer(title1=prevTitle, title2=TEXT_CATEGORIES)
    keys = categories.keys()
    keys.sort()
    for key in keys:
        d = DirectoryObject(key=Callback(GetCategoryShows, key=key, prevTitle=TEXT_CATEGORIES), \
                title=key, thumb=R(cat2thumb[key]))
        catList.add(d)

    return catList

#------------ SEARCH ---------------------
def SearchShow (query):
    query = unicode(query)
    oc = ObjectContainer(title1=TEXT_TITLE, title2=TEXT_SEARCH_RESULT)
    for video in GetAllShowsCombined():
        if len(query) == 1 and query.lower() == video.title[0].lower():
            # In case of single character - only compare initial character.
            oc.add(video)
        elif len(query) > 1 and query.lower() in video.title.lower():
            oc.add(video)

    if len(oc) == 0:
        return MessageContainer(
            TEXT_SEARCH_SHOW,
            TEXT_SEARCH_FAIL % query,
            )
    else:
        return oc

#------------ SHOW FUNCTIONS ---------------------
def GetIndexShows(prevTitle):
    showsList = ObjectContainer(title1=prevTitle, title2=TEXT_INDEX_SHOWS)
    json = JSON.ObjectFromURL(WLPS_INDEX)

    for show in json['objects']:
        showObj = CreateShowObject(show, TEXT_INDEX_SHOWS)
        showsList.add(showObj)

    return showsList

def CreateShowObject(jsonShow, parentTitle=None):

    show = DirectoryObject()
    showName = jsonShow['title']
    showUrl = WLPS_EPISODES % jsonShow['id']
    show.title = showName
    #show.thumb = ""
    #show.summary = ""
    show.key = Callback(GetShowEpisodes, prevTitle=parentTitle, showUrl=showUrl, showName=showName)

    return show

def MakeShowContainer(showUrl, title1="", title2="", sort=False):
    json = JSON.ObjectFromURL(showUrl)
    resultList  = ObjectContainer(title1=title1, title2=title2)
    
    for ep in json['objects']:
        resultList.add(GetEpisodeObject(ep, title1))

    return resultList

def GetShowEpisodes(prevTitle=None, showUrl=None, showName=""):
    return MakeShowContainer(showUrl, prevTitle, showName, False)

def GetLatestNews(prevTitle):
    epUrls = GetShowUrls(showUrl=URL_LATEST_NEWS, maxEp=15, addClips=False)
    return MakeShowContainer(epUrls, prevTitle, TEXT_LATEST_NEWS)

def GetLatestShows(prevTitle):
    epUrls = GetShowUrls(showUrl=URL_LATEST_SHOWS, maxEp=30, addClips=False)
    return MakeShowContainer(epUrls, prevTitle, TEXT_LATEST_SHOWS)

def GetChannels(prevTitle):
    page = HTML.ElementFromURL(URL_CHANNELS, cacheTime = 0)
    shows = page.xpath("//div[contains(concat(' ',@class,' '),' playJsSchedule-SelectedEntry ')]")
    thumbBase = "/public/images/channels/backgrounds/%s-background.jpg"
    channelsList = ObjectContainer(title1=prevTitle, title2=TEXT_CHANNELS)

    for show in shows:
        channel = show.get("data-channel")
        if channel == None:
            continue
        url = URL_CHANNELS + '/' + channel
        desc = show.get("data-description")
        thumb = show.get("data-titlepage-poster")
        if thumb == None:
            thumb = URL_SITE + thumbBase % channel

        title = show.get("data-title")
        airing = show.xpath(".//time/text()")[0]

        if 'svt' in channel:
            channel = channel.upper()
        else:
            channel = channel.capitalize()

        show = EpisodeObject(
                url = url,
                title = channel + " - " + title + ' (' + airing + ')',
                summary = desc,
                thumb = thumb)
        channelsList.add(show)
    return channelsList

def GetLiveShows(prevTitle):
    page = HTML.ElementFromURL(URL_LIVE, cacheTime=0)
    liveshows = page.xpath("//img[@class='playBroadcastLiveIcon']//../..")
    showsList = ObjectContainer(title1=prevTitle, title2=TEXT_LIVE_SHOWS)

    for a in liveshows:
        url = a.get("href")
        url = URL_SITE + url
        showsList.add(GetEpisodeObject(url))

    return showsList

#------------ EPISODE FUNCTIONS ---------------------
def GetEpisodeObject(jsonEp, show):

    url = jsonEp['url']
    show = show
    title = jsonEp['title']
    description = jsonEp['description']
    duration = 10 * 60 * 1000
    thumb = jsonEp['thumbnail_url']
    art = thumb
    air_date = None

    return EpisodeObject(
           url = url,
           show = show,
           title = title,
           summary = description,
           duration = duration,
           thumb = thumb,
           art = thumb,
           originally_available_at = air_date
         )

#------------OPEN ARCHIVE FUNCTIONS ---------------------
def GetOAIndex(prevTitle):
    showsList = ObjectContainer(title1 = prevTitle, title2=TEXT_OA)
    pageElement = HTML.ElementFromURL(URL_OA_INDEX)
    programLinks = pageElement.xpath("//a[@class='svt-text-default']")
    for s in CreateOAShowList(programLinks, TEXT_OA):
        showsList.add(s)
    return showsList

def CreateOAShowList(programLinks, parentTitle=None):
    showsList = []
    for l in programLinks:
        try:
            showUrl = l.get("href")
            Log("ÖA: showUrl: " + showUrl)
            showName = (l.xpath("text()")[0]).strip()
            Log("ÖA: showName: " + showName)
            show = DirectoryObject()
            show.title = showName
            show.key = Callback(GetOAShowEpisodes, prevTitle=parentTitle, showUrl=showUrl, showName=showName)
            showsList.append(show)
        except:
            Log(VERSION)
            pass

    return showsList

def GetOAShowEpisodes(prevTitle, showUrl, showName):
    episodes = ObjectContainer()
    pageElement = HTML.ElementFromURL(showUrl)
    epUrls = pageElement.xpath("//div[@class='svt-display-table-xs']//h3/a/@href")
    for url in epUrls:
        eo = GetOAEpisodeObject(url)
        if eo != None:
            episodes.add(eo)
    return episodes

def GetOAEpisodeObject(url):
    try:
        page= HTML.ElementFromURL(url)

        show = None
        title = page.xpath('//meta[@property="og:title"]/@content')[0].split(' | ')[0].replace('&amp;', '&')
        title = String.DecodeHTMLEntities(title)

        if ' - ' in title:
            (show, title) = title.split(' - ', 1)

        summary = page.xpath('//meta[@property="og:description"]/@content')[0].replace('&amp;', '&')
        summary = String.DecodeHTMLEntities(summary)
        thumb = page.xpath('//meta[@property="og:image"]/@content')[0].replace('/small/', '/large/')

        try:
            air_date = page.xpath("//span[@class='svt-video-meta']//time/@datetime")[0].split('T')[0]
            air_date = Datetime.ParseDate(air_date).date()
        except:
            air_date = None

        try:
            duration = page.xpath("//a[@id='player']/@data-length")
            duration = int(duration[0]) * 1000
        except:
            duration = None
            pass

        return EpisodeObject(
                url = url,
                show = show,
                title = title,
                summary = summary,
                art = thumb,
                thumb = thumb,
                duration = duration,
                originally_available_at = air_date)

    except:
        Log(VERSION)
        Log("Exception occurred parsing url " + url)
