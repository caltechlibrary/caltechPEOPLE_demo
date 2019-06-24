# FUNCTIONS

# update name dict
# index of IDs by name (given or family)
def updateNameDict(ID, name, nameDict):
    if name not in nameDict:
        nameDict[name] = [ID]
    else:
        nameDict[name].append(ID)
    return

# flatten list of lists
# down to single list of IDs
def flattenList(sourceList):
    newList = []
    for e1 in sourceList:
        for e2 in e1:
            newList.append(e2)
    return newList

# search for strings in given and family names
def search(given, family, aut, adv, the, arc):
    # search2 is called twice, once each for familyNames and givenNames
    # returns list of qualifying IDs
    # result list is flattened, de-duped, sorted (case independent)
    def search2(searchString, nameDict):
        result = []
        for e in nameDict:
            if searchString.lower() in e.lower():
                result.append(nameDict[e])
        return sorted(list(dict.fromkeys(flattenList(result))), key=str.lower)
    # if all repos are checked, or no repos are checked
    if (aut and adv and the and arc) or (not aut and not adv and not the and not arc):
        result = [id for id in search2(family, familyNames) if id in search2(given, givenNames)]
    # if search is limited by repo then rebuilt index of names
    # this is faster than searching across all repos and then limiting the result!
    else:
        srchList = []
        if aut:
            for id in authors_dict:
                srchList.append(id)
        if adv:
            for id in advisors_dict:
                srchList.append(id)
        if the:
            for id in theses_dict:
                srchList.append(id)
        if arc:
            for id in archives_dict:
                srchList.append(id)
        familyNames_srch, givenNames_srch = {}, {}
        for name in givenNames:
            for id in givenNames[name]:
                if id in srchList:
                    updateNameDict(id, name, givenNames_srch)
        for name in familyNames:
            for id in familyNames[name]:
                if id in srchList:
                    updateNameDict(id, name, familyNames_srch)
        result = [id for id in search2(family, familyNames_srch) if id in search2(given, givenNames_srch)]
    return [(id, caltechpeople[id]['familyName']+', '+caltechpeople[id]['givenName']) for id in result]

# MAIN

# load data from TSV (replace URL_FOR_DATA with the location of the correctly structured TSV file)
import requests
data = requests.get('URL_FOR DATA').text
people = data.split('\n')
labels = people.pop(0)

# build data structures
caltechpeople = {} # dictionary of IDs
familyNames = {} # familyName index
givenNames = {} # givenName index
authors = [] # authors ID list
advisors = [] # advisors ID list
theses = [] # thesis authors ID list
archives = [] # archives agent ID list
for person in people:
    p = person.split('\t')
    ID = p[2]
    item = {}
    item['familyName'] = p[0]
    item['givenName'] = p[1]
    item['thesis_ID'] = p[4]
    item['advisor_ID'] = p[6]
    item['author_ID'] = p[8]
    item['archives_ID'] = p[10]
    item['directory_ID'] = p[12]
    item['viaf_ID'] = p[14]
    item['lcnaf_ID'] = p[16]
    item['isni_ID'] = p[17]
    item['wikidata_ID'] = p[18]
    item['snac_ID'] = p[20]
    item['orc_ID'] = p[21]
    item['image'] = p[23]
    caltechpeople[ID] = item
    updateNameDict(ID, caltechpeople[ID]["familyName"], familyNames)
    updateNameDict(ID, caltechpeople[ID]["givenName"], givenNames)
    if caltechpeople[ID]["thesis_ID"].strip():
        theses.append(ID)
    if caltechpeople[ID]["advisor_ID"].strip():
        advisors.append(ID)
    if caltechpeople[ID]["author_ID"].strip():
        authors.append(ID)
    if caltechpeople[ID]["archives_ID"].strip():
        archives.append(ID)
theses_dict = dict.fromkeys(theses)
advisors_dict = dict.fromkeys(advisors)
authors_dict = dict.fromkeys(authors)
archives_dict = dict.fromkeys(archives)

# WEB APPLICATION

from flask import Flask, render_template, request
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main_menu():
    if request.method != 'POST': # goto form
        return render_template('index.html', searchResult=[], 
                        given_srch="", family_srch="", rslt=False,
                        aut=False, adv=False, the=False, arc=False,
                        auCount=len(authors), adCount=len(advisors), 
                        thCount=len(theses), arCount=len(archives))
    else: # data returned from form
        aut, adv, the, arc = False, False, False, False
        if request.form.get('aut'):
            aut = True
        if request.form.get('adv'):
            adv = True
        if request.form.get('the'):
            the = True
        if request.form.get('arc'):
            arc = True
        searchResult = search(request.form['given'], request.form['family'], aut, adv, the, arc)
        return render_template('index.html', searchResult=searchResult, count=len(searchResult),
                        given_srch=request.form['given'], family_srch=request.form['family'], rslt=True,
                        aut=aut, adv=adv, the=the, arc=arc,
                        auCount=len(authors), adCount=len(advisors), 
                        thCount=len(theses), arCount=len(archives))

@app.route('/person/<person_ID>')
def displayPerson(person_ID):
    return render_template('person.html', person_ID=person_ID, person=caltechpeople[person_ID])

@app.route('/person/updatePerson?person_ID=<string:person_ID>', methods=['GET', 'POST'])
def upd_person(person_ID):
    if request.method != 'POST': # goto form
        return render_template('upd_person.html',
                               person_ID=person_ID, person=caltechpeople[person_ID]
                              )
    else:
        ID = request.form['person_ID']
        caltechpeople[ID]['familyName'] = request.form['familyName'].strip()
        caltechpeople[ID]['givenName'] = request.form['givenName'].strip()
        caltechpeople[ID]['thesis_ID'] = request.form['thesis_ID'].strip()
        caltechpeople[ID]['advisor_ID'] = request.form['advisor_ID'].strip()
        caltechpeople[ID]['author_ID'] = request.form['author_ID'].strip()
        caltechpeople[ID]['archives_ID'] = request.form['archives_ID'].strip()
        caltechpeople[ID]['directory_ID'] = request.form['directory_ID'].strip()
        caltechpeople[ID]['viaf_ID'] = request.form['viaf_ID'].strip()
        caltechpeople[ID]['lcnaf_ID'] = request.form['lcnaf_ID'].strip()
        caltechpeople[ID]['isni_ID'] = request.form['isni_ID'].strip()
        caltechpeople[ID]['wikidata_ID'] = request.form['wikidata_ID'].strip()
        caltechpeople[ID]['snac_ID'] = request.form['snac_ID'].strip()
        caltechpeople[ID]['orc_ID'] = request.form['orc_ID'].strip()
        caltechpeople[ID]['image'] = request.form['image'].strip()
        return render_template('person.html', person_ID=request.form['person_ID'], person=caltechpeople[request.form['person_ID']])
