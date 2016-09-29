import json, httplib2, re


def lambda_handler(event, context):

    assert context

    # grab the text string from the slack data object and remove the botname,
    # then split into a more usable array
    trigger_word = event['trigger_word']
    raw_text = event['text'].replace(trigger_word,'')
    raw_args = raw_text.split(' ')

    # setup the http connection used to communicate with the pagerduty api
    h = httplib2.Http(disable_ssl_certificate_validation=True)

    # load in data from the configuration file
    with open('pd_config.json') as data_file:
        pd_config = json.load(data_file)
    token = pd_config['api_token']

    # define the "help" feature function
    def help(data):
        return "usage: pdbot <option>\n" \
               "       options:\n" \
               "            help - print this help output.\n" \
               "            on-call|oncall - output the current ops person on-call.\n" \
               "            alert <text> - sends an alert to the on-call ops person, containing your text"

    # define the "on-call" feature function
    def oncall(data):
        return on_call_name+" is on-call"

    # define the "alert" feature function
    def alert(data):

        # handle empty "alerting" string
        if data == "fake_data":
            data = ""

        # trim the "alerting" string
        data = data.replace("alert ","")
        data = data.replace(" ","",1)

        # build the "event" data object to be sent to pagerduty
        event = {}
        event['service_key'] = pd_config['event_service_key']
        event['event_type'] = "trigger"
        event['description'] = "pdbot slack user initiated incident: "+data
        json_data = json.dumps(event)

        # send the "event" to pagerduty's event api
        try:
            resp, content = h.request(uri="https://events.pagerduty.com/generic/2010-04-15/create_event.json", method="POST", headers={"Authorization": "Token token=" + token},
                                  body=json_data)
        except:
            return "Oops! There are issues connecting to PagerDuty API, please try me again later"

        return on_call_name+' has been alerted: "'+data+'"'


    # retrieve current on-call person's name
    PD_API_URL = pd_config['pagerduty_url'] + '/api/v1/users/on_call'
    try:
        resp, content = h.request(PD_API_URL, headers={"Authorization": "Token token=" + token})  # need to handle token
        response_json = json.loads(content)
        for i in range(len(response_json['users'])):
            for j in range(len(response_json['users'][i]['on_call'])):
                if (response_json['users'][i]['on_call'][j]['level'] == pd_config['on_call_level']):
                    resp = response_json['users'][i]['name'], \
                           response_json['users'][i]['on_call'][j]['start'], response_json['users'][i]['on_call'][j]['end']
        on_call_name = resp[0]
    except:
        return_text="Oops! There are issues connecting to PagerDuty API, please try me again later"
        return {
            'text': "{0}".format(return_text)
        }

    # map the feature bot strings to the appropriate function
    commands = {
        'help': help,
        'on-call': oncall,
        'oncall' : oncall,
        'alert' : alert
    }

    # test the commands sent to make sure they match a known feature
    #  and if not output the help response
    try:
        if (re.search("help|alert|on-call|oncall",raw_args[1]) == None):
            return_text = help('fake_data')
            return {
                'text': "{0}".format(return_text)
            }
    except:
        return_text = help('fake_data')
        return {
            'text': "{0}".format(return_text)
        }

    # execute the correct mapped feature based on the commands sent
    if len(raw_args) > 2:
        arg_data = ' '.join(raw_args)
        return_text = commands[raw_args[1]](arg_data)
    elif len(raw_args) == 2:
        return_text = commands[raw_args[1]]('fake_data')
    else:
        return_text = help('fake_data')

    # return the response to api gateway
    return {
        'text': "{0}".format(return_text)
    }
