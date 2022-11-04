# Credentials for using google sheets, google slides and google drive APIs

## Create service credentials

* Create a project in https://console.cloud.google.com
* Download service credentials json
* When raising the work environment, set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` with the path for your credentials

## Create OAuth credentials

* Create a project in https://console.cloud.google.com
* Download OAuth credentials json
* When raising the work environment, set the environment variable `GOOGLE_OAUTH_CREDENTIALS` with the path for your credentials

## Creating a service account in Google

https://cloud.google.com/docs/authentication/production#creating_a_service_account

## Create credentials (OLD / not robust) [TO DELETE]

* Create a project in https://console.cloud.google.com
* Download service credentials json
* Rename-it to service_credentials.json
* GoogleApiSuppor.auth module will search for credentials file in the following order:
    0. In your home path, inside `.credentials` folder. Full path `~/.credentials/service_credentials.json`.
    0. -In your relative path `.credentials/service_credentials.json`.- Legacy, not recommended. 
