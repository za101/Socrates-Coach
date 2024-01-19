# Socrates: an AI tool for socratic dialogue

## Overview

The code is organized as follows:
  * `scripts/`
    - `socratic_dialogue.py`: Implements the main functionality for socratic dialogue (see the class definitions there).
    - `run_socratic_dialogue.py`: Lagacy script for CLI version of the app. May not be quite functional now but might be useful for testing.
  * `static/`: Contains the javascript and css code for the web app.
  * `template/`: Contains the html code.
  * `main.py`: Implementation of the flask app. All the actual app logic is implemented here.
  * `app.yaml.template`: Included as an example of what environment variables the app expects to be defined.

### Details of socratic dialogue implementation

The implementation in `socratic_dialogue.py` introduces a number of concepts:
1. `Room`
1. `Participant`
1. `Trascript`/`TrascriptView`

Each socratic dialogue happens in a `Room`. Each `Room` contains a list of `Participant`s. Each `Participant` can do things like produce new statements (which we call responses) and let us know which other `Participant` is next to talk (if any). `Participant`s can be of various flavors, but the most important distinction is between `AIParticipant`s and other `Participant`s. The former are able to query a language model to obtain their next response. Each `Room` also contains a `Transcript`, which is a record of all the responses of the `Participant`s in that room. A `Transcript` can also be specialized into a `TranscriptView`, which is morally the part of a transcript which is relavent to a given `Participant`.

Socratic dialogue runs by querying the responses of the various `Participant`s in the room. At the end of the dialogue, the `Transcript` may be recorded to produce a reference of what happened.

## OpenAI API

We make heavy use of Chat Completions from the OpenAI API. Reading the [docs](https://platform.openai.com/docs/guides/chat) is recommended for anyone unfamiliar with the mechanics of this.

## Deploying to GCP

The app is currently hosted on the Google Cloud Platform using [Google App Engine](https://cloud.google.com/appengine). After setting up your command line environment (see https://cloud.google.com/sdk/docs/install-sdk), deploying new code to the live app is as simple as running the following command from your local repo.
```
gcloud app deploy
```
Note that you will need to create a new file `app.yaml` which fills in the definitions of the environment variables listed in `app.yaml.template`. **Make sure to add `app.yaml` to your `.gitignore` before pushing to make sure no sensitive variables are accidentally shared!**

## Activate python env
C:\git\github\socrates-folk\socrates> & c:/git/github/socrates-folk/socrates/.venv/Scripts/Activate.ps1

## Run flask command: 
.\.venv\Scripts\activate
flask --app app  run  or flask --app app --debug run

## The syntax on server
from scripts.io_interface import IOBase
from scripts.socratic_dialogue import AsyncSocraticDialogueRoom

## The syntax on VS Code
from .scripts.io_interface import IOBase
from .scripts.socratic_dialogue import AsyncSocraticDialogueRoom

## Deploy from VS Code
no need build or change env


