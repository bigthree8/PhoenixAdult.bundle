import PAsearchSites
import PAgenres

def search(results,encodedTitle,title,searchTitle,siteNum,lang,searchByDateActor,searchDate, searchSiteID):
    if searchSiteID != 9999:
        siteNum = searchSiteID
    if siteNum != 670: # If it's any of the sites besides TushyRaw that have a search function, let's use that
        searchResults = HTML.ElementFromURL(PAsearchSites.getSearchSearchURL(siteNum) + encodedTitle)
        for searchResult in searchResults.xpath('//div[@class="pb6v16-1 fNpwyc"]'):
            titleNoFormatting = searchResult.xpath('.//img')[0].get('alt')
            scenePage = searchResult.xpath('.//a')[0].get('href')
            curID = scenePage.replace('/','_').replace('?','!')
            detailsPageElements = HTML.ElementFromURL(PAsearchSites.getSearchBaseURL(siteNum) + scenePage)
            bigScript = detailsPageElements.xpath('//footer/following::script[1]')[0].text_content()
            alpha = bigScript.find('"releaseDate":"')+15
            omega = bigScript.find('"',alpha)
            date = bigScript[alpha:omega]
            releaseDate = parse(date).strftime('%Y-%m-%d')
            if searchDate and releaseDate:
                score = 100 - Util.LevenshteinDistance(searchDate, releaseDate)
            else:
                score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())
            results.Append(MetadataSearchResult(id = curID + "|" + str(siteNum), name = titleNoFormatting + " [" + PAsearchSites.getSearchSiteName(siteNum) + "] " + releaseDate, score = score, lang = lang))
    else: # Special parsing for TushyRaw exact match until they get a search function put in
        encodedTitle = searchTitle.lower().strip().replace(' ','-')
        searchResults = HTML.ElementFromURL(PAsearchSites.getSearchBaseURL(siteNum) + '/' + encodedTitle)
        titleNoFormatting = searchResults.xpath('//h1[@data-test-component="VideoTitle"]')[0].text_content()
        curID = ("/"+encodedTitle).replace('/','_').replace('?','!')
        bigScript = searchResults.xpath('//footer/following::script[1]')[0].text_content()
        alpha = bigScript.find('"releaseDate":"')+15
        omega = bigScript.find('"',alpha)
        date = bigScript[alpha:omega]
        releaseDate = parse(date).strftime('%Y-%m-%d')
        score = 100
        results.Append(MetadataSearchResult(id = curID + "|" + str(siteNum), name = titleNoFormatting + " [" + PAsearchSites.getSearchSiteName(siteNum) + "] " + releaseDate, score = score, lang = lang))
    return results

