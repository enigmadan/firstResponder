import urllib.request
import urllib.parse
import re
import json


def title_except(s, exceptions):
    word_list = re.split(' ', s)
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        final.append(word in exceptions and word or word.capitalize())
    return " ".join(final)


def get_jsonparsed_data(url):
    """Receive the content of ``url``, parse it as JSON and return the
       object.
    """
    response = urllib.request.urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)


def url_data_req(url, values):
    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8') # data should be bytes
    req = urllib.request.Request(url, data)
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def get_fd_data():
    fd_data_raw = []
    fd_data = []
    local_filename, headers = urllib.request.urlretrieve('http://apps.sandiego.gov/sdfiredispatch/')
    for line in open(local_filename):
        m = re.match(r'<span id="gv1_ctl\d{2}_Label\d">([^\u0000<]*)', line.strip())
        if m is not None:
            fd_data_raw.append(title_except(m.group(1), ['st','PM','AM']))

    # iter through all items 4 at a time to split them into events
    it = iter(fd_data_raw)
    fd_data_temp = []
    for x in it:
        fd_data_temp.append({"date": x, "type": [next(it)], "street": next(it), "cross": next(it), "unit": [next(it)]})
    # combine items with multiple types/units
    # add an item to the data list
    fd_data.append(fd_data_temp[0])
    for x in fd_data_temp[1:]:
        addmore = True
        for y in fd_data:
            if x["date"] == y["date"] and x["street"] == y["street"] and x["street"] == y["street"]:
                addmore = False
                if x["type"][0] not in y["type"]:
                    y["type"].append(x["type"][0])
                if x["unit"][0] not in y["unit"]:
                    y["unit"].append(x["unit"][0])
        if addmore:
            fd_data.append(x)
    # get lat/lng from google
    for d in fd_data:
        jsondata = ""
        if d["cross"]:
            jsondata = get_jsonparsed_data('https://maps.googleapis.com/maps/api/geocode/json?address=' +
                                           d["street"].replace(" ", "+") + '+and+' +
                                           d["cross"].split("/")[0].replace(" ", "+") + '+San+Diego,+CA')
        else:
            jsondata = get_jsonparsed_data('https://maps.googleapis.com/maps/api/geocode/json?address=' +
                                           d["street"].replace(" ", "+") + '+San+Diego,+CA')
        d["lat"] = jsondata["results"][0]["geometry"]["location"]["lat"]
        d["lng"] = jsondata["results"][0]["geometry"]["location"]["lng"]
    return json.dumps(fd_data)

def get_chp_data():
    url = 'https://cad.chp.ca.gov/Traffic.aspx'
    target = "ddlComCenter"
    argument = ""
    values = {'__EVENTTARGET': target, '__EVENTARGUMENT': argument, 'ddlComCenter': 'BCCC'}
    chp_data = []

    page = url_data_req(url,values)
    m = re.findall(r'<td class="GVSelectColumn">(.*)</td>', page)
    if m is not None:
        for x in m:
            chp_data_raw = re.findall(r'(<td[^>]*>([^<]*)</td>)', x + "</td>")
            if chp_data_raw is not None:
                chp_data_temp = []
                for y in chp_data_raw:
                    chp_data_temp.append(y[1])
                chp_data.append({"number": chp_data_temp[0], "time": chp_data_temp[1],
                                 "type": chp_data_temp[2], "location": chp_data_temp[3],
                                 "location_desc": chp_data_temp[4], "area": chp_data_temp[5].replace("&nbsp;", "")})
    for d in chp_data:
        if d["area"] is not None:
            jsondata = get_jsonparsed_data('https://maps.googleapis.com/maps/api/geocode/json?address=' +
                                       d["location"].replace(" ", "+").replace("+/+", "+and+").replace("/", "+and+").replace("(", "").replace(")", "") +
                                       '+' + d["area"].replace(" ", "+") + ',+CA')
            d["lat"] = jsondata["results"][0]["geometry"]["location"]
            d["lng"] = jsondata["results"][0]["geometry"]["location"]["lng"]
        else:
            d["info"] = True
    return json.dumps(chp_data)

# run the scrapers
# print(get_fd_data())
# print(get_chp_data())

'''
get_fd_data() returns more accurate long,lat coordinates because it has better input data.

We'll need to figure out a better way to geocode the data from the chp.
'''

