import logging, uuid, json, os, datetime, urllib, ast, bcrypt
from flask import Flask, render_template, make_response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


# for Azure Web App Env
#from scripts.io_interface import IOBase
#from scripts.socratic_dialogue import AsyncSocraticDialogueRoom

#for VS Code Local Env
from .scripts.io_interface import IOBase
from .scripts.socratic_dialogue import AsyncSocraticDialogueRoom



#for Azure Web App Env
#from scripts.gpt_init_azure import getAzureGptInstance
#from scripts.gpt_init_openai import getOpenAiGptInstance

# for VS Code Local Env
from .scripts.gpt_init_azure import getAzureGptInstance
from .scripts.gpt_init_openai import getOpenAiGptInstance




"""
USERSALLOWMODELSELECTION = os.environ.get('USERS_ALLOW_MODEL_SELECTION')
USERNAME = os.environ.get('SQL_USERNAME')
USERPASS_KEYVAULT_KEY = os.environ.get('SQL_USERPASS_KEYVAULT_KEY')
DBNAME = os.environ.get('SQL_DBNAME')
#DBNAME = os.environ.get('SocratesCoachDev')
DATABASE_HOST = os.environ.get('SQL_DATABASE_HOST')
CONN_NAME = os.environ.get('SQL_CONN_NAME')

"""
USERSALLOWMODELSELECTION = "aarondev,pheld,rhp,test"
USERNAME = "SqlServerADMIN"
DBNAME = "SocratesCoachDev"
DATABASE_HOST = "ruanonprodrhsqlserver.database.windows.net"
CONN_NAME = "MSSQL"


#keyVaultName = os.environ["AZ_KEY_VAULT_NAME"]
keyVaultName = "rhnonprodkv"

KVUri = f"https://{keyVaultName}.vault.azure.net"
print("===============KVUri::app.py", type(KVUri))
credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)
#retrieved_secret = client.get_secret(USERPASS_KEYVAULT_KEY)
retrieved_secret = "RoadHomeNonProdSQL@"
#db_encryption_secret = client.get_secret('SOCRATE-SQL-DB-ENCRYPTION-KEY')
db_encryption_secret = "b'1lzHEa9BNwFLCJJFNzTOT5wigoDaRNlyjp85SP3svaE='"

#PASSWORD_ORI = retrieved_secret.value
PASSWORD_ORI = retrieved_secret

PASSWORD = urllib.parse.quote_plus(PASSWORD_ORI)
#DB_ENCRYPTION_KEY = ast.literal_eval(db_encryption_secret.value)
DB_ENCRYPTION_KEY = ast.literal_eval(db_encryption_secret)
#print("=========retrieved_secret:", retrieved_secret, DB_ENCRYPTION_KEY, type(DB_ENCRYPTION_KEY))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my_secret_key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pymssql://'+USERNAME+':'+PASSWORD+'@'+DATABASE_HOST+'/'+DBNAME
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#print("=========SQLALCHEMY_DATABASE_URI:", app.config['SQLALCHEMY_DATABASE_URI'])

app.logger.setLevel(logging.ERROR)
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
print("======getLogger('sqlalchemy'):Logger Level: ", logging.getLogger('sqlalchemy'))
logging.disable(logging.WARNING)
print("======test for print output")
print("======test for print(flush=True) output", flush=True)
app.logger.debug("======test for debug log")
app.logger.info("======test for info log")
app.logger.warning("======test for warning log")
#app.logger.error("======test for error log")
#app.logger.critical("======test for critical log")

from cryptography.fernet import Fernet
cipher_suite = Fernet(DB_ENCRYPTION_KEY)
# Encrypt function
def encrypt_text(text):
    encrypted_text = cipher_suite.encrypt(text.encode())
    return encrypted_text

# Decrypt function
def decrypt_text(encrypted_text):
    decrypted_text = None
    try:
        decrypted_text = cipher_suite.decrypt(encrypted_text).decode()
    except:
        decrypted_text = 'decryption error'
    return decrypted_text

def check_password_salthash(input_password, stored_hashed_password):
    # Check if the input password matches the stored hashed password
    return bcrypt.checkpw(input_password.encode('utf-8'), stored_hashed_password)

db = SQLAlchemy(app)
print("===db:",  db, DATABASE_HOST, DBNAME)

with app.app_context():
    try:
        db.session.execute(text('SELECT 1'))
        print('\n\n----------- Connection successful !')
    except Exception as e:
        print('\n\n----------- Connection failed ! ERROR : ', e)

class PassthroughIO(IOBase):
    def deliver_output(self, content):
        return content