def update(metadata,siteID,movieGenres,movieActors):
    url = PAsearchSites.getSearchBaseURL(siteID) + str(metadata.id).split("|")[0].replace('_','/').replace('!','?')
    detailsPageElements = HTML.ElementFromURL(url)
    art = []

    # Studio
    metadata.studio = "Strike 3"

    # Tagline (Site)
    metadata.tagline = PAsearchSites.getSearchSiteName(siteID)

    # Collections (Site and sometimes others like DVD name or series name)
    metadata.collections.clear()
    metadata.collections.add(metadata.tagline)

    # Summary
    metadata.summary = detailsPageElements.xpath('//meta[@name="description"]')[0].get('content').strip()

    # Title
    metadata.title = detailsPageElements.xpath('//h1[@data-test-component="VideoTitle"]')[0].text_content().strip()

    # Release Date
    wholeScript = detailsPageElements.xpath('//footer/following::script[1]')[0].text_content()
    bigScript = wholeScript[:wholeScript.find("itsUpAds")] # This should truncate bigScript to just the parts relevant to the current scene
    alpha = bigScript.find('"releaseDate":"')+15
    omega = bigScript.find('"',alpha)
    date = bigScript[alpha:omega]
    date_object = parse(date)
    metadata.originally_available_at = date_object
    metadata.year = metadata.originally_available_at.year    

    # Genres
    movieGenres.clearGenres()
    try:
        alpha = bigScript.find('"tags":[')+8
        omega = bigScript.find(']',alpha)
        genres = bigScript[alpha:omega].strip('"').split(',')
        for genre in genres:
            movieGenres.addGenre(genre.replace('"','').lower())
    except:
        # No Source for Genres, add manual
        if 'Blacked' in metadata.tagline:
            movieGenres.addGenre("Interracial")
        if 'Tushy' in metadata.tagline:
            movieGenres.addGenre("Anal")
        if 'Vixen' in metadata.tagline:
            movieGenres.addGenre("Boy Girl")
            movieGenres.addGenre("Caucasian Men")
            movieGenres.addGenre("Glamcore")
        if 'Deeper' in metadata.tagline:
            movieGenres.addGenre("Bondage")
        movieGenres.addGenre("Hardcore")
        movieGenres.addGenre("Heterosexual")

    # Actors
    movieActors.clearActors()
    actors = detailsPageElements.xpath('//div[@data-test-component="VideoModels"]/a')

    if len(actors) > 0:
        for actorLink in actors:
            actorName = actorLink.text_content()
            actorPageURL = actorLink.get("href")
            actorPage = HTML.ElementFromURL(PAsearchSites.getSearchBaseURL(siteID)+actorPageURL)
            actorBigScript = actorPage.xpath('//footer/following::script[1]')[0].text_content()
            alpha = actorBigScript.find('"src":"')+7
            omega = actorBigScript.find('"',alpha)
            actorPhotoURL = actorBigScript[alpha:omega].decode('unicode_escape')
            if 'http' not in actorPhotoURL:
                actorPhotoURL = PAsearchSites.getSearchBaseURL(siteID)+actorPhotoURL
            movieActors.addActor(actorName,actorPhotoURL)

    # Director
    metadata.directors.clear()
    director = metadata.directors.new()
    alpha = bigScript.find('directorNames')+16
    omega = bigScript.find('"',alpha)
    dirName = bigScript[alpha:omega]
    if dirName == "ull," or dirName == '':
        dirName = "Greg Lansky"
    director.name = dirName

    # Posters/Background
    valid_names = list()
    metadata.posters.validate_keys(valid_names)
    metadata.art.validate_keys(valid_names)

    # Background
    alpha = 0
    omega = 0
    alpha = bigScript.find('mainLandscape_1920x1080')
    alpha = bigScript.find('3x',alpha)
    alpha = bigScript.find('http',alpha)
    omega = bigScript.find('"',alpha)
    posterUrl = bigScript[alpha:omega].decode('unicode_escape')
    if 'http' not in posterUrl and posterUrl != '':
        posterUrl = PAsearchSites.getSearchBaseURL(siteID)+posterUrl
    Log("Background: "+posterUrl)
    art.append(posterUrl)

    # Promo Portait
    alpha = 0
    omega = 0
    alpha = bigScript.find('promoPortrait_')
    alpha = bigScript.find('3x',alpha)
    alpha = bigScript.find('http',alpha)
    omega = bigScript.find('"',alpha)
    posterUrl = bigScript[alpha:omega].decode('unicode_escape')
    if 'http' not in posterUrl and posterUrl != '':
        posterUrl = PAsearchSites.getSearchBaseURL(siteID)+posterUrl
    Log("Promo Portait: "+posterUrl)
    art.append(posterUrl)

    # Promo Portait (Landscape)
    alpha = 0
    omega = 0
    alpha = bigScript.find('promoLandscape_')
    alpha = bigScript.find('3x',alpha)
    alpha = bigScript.find('http',alpha)
    omega = bigScript.find('"',alpha)
    posterUrl = bigScript[alpha:omega].decode('unicode_escape')
    if 'http' not in posterUrl and posterUrl != '':
        posterUrl = PAsearchSites.getSearchBaseURL(siteID)+posterUrl
    Log("Promo Landscape: "+posterUrl)
    art.append(posterUrl)

    # Tall pictures
    i = 1
    alpha = 0
    omega = 0
    imageCount = bigScript.count('"width":800,"height":1200,"src"')
    while i <= imageCount:
        alpha = bigScript.find('"width":800,"height":1200,"src"',omega)+33
        omega = bigScript.find('"',alpha)
        posterUrl = bigScript[alpha:omega].decode('unicode_escape')
        if 'http' not in posterUrl and posterUrl != '':
            posterUrl = PAsearchSites.getSearchBaseURL(siteID)+posterUrl
        Log("artwork: "+posterUrl)
        art.append(posterUrl)
        i = i + 1

    # Wide pictures
    i = 1
    alpha = 0
    omega = 0
    imageCount = bigScript.count('"width":1200,"height":800,"src"')
    while i <= imageCount:
        alpha = bigScript.find('"width":1200,"height":800,"src"',omega)+33
        omega = bigScript.find('"',alpha)
        posterUrl = bigScript[alpha:omega].decode('unicode_escape')
        if 'http' not in posterUrl and posterUrl != '':
            posterUrl = PAsearchSites.getSearchBaseURL(siteID)+posterUrl
        Log("artwork: "+posterUrl)
        art.append(posterUrl)
        i = i + 1

    # Posters
    j = 1
    for posterUrl in art:
        if not PAsearchSites.posterAlreadyExists(posterUrl,metadata):            
            #Download image file for analysis
            try:
                img_file = urllib.urlopen(posterUrl)
                im = StringIO(img_file.read())
                resized_image = Image.open(im)
                width, height = resized_image.size
                #Add the image proxy items to the collection
                if(width > 1):
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Preview(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order = j)
                if(width > 100):
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Preview(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order = j)
                j = j + 1
            except:
                pass


    return metadata
