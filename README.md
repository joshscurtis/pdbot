# pdbot - PagerDuty Slack Bot
# What is it?
**pdbot**  is a really simple Slack bot that integrates with PagerDuty's APIs to tell you who currently is on-call and to give you a way to send them a message as a PageryDuty event.

The bot is written to run as an "outgoing webhook" style Slack bot in AWS, on the API-Gateway/Lambda Function platform. A simple lamba-uploader [https://github.com/rackerlabs/lambda-uploader] config is provided. 


# Setup Instructions
##1. Download this project

##2. Pager Duty Setup
These setup instructions assume that you have an active PagerDuty account. If you're just testing this bot and PagerDuty, they provide a 14-day free trial. [https://www.pagerduty.com/]

####I. Create an API Token

- Navigate to "Configuration"->"API Access".
- Click "Create New API Key" button.
- Enter whatever you'd like for "Description".
- Choose "v1 Legacy" radio button.
- Checkmark the "Read-only API Key" box.
- Click "Create Key".
- Set aside the API key for later, and click "Close".


####II. Create an Event Service
 Create a new PagerDuty service, from the PagerDuty documentation:
			
			For creating a new Service with a "Generic API" integration:

				1. In your account, under the Services tab, click "Add New Service".
				2. Select "Use our API Directly" from the Integration Type menu and enter in an Integration Name.
				3. Enter a name for the service and select an escalation policy.
				4. Click the "Add Service" button.
				5. Once the service is created, you'll be taken to the Integrations tab for that service. On this page, you'll see the "Integration key", 
					which is referred to as "service_key" in our API documentation, and is needed to access the API.
				6. Set aside this key for later.
		
##3. Bot Setup

####I. Lambda Setup
- Install lambda-uploader
	
			pip install lambda-uploader

- Configure the bot
	* Open the file pdbot/pd_config.json in your favorite editor.
	* Enter your api_token, event_service_key, and complete your PagerDuty url.
	* If you have a complicated escalation policy, you can change the "on_call_level" config variable.
	* Install dependencies in the bot directory, from the root of the project
	
			pip install httplib2 -t pdbot

	* Upload the bot using deploy script
		* The deploy.sh script will use lambda-uploader to upload the bot to your AWS account, provided that you have credentials configured in your environment, eg. https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html
		* The user you use to upload must have full rights to the Lambda Service.
		* The bot itself needs an AWS execution role which needs the AmazonAPIGatewayInvokeFullAccess Managed Policy attached to it.
		* Once you've created the role, put it's arn in pdbot/lambda.json
		* Then simply call ./deploy.sh to push up to AWS.
		
				./deploy.sh
			
		* Verify that you now have a Lambda function named "pdbot"


####II. API Gateway Setup
- Create an API Gateway API
- Create a method of type: POST
- Select Integration Type: Lambda
- Select the region in which you created your Lambda function
- Select the Lambda Function you created
- Click "Integration Request"
- At the bottom of this Page select "Add mapping Template"
- For content type please specify: "application/x-www-form-urlencoded"
- Insert the template code below into the text field for the template. This code converts a 			URL Encoded form post into JSON for your Lambda function to parse
- Deploy your API

**Template Code**	
		
			## convert HTML POST data or HTTP GET query string to JSON
	
			## get the raw post data from the AWS built-in variable and give it a nicer name
			#if ($context.httpMethod == "POST")
			 #set($rawAPIData = $input.path('$'))
			#elseif ($context.httpMethod == "GET")
			 #set($rawAPIData = $input.params().querystring)
			 #set($rawAPIData = $rawAPIData.toString())
			 #set($rawAPIDataLength = $rawAPIData.length() - 1)
			 #set($rawAPIData = $rawAPIData.substring(1, $rawAPIDataLength))
			 #set($rawAPIData = $rawAPIData.replace(", ", "&"))
			#else
			 #set($rawAPIData = "")
			#end
	
			## first we get the number of "&" in the string, this tells us if there is more than one key value pair
			#set($countAmpersands = $rawAPIData.length() - $rawAPIData.replace("&", "").length())
	
			## if there are no "&" at all then we have only one key value pair.
			## we append an ampersand to the string so that we can tokenise it the same way as multiple kv pairs.
			## the "empty" kv pair to the right of the ampersand will be ignored anyway.
			#if ($countAmpersands == 0)
			 #set($rawPostData = $rawAPIData + "&")
			#end
	
			## now we tokenise using the ampersand(s)
			#set($tokenisedAmpersand = $rawAPIData.split("&"))
	
			## we set up a variable to hold the valid key value pairs
			#set($tokenisedEquals = [])
	
			## now we set up a loop to find the valid key value pairs, which must contain only one "="
			#foreach( $kvPair in $tokenisedAmpersand )
			 #set($countEquals = $kvPair.length() - $kvPair.replace("=", "").length())
			 #if ($countEquals == 1)
			  #set($kvTokenised = $kvPair.split("="))
			  #if ($kvTokenised[0].length() > 0)
			   ## we found a valid key value pair. add it to the list.
			   #set($devNull = $tokenisedEquals.add($kvPair))
			  #end
			 #end
			#end
	
			## next we set up our loop inside the output structure "{" and "}"
			{
			#foreach( $kvPair in $tokenisedEquals )
			  ## finally we output the JSON for this pair and append a comma if this isn't the last pair
			  #set($kvTokenised = $kvPair.split("="))
			 "$util.urlDecode($kvTokenised[0])" : #if($kvTokenised[1].length() > 0)"$util.urlDecode($kvTokenised[1])"#{else}""#end#if( $foreach.hasNext ),#end
			#end
			}
		

###4. Slack Setup

- In Slack, Go to Apps and Integrations
- Click Build in the top right
- Select Make a Custom Integration
- Select Outgoing Webhooks
- Pick a trigger word for your Bot! **"pdbot"**
- In URL, put the URL created by your API Gateway Deployment
- Save the integration

###5. Test your bot
Enter your slack room and type the trigger word, you should recieve the help message.

	
	usage: pdbot <option>
	      options:
	           help - print this help output.
	           on-call|oncall - output the current ops person on-call.
	           alert <text> - sends an alert to the on-call ops person, containing your text
	           
           
	