passthrough_io = PassthroughIO()

class UserState(db.Model):
    __tablename__ = "user_state"
    __table_args__ = {"schema": "gpt"}
    id = db.Column(db.String(100), primary_key=True)
    state = db.Column(db.TEXT, nullable=False)
    state_bin = db.Column(db.LargeBinary)
    system_messages = db.Column(db.TEXT)
    username = db.Column(db.String(80), nullable=False)

    @property
    def state_data(self):
        #return json.loads(self.state)
        return json.loads(decrypt_text(self.state_bin))

    @state_data.setter
    def state_data(self, value):
        self.state = json.dumps([])
        self.state_bin = encrypt_text(json.dumps(value))

    @property
    def system_message_data(self):
        try:
            return json.loads(self.system_messages)
        except:
            return {}

    @system_message_data.setter
    def system_message_data(self, value):
        self.system_messages = json.dumps(value)
    
    def __str__(self):
        state_data = json.loads(decrypt_text(self.state_bin))
        return f"id: {self.id}, state: {state_data}"

class Transcripts(db.Model):
    __tablename__ = "transcripts"
    __table_args__ = {"schema": "gpt"}
    id = db.Column(db.String(100), primary_key=True)
    transcript = db.Column(db.TEXT, nullable=False)
    transcript_bin = db.Column(db.LargeBinary)
    created_at = db.Column(db.TIMESTAMP)
    updated_at = db.Column(db.TIMESTAMP, default=db.func.now())
    username = db.Column(db.TEXT)
    userid = db.Column(db.INT)
    dialog_title = db.Column(db.TEXT)
    dialog_content = db.Column(db.TEXT)
    dialog_content_bin = db.Column(db.LargeBinary)
    status = db.Column(db.INT)  # 1: chat end
    dialog_feedbacks = db.Column(db.TEXT) 
    dialog_survey = db.Column(db.TEXT) 

    @property
    def transcript_data(self):
        #return json.loads(self.dialog_content)
        return decrypt_text(self.transcript_bin)
    
    @transcript_data.setter
    def transcript_data(self, value):
        self.transcript = ''
        self.transcript_bin = encrypt_text(value)

    @property
    def dialog_content_data(self):
        #return json.loads(self.dialog_content)
        return json.loads(decrypt_text(self.dialog_content_bin))
    
    @dialog_content_data.setter
    def dialog_content_data(self, value):
        #self.dialog_content = json.dumps(value)
        self.dialog_content_bin = encrypt_text(json.dumps(value))

    @property
    def dialog_feedbacks_data(self):
        return json.loads(self.dialog_feedbacks)
    
    @property
    def dialog_survey_data(self):
        return json.loads(self.dialog_survey)
    
    @dialog_feedbacks_data.setter
    def dialog_feedbacks_data(self, value):
        self.dialog_feedbacks = json.dumps(value)

    @dialog_survey_data.setter
    def dialog_survey_data(self, value):
        self.dialog_survey = json.dumps(value)

    def __str__(self):
        return f"id: {self.id}, username: {self.username}, transcript: {self.transcript_data}"
    
