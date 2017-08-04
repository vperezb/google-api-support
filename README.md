# google-api-python-tools

Some functions to make Google APIs more accesible using Pandas. 

## Steps

1. Create google service account 
    1. Go to https://console.developers.google.com/projectselector/apis/credentials
    2. Create new project
    3. Share the file you want to access with the service "account" :
        first-service-account@example-id-175820.iam.gserviceaccount.com


## Motivation
I've been working with some Google APIs and I would like to share what I've learned.

[READ _RAW_ DATA] - [WORK WITH DATA] - [CREATE VALUABLE DATA] - [DISPLAY DATA]

I wanted to use Google APIs to develop a dashboard to analize and display data from Google Analytics, Google SearchConsole and Google Drive.

After retrieve the data, we can modify, filter, compare, delete and work with it 

## APIs used
* Sheets
* Analytics
* SearchConsole
* ... Someday


## Auth
There are two ways of authenticating to be able to make Google API calls.
* By redirecting the user to the web browser and then Log-in (the typical) within the account you want to use de data.
* By creating a Google service and download its credentials.json.

### When use client auth
If you are developing tools to deploy it in a computer with graphical env.
Is the easier to start and have full access to the info.

### When use Google service account
* If you want your API (or someones external API) to have access to only the services you want. IE: You built an API to read each morning your boss "todo today" document. In order to read it he can add _readonly_ permisions to the desired file to your service account. 

## Service accounts

#### Furhter information