class Credentials(db.Model):
    __tablename__ = "credentials"
    __table_args__ = {"schema": "gpt"}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    password_salthash = db.Column(db.LargeBinary, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        #return check_password_hash(self.password_hash, password)
        return check_password_salthash(password, self.password_salthash)
    
    def __str__(self):
        return f"id: {self.id}, username: {self.username}, hash: {self.password_hash}"

class UserUsage(db.Model):
    __tablename__ = "user_usage"
    __table_args__ = {"schema": "gpt"}
    username = db.Column(db.String(80), primary_key=True, nullable=False)
    token_usage = db.Column(db.Integer, nullable=False)
    token_usage_limit = db.Column(db.Integer, nullable=False, default=5000000) # 5 million tokens = $10 for gpt-3.5-turbo
    
    def __str__(self):
        return f"username: {self.username}, token_usage: {self.token_usage}"

def get_user_state_id_in_cookies():
    user_state_id = request.cookies.get('user_state_id')
    return user_state_id

def get_verbose():
    verbose = request.cookies.get('verbose')
    return verbose == "True"

def get_username():
    username = request.cookies.get('username')
    return username
def tempe(selected_belief):

    """import os
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    print(script_dir)
    print("---------------")
    rel_path = "scripts/output.txt"
    abs_file_path = os.path.join(script_dir, rel_path)

    with open(abs_file_path, 'r') as file:
        belief = file.read()
    belief=belief.lower()
    print("HERE->>>>>>>")
    print(belief)"""
    print("\nIn  tempe\n"+str(selected_belief))
    flag=0
    if selected_belief['Therapist']=='' and  selected_belief['Supservisor']=='':
        flag=1
    belief=selected_belief['selected_belief']
    belief=belief.lower()
    #print("piss "+str(belief))

    dic={
        'natural disasters':[
        "I have a natural disaster trauma. For example, I should have been able to protect my family.",
        "I have a natural disaster trauma. For example, Nature is always going to be a threat to me.",
        "I have a natural disaster trauma. For example, If I had been more prepared, I could have prevented the loss."],
        'sexual trauma':[
        "I have a sexual trauma. For example, It was my fault because of how I acted or dressed.",
        "I have a sexual trauma. For example, I can never trust anyone again.",
        "I have a sexual trauma. For example, People are always going to view me differently now."],
        'military / combat':[
        "I have a military / combat trauma. For example, I should have saved my fellow soldiers.",
        "I have a military / combat trauma. For example, Violence is the only way to solve problems.",
        "I have a military / combat trauma. For example, If I let my guard down, something bad will happen."],
        'childhood sexual trauma':[
        "I have a childhood sexual trauma. For example, I was a bad child to have let that happen.",
        "I have a childhood sexual trauma. For example, I am permanently damaged and can never fully heal.",
        "I have a childhood sexual trauma. For example, I can't have healthy relationships because of what happened to me."],
        'medical trauma':[
        "I have a medical trauma. For example, My body is weak and will always fail me.",
        "I have a medical trauma. For example, Medical professionals can't be trusted.",
        "I have a medical trauma. For example, I am a burden to others because of my health issues."]
    }
    import random
    if belief == "random trauma":
        here = random.choice(list(dic.values()))

    else:
        here = dic[str(belief)]
    print("++++++++++++++++++++")
    print(str(here[random.randint(0, 2)]))
    temp={}
    print("\n\nFLAG\n\n"+str(flag)+"\n\n")
    if flag==1:
        default_system_message = "You are a practice patient with the goal of helping the user practice Socratic dialogue. Please mimic responses of a trauma survivor. Act like you are human who suffered from a " + str(belief) + " trauma and start talking about your trauma such as "+str(here[random.randint(0, 2)])
        temp={'Therapist': default_system_message
            , 'Supervisor': "You are Socrates with the goal of improving the Trainee's Socratic dialogue. Read the following transcript, and offer the Trainee concise advice on how to improve the Socratic dialogue."
            , 'Assessor': ""}
    else:
        temp={'Therapist': selected_belief['Therapist']
            , 'Supervisor': selected_belief['Supservisor']
            , 'Assessor': ""}
    print("\nPROMPTS ARE:\n\n"+str(temp))
    return temp

def get_user_state(user_state_id):
    user_state = db.session.get(UserState, user_state_id)
    
    if user_state is None:
        user_state = UserState(id=user_state_id, username=get_username())
        user_state.state_data = []
        db.session.add(user_state)
        db.session.commit()
        #print("Okay I am in")
    #print("inside\n"+str(user_state_id)+"\n"+str(user_state.system_message_data)+"DONEDOONEDONE\n")
    return user_state

def get_user_usage_fraction(username=None, user_usage=None):
    if not user_usage and username:
        user_usage = db.session.get(UserUsage, username)
    if user_usage and user_usage.token_usage_limit:
        return float(user_usage.token_usage) / float(user_usage.token_usage_limit)
    return 0.

def get_user_state_and_room(selected_belief,user_state_id):
    user_state = get_user_state(user_state_id)
    #print("DEADDEADDEADMANMANMANMAN")
    print("\n@@@===get_user_state_and_room():user_state::", user_state_id)
    #print("\n@@@===get_user_state_and_room():user_state.system_message_data::", user_state.system_message_data)
    print("\nbefore tempe selected belief\n"+str(selected_belief))
    temp=tempe(selected_belief)
    
    room = AsyncSocraticDialogueRoom(selected_belief,io_handler=passthrough_io,
                                     transcript_content=user_state.state_data,
                                     #system_messages=user_state.system_message_data,
                                     system_messages=temp,
                                     verbose=get_verbose())
    return user_state, room

def init_user_state_and_room(selected_belief,user_state_id):
    user_state = get_user_state(user_state_id)
    user_state_default = get_user_state('')
    print("^^^^\n"+str(user_state)+"^^^^^^\n")
    #print(user_state_default.system_message_data)
    temp=tempe(selected_belief)
    print("\n\nBURRON init_user_state_and_room\n\n"+str(selected_belief))

    room = AsyncSocraticDialogueRoom(selected_belief,io_handler=passthrough_io,
                                     transcript_content=user_state.state_data,
                                     #system_messages=user_state_default.system_message_data,
                                     system_messages=temp,
                                     verbose=get_verbose())
    return user_state, room

def update_user_state(selected_belief,user_state, room, prev_tokens=None):
    user_state.state_data = room.transcript.content
    system_messages = get_system_messages(selected_belief,room)
    user_state.system_message_data = system_messages
    user_state.username = get_username()
    if prev_tokens is not None:
        num_tokens = room.transcript.get_tokens()
        username = get_username()
        user_usage = db.session.get(UserUsage, username)
        if user_usage is None:
            user_usage = UserUsage(username=username, token_usage=num_tokens)
            db.session.add(user_usage)
        else:
            user_usage.token_usage += (num_tokens - prev_tokens)
    db.session.commit()

def get_transcripts_by_username(user_name):
    items = Transcripts.query.filter_by(username=user_name).order_by(Transcripts.created_at.desc()).all()
    return items
def summarize(dialog_content):


    """import os, openai
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential

    keyVaultName = "rhnonprodkv"
    KVUri = f"https://{keyVaultName}.vault.azure.net"
    print("=======module==AZ_KV_Uri in socratic_dialogue:", KVUri)
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KVUri, credential=credential)

    openai.api_type = "azure"
    openai.api_version = "2023-07-01-preview"
    openai.api_base = client.get_secret('SOCRATE-AZ-OPENAI-API-BASE').value
    api_base = client.get_secret('SOCRATE-AZ-OPENAI-API-BASE').value
    openai.api_key = client.get_secret('SOCRATE-AZ-OPENAI-API-KEY').value
    
    print('=======module==az.openai.api_base:', openai.api_base)"""
    gptmodel_instance = getAzureGptInstance()
    openai_instance  = gptmodel_instance.get_openai_instance()
    #openai_instance  = openai
    api_base = gptmodel_instance.get_api_base()

    transcript=""
    print(dialog_content)
    for dialog in dialog_content:
        try:
            if(dialog['name'] == "Patient"):
                transcript+= "Therapist:"+dialog['message']+"\n"
            if(dialog['name'] == "Therapist"):
                transcript+= "Patient:"+dialog['message']+"\n"
        except:
            continue
    
    messages=[
    {"role": "system", "content": "You are a helpful assistant for text summarization of socratic dialogs. Read the entire transcript and give less than 10 words of summarization of the entire conversation between Therapist and Patient. Your response should be succient."},
    {"role": "user", "content": f"Summarize the conversation: Prompt: {transcript}"}
    ]
    initial_delay=20.0
    for attempt in range(5):
        try:
            needs_truncation = False
            try:
                response = None
                response = openai_instance.ChatCompletion.create(engine="rhgpt35turbo", messages=messages,
                temperature=0.7, max_tokens=800,  top_p=0.95,  frequency_penalty=0,  presence_penalty=0, stop=None)

                print("The response is:")
                print(response["choices"][0]["message"])
                
            except openai_instance.error.InvalidRequestError as e:
                if "maximum context length" in str(e):
                    needs_truncation = True
            finish_reason = 'length' if needs_truncation else response['choices'][0]['finish_reason']
            if finish_reason == 'length':
                print("ok")
            elif finish_reason == 'content_filter':
                print('[AIParticipant] WARNING: az-gpt API call failed due to content filter.')
            elif finish_reason == 'null':
                print('[AIParticipant] WARNING: az-gpt API call failed.')
            break
        
        except openai_instance.error.RateLimitError as e:
            #delay = initial_delay * (2 ** attempt)
            delay = initial_delay
            print(f"!!!!!![AIParticipant:Exception] RateLimitError: Retrying in {delay} seconds.", e)
            time.sleep(delay)
        except openai_instance.error.APIConnectionError as e:
            delay = initial_delay
            print(f"!!!!!![AIParticipant:Exception] APIConnectionError: Retrying in {delay} seconds.", e)
            time.sleep(delay)
        except Exception as e:
            exception_type = type(e).__name__
            print(f"!!!!!!-[AIParticipant:Exception]: {exception_type}: An unexpected error occurred: {e}, {type(e)}")
            break
    
    
    print("\n\nSummarization---------->\n"+str(response["choices"][0]["message"]['content']))
    return response["choices"][0]["message"]['content']

def createDialogTitle(dialog_content, createdTimestamp):
    return summarize(dialog_content)
    """
    for dialog in dialog_content:
        if(dialog['name'] == "Patient"):
            subject = dialog['message']
            if (subject):
                formatedTime = createdTimestamp.split(".")[0]
                formatedSubject = subject[0:50]
                #return '[' + formatedTime + '] ' + formatedSubject
                return formatedSubject
    """
#status: Transcript_Status_Open, Transcript_Status_Close
def update_transcripts(transcript_id, transcript_text, dialog_content):
    #print("===update_transcripts(11):dialog_content:", type(dialog_content), dialog_content)
    #print("===update_transcripts(12):transcript_text:", type(transcript_text), transcript_text)
    transcript = db.session.get(Transcripts, transcript_id)
    if transcript is None:
        currentTime = datetime.datetime.now()
        formatedTime = currentTime.strftime("%Y-%m-%d %H:%M:%S")
        transcript = Transcripts(id=transcript_id)
        transcript.transcript_data = transcript_text
        transcript.dialog_content_data = dialog_content
        transcript.dialog_title = createDialogTitle(dialog_content, formatedTime)
        transcript.username = get_username()
        transcript.created_at = db.func.now()
        transcript.updated_at = db.func.now()
        transcript.status = 0
        db.session.add(transcript)
    else:
        transcript.transcript_data = transcript_text
        transcript.dialog_content_data = dialog_content
        #transcript.dialog_feedbacks_data = dialog_feedbacks
        #transcript.username = get_username()
        transcript.updated_at = db.func.now()
    db.session.commit()

def update_transcript_feedback(transcript_id, dialog_feedbacks):
    #print("===update_transcript_feedback(12):dialog_feedbacks:", type(dialog_feedbacks), dialog_feedbacks)
    transcript = db.session.get(Transcripts, transcript_id)
    if transcript is None:
        print("===The transcript is not found!", transcript_id)
    else:
        transcript.dialog_feedbacks_data = dialog_feedbacks
        transcript.updated_at = db.func.now()
        db.session.commit()

def update_transcript_survey(transcript_id, dialog_survey):
    transcript = db.session.get(Transcripts, transcript_id)
    if transcript is None:
        print("===The transcript is not found!", transcript_id)
    else:
        transcript.dialog_survey_data = dialog_survey
        transcript.updated_at = db.func.now()
        transcript.status = 1
        db.session.commit()

def end_transcripts(user_state_id):
    transcript = db.session.get(Transcripts, user_state_id)
    print("===end_transcripts:", transcript)
    if transcript is None or transcript.dialog_title is None:
        return False
    else:
        transcript.updated_at = db.func.now()
        transcript.status = 1
        db.session.commit()
        return True

def remove_user_state(user_state_id):
    user_state = UserState.query.get(user_state_id)
    if user_state is not None:
        db.session.delete(user_state)
        db.session.commit()

def get_system_messages(selected_belief,room=None):
    system_messages = {}
    #print("===get_system_messages(): 1.room:", room)
    #print("===get_system_messages(): 2.get_user_state_id_in_cookies():", get_user_state_id_in_cookies())
    if room is None:
        _, room = get_user_state_and_room(selected_belief,get_user_state_id_in_cookies())
    for participant in room.participants:
        #print("===get_system_messages(): 3.in the loop:participant:", participant)
        if participant.get_system_message():
            system_messages[participant.name] = participant.get_system_message()
    return system_messages

def getDialogList(username):
    transcripts = get_transcripts_by_username(username)
    dialogs = []
    for item in transcripts:
        #print("===item:", item.username, item.id, item.created_at)
        dialogs.append(
            {
                "id": item.id, 
                "username":item.username, 
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "dialog_title": item.dialog_title
            }
        )
    return dialogs

@app.route('/validate_password', methods=['POST'])
def validate_password():
    password = request.form.get('password')
    selected_belief = request.form.get('selected_belief')
    dev_user = Credentials.query.filter_by(username="developer@socrates.ai").first()
    print("===/validate_password", dev_user)
    is_correct = dev_user and dev_user.check_password(password)
    system_messages = get_system_messages(selected_belief) if is_correct else {}
    #print("===/validate_password:system_messages:", system_messages)
    response_data = {
        "is_correct" : is_correct,
        "system_messages" : system_messages
    }
    return jsonify(response_data)

def showModelSelection(user):
    userlist = USERSALLOWMODELSELECTION.split(',')
    if user in userlist:
        return True
    else:
        return False
    
@app.route('/accept_disclaimer', methods=['POST'])
def accept_disclaimer():
    username = request.form.get('username')
    password = request.form.get('password')
    user = Credentials.query.filter_by(username=username).first()
    print(f"===/accept_disclaimer:user:",username, password, user, type(user), showModelSelection(username))
    success = user and user.check_password(password)
    print(f"===/accept_disclaimer:success: {username}, {success}", flush=True)
    if (success):
        dialogs = getDialogList(username)
        response = make_response(jsonify({"is_correct" : True, "showModelSelection": showModelSelection(username), "dialogs": dialogs}))
        response.set_cookie('username', username)

    else:
        response = make_response(jsonify({"is_correct" : False}))
        response.set_cookie('username', "")
    return response

@app.route('/submit_developer_prompts', methods=['POST'])
def submit_extra_data():
    new_prompts = {}
    new_prompts['Therapist'] = request.form.get('therapist_prompt')
    new_prompts['Supservisor'] = request.form.get('supervisor_prompt')
    new_prompts['Assessor'] = request.form.get('assessor_prompt')

    selected_belief = request.form.get('selected_belief')
    selected_belief = {'selected_belief':selected_belief,'Therapist':new_prompts['Therapist'],'Supservisor':new_prompts['Supservisor']}
    user_state, sd_room = get_user_state_and_room(selected_belief,get_user_state_id_in_cookies())
    #user_state, sd_room = get_user_state_and_room('')
    print(f"==========/submit_developer_prompts.user_state: {type(user_state.state)}")
    #print(f"==========/submit_developer_prompts.sd_room:222 {sd_room}")
    for participant in sd_room.participants:
        if participant.name in new_prompts:
            participant.set_system_message(new_prompts[participant.name], sd_room.transcript)
    update_user_state(selected_belief,user_state, sd_room)
    response = make_response(jsonify(success=True))
    response.set_cookie('verbose', "False")
    print("\n\nBUTTON PRESSED\n\n")
    return response

@app.route('/send_input', methods=['POST'])
def handle_send_input():

    data = request.get_json()
    a1 = data.get('selected_belief')
    a2 = data.get('Therapist')
    a3 = data.get('Supservisor')

    

    selected_belief = {'selected_belief':a1,'Therapist':a2,'Supservisor':a3}

    """
    if selected_belief['Therapist']==None:
        selected_belief['Therapist']=''
    if selected_belief['Supservisor']==None:
        selected_belief['Supservisor']=''
    """

    

    startTime = datetime.datetime.now()
    data = request.get_json()
    #user_input = data.get('user_input')
    user_input = data['user_input']
    gpt_model = data['gpt_model']

    print("Thank God Again *** "+str(selected_belief)+" ** "+str(data['gpt_model'])+" ****** "+"\n")

    usage_fraction = get_user_usage_fraction(username=get_username())
    request_uuid = get_username() + '---' +  str(startTime.timestamp())

    print("===/send_input:usage_fraction:", request_uuid, startTime, gpt_model, usage_fraction, get_user_state_id_in_cookies(), user_input, flush=True)
    no_remaining_tokens = False
    if usage_fraction > 1.:
        responses = []
        no_remaining_tokens = True
    else:
        user_state, sd_room = get_user_state_and_room(selected_belief,get_user_state_id_in_cookies())
        cur_tokens = sd_room.transcript.get_tokens()
        responses = sd_room.handle_user_input(selected_belief,user_input, gpt_model, request_uuid) #send user input to chatgpt
        update_user_state(selected_belief,user_state,sd_room, prev_tokens=cur_tokens)
        usage_fraction = get_user_usage_fraction(username=get_username())
        text_transcript = sd_room.record()
        dialog_content = user_state.state_data
        #print("===/send_input:text_transcript:", text_transcript)
        #print("===/send_input:dialog_content:", dialog_content)
        update_transcripts(get_user_state_id_in_cookies(), text_transcript, dialog_content)
    
    endTime = datetime.datetime.now()
    print(f"===/send_input:end time: {request_uuid},  {endTime}, total(seconds): {endTime.timestamp() - startTime.timestamp()}, user:{get_username()}",  flush=True)
    return jsonify({
        'responses': responses,
        'usage' : f"{usage_fraction * 100:.1f}%",
        'no_remaining_tokens' : no_remaining_tokens
    })
def suggest_convo(dialog_content):
    gptmodel_instance = getAzureGptInstance()
    openai_instance  = gptmodel_instance.get_openai_instance()
    #openai_instance  = openai
    api_base = gptmodel_instance.get_api_base()

    transcript=""
    print(dialog_content)
    for dialog in dialog_content:
        try:
            if(dialog['name'] == "Patient"):
                transcript+= "Therapist:"+dialog['message']+"\n"
            if(dialog['name'] == "Therapist"):
                transcript+= "Patient:"+dialog['message']+"\n"
        except:
            continue
    
    messages=[
    {"role": "system", "content": "You are a expert analyzer assistant of socratic dialogs. Read the entire transcript between Therapist and Patient and analyze Therapist responses and see where the Therapist can do better in responding to Patient and suggest how should a Therapist respond to patient instead. Also, rate the Therapist responses on the scale  of 1 to 10."},
    {"role": "user", "content": f"Analyse the conversation: Prompt: {transcript}"}
    ]
    initial_delay=20.0
    for attempt in range(5):
        try:
            needs_truncation = False
            try:
                response = None
                response = openai_instance.ChatCompletion.create(engine="rhgpt35turbo", messages=messages,
                temperature=0.7, max_tokens=800,  top_p=0.95,  frequency_penalty=0,  presence_penalty=0, stop=None)

                print("The response is:")
                print(response["choices"][0]["message"])
                
            except openai_instance.error.InvalidRequestError as e:
                if "maximum context length" in str(e):
                    needs_truncation = True
            finish_reason = 'length' if needs_truncation else response['choices'][0]['finish_reason']
            if finish_reason == 'length':
                print("ok")
            elif finish_reason == 'content_filter':
                print('[AIParticipant] WARNING: az-gpt API call failed due to content filter.')
            elif finish_reason == 'null':
                print('[AIParticipant] WARNING: az-gpt API call failed.')
            break
        
        except openai_instance.error.RateLimitError as e:
            #delay = initial_delay * (2 ** attempt)
            delay = initial_delay
            print(f"!!!!!![AIParticipant:Exception] RateLimitError: Retrying in {delay} seconds.", e)
            time.sleep(delay)
        except openai_instance.error.APIConnectionError as e:
            delay = initial_delay
            print(f"!!!!!![AIParticipant:Exception] APIConnectionError: Retrying in {delay} seconds.", e)
            time.sleep(delay)
        except Exception as e:
            exception_type = type(e).__name__
            print(f"!!!!!!-[AIParticipant:Exception]: {exception_type}: An unexpected error occurred: {e}, {type(e)}")
            break
    
    
    print("\n\nAnalysis---------->\n"+str(response["choices"][0]["message"]['content']))
    return response["choices"][0]["message"]['content']

@app.route('/suggest', methods=['POST'])
def start_suggest():
    #user_state, sd_room = get_user_state_and_room(get_user_state_id_in_cookies())
    #if not user_state_id:
    
    transcript = db.session.get(Transcripts, get_user_state_id_in_cookies())
    dialog_content = transcript.dialog_content_data
    print("\n\n\nhere dialog contents is\n"+str(dialog_content))
    output = suggest_convo(dialog_content)
    print("\n\n\nhere the op is\n"+str(output))
    db.session.commit()
    final=""
    for i in output.split('\n'):
        if i=='\n':
            final+='<br>'
        else:
            final+='<p>'+i+'</p>'

    return final
    
    #return ""

@app.route('/new_chat', methods=['POST'])
def start_new_chat():
    #user_state, sd_room = get_user_state_and_room(get_user_state_id_in_cookies())
    #if not user_state_id:

    data = request.get_json()
    selected_belief = data.get('selected_belief')
    new_prompts={}
    new_prompts['Therapist'] = data.get('Therapist')
    new_prompts['Supservisor'] = data.get('Supservisor')

    """
    if new_prompts['Therapist']==None:
        new_prompts['Therapist']=''
    if new_prompts['Supservisor']==None:
        new_prompts['Supservisor']=''
    """

    print("\n\nHere are the new prompts :"+str(data))
    


    selected_belief = {'selected_belief':selected_belief,'Therapist':new_prompts['Therapist'],'Supservisor':new_prompts['Supservisor']}
    print("Thank God ********************* "+str(selected_belief)+"\n") 

    print(f"===/new_chat:")
    print("NEW PROMPTSSSSSSS\n")
    print(new_prompts)
    print(selected_belief)
    print('\n******************\n')
    user_state_id = str(uuid.uuid4())
    user_state, sd_room = init_user_state_and_room(selected_belief,user_state_id)
    responses = sd_room.send_first_message(selected_belief,'', '')
    usage_fraction = get_user_usage_fraction(username=get_username())
    print(f"===/new_chat:: user_state: {user_state}, user_state.sys-msg:{user_state.system_message_data}")

    for participant in sd_room.participants:
        print("===/new_chat:::sd_room.participants:", participant)
        #print("===/new_chat:::sd_room.participants:sys-msg:", participant.get_system_message())


    update_user_state(selected_belief,user_state, sd_room)
    response = make_response(jsonify({'responses': responses, 'usage' : "", 'user_state_id': user_state_id}))
    response.set_cookie('user_state_id', user_state_id)
    return response

@app.route('/report_issue', methods=['POST'])
def report_issue():
    issue = request.form.get('issue')
    print("===/report_issue:", issue)
    transcriptId = get_user_state_id_in_cookies()
    items = Transcripts.query.filter_by(id=transcriptId).all()
    print("===/report_issue:", items)
    for item in items:
        print()
        user_state, sd_room = get_user_state_and_room(get_user_state_id_in_cookies())
        sd_room.transcript.add_content(issue, "UserFeedback")
        text_transcript = sd_room.record()
        dialog_content = user_state.state_data
        update_transcripts(get_user_state_id_in_cookies(), text_transcript, dialog_content)
        return '', 200
    return '', 204

@app.route('/end_chat', methods=['POST'])
def end_chat():
    print("===/end_chat:")
    payload = request.get_json()
    #remove_user_state(get_user_state_id_in_cookies())
    #dialog_content = transcript.dialog_content
    transcriptId = end_transcripts(payload["transcriptId"])
    return jsonify({'transcript.id' : transcriptId})

@app.route('/create_clinician', methods=['POST'])
def create_clinician():
    data = request.get_json()
    selected_belief = data.get('selected_belief')
    print("MY  BELIEF "+str(selected_belief))
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    rel_path = "scripts/output.txt"
    abs_file_path = os.path.join(script_dir, rel_path)
    print(script_dir)
    with open(abs_file_path, 'w') as file:
        
        #file.write(abs_file_path+"\n")
        file.write(selected_belief)
    return ""

@app.route('/get_dialog_list', methods=['GET'])
def get_dialog_list():
    print("===/get_dialog_list:")
    username = get_username()
    dialogs = getDialogList(username)
    return jsonify({'dialogs': dialogs})

@app.route('/feedback', methods=['POST'])
def feedback():
    payload = request.get_json()
    print("===/feedback:payload:", payload)
    user_state, sd_room = get_user_state_and_room(get_user_state_id_in_cookies())
    transcript_txt = sd_room.record()
    transcript = payload["transcript"]
    dialog_feedbacks = payload["dialog_feedbacks"]
    update_transcript_feedback(transcript["id"], dialog_feedbacks)
    return jsonify({'transcript_id' : transcript["id"]})

@app.route('/survey', methods=['POST'])
def survey():
    payload = request.get_json() 
    print("===/survey:payload:", payload)
    transcript_id = get_user_state_id_in_cookies()
    update_transcript_survey(transcript_id, payload)
    return jsonify({'transcript_id' : transcript_id})

@app.route('/get_transcript_by_id', methods=['GET'])
def get_transcripts_by_id():
    transcripts = []
    args = request.args
    transcriptId = args.get('transcriptId')
    print(f"===/get_transcript_by_id: {transcriptId}", flush=True)
    items = Transcripts.query.filter_by(id=transcriptId).all()
    for item in items:
        #print("===item:", item.username, item.id, item.created_at)
        #print("===item:", type(item), item)
        transcripts.append(
            {
                "id": item.id, 
                "transcript": decrypt_text(item.transcript_bin),
                "created_at": item.created_at,
                "username":item.username, 
                "usernid":item.userid, 
                "updated_at": item.updated_at,
                "dialog_title": item.dialog_title,
                "dialog_content": decrypt_text(item.dialog_content_bin),
                "status": item.status,
                "dialog_feedbacks": item.dialog_feedbacks
            }
        )
    response = make_response(jsonify({"is_correct" : True, "transcripts": transcripts}))
    response.set_cookie('user_state_id', transcriptId)
    return response

@app.route('/')
def index():
    # user_state_id = get_user_state_id_in_cookies()
    # print("======= route/............user_state_id in cookies:", user_state_id)
    # if not user_state_id:
    #     user_state_id = str(uuid.uuid4())
    # transcripts = []
    # try:
    #    transcripts = get_transcripts_by_username('aarondev')
    # except Exception as error:
    #     print("=======Exception: get_transcripts_by_username", error )
    print(f"======/ Socrates home page is rendered.", flush=True)
    response = make_response(render_template('index.html'))
    response.set_cookie('user_state_id', "")
    response.set_cookie('username', "")
    response.set_cookie('verbose', "False")
    return response

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
