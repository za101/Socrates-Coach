import re, time, datetime, json
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

#for Azure Web App Env
#from scripts.gpt_init_azure import getAzureGptInstance
#from scripts.gpt_init_openai import getOpenAiGptInstance

# for VS Code Local Env
from .gpt_init_azure import getAzureGptInstance
from .gpt_init_openai import getOpenAiGptInstance

class Transcript():
    def __init__(self, cached_content=[]):
        content_temp = []
        if(type(content_temp) == 'str'):
            content_temp = json.loads(cached_content)
        else:
            content_temp = cached_content
        self.content = content_temp

    def add_content(self, content, participant_name):
        #print("===T.add_content().self.content:", self.content)
        self.content.append({"name" : participant_name, "message" : content})

    def get_tokens(self):
        for item in self.content:
            if "tokens" in item:
                return item["tokens"]
        return 0

    def add_tokens(self, new_tokens):
        new_content = []
        tokens = 0
        for item in self.content:
            if "tokens" in item:
                tokens = item["tokens"]
            else:
                new_content.append(item)
        new_content.append({"tokens" : tokens + new_tokens})
        self.content = new_content

    def clear(self):
        self.content = []

    def to_string(self):
        content_str = ""
        for item in self.content:
            if "name" in item:
                content_str += f"{item['name']}: {item['message']}\n\n"
        return content_str

class TranscriptView():
    def __init__(self, transcript, participant):
        messages = []
        if participant.get_system_message():
            messages.append({"role" : "system", "content" : participant.get_system_message()})
        messages += participant._process_content(transcript.content)
        self.messages = list(messages)
        self.api_messages = list(messages)

    def add_message(self, role, content):
        new_message = {"role" : role, "content" : content}
        self.messages.append(new_message)
        self.api_messages.append(new_message)
    
    def truncate(self):
        for i in range(len(self.api_messages)):
            msg = self.api_messages[i]
            if msg['role'] != 'system':
                del self.api_messages[i]
                break

class Participant():
    def __init__(self, name, role, recipient=None):
        self.name = name
        self.role = role
        self.recipient = recipient
        self.system_message = None

    def _process_content(self, content):
        return []

    def get_system_message(self):
        return self.system_message

    def get_transcript_view(self, transcript):
        transcript_view = TranscriptView(transcript, self)
        return transcript_view

    def get_next_response(self, transcript, gpt_model):
        return "silent", ""

class AIParticipant(Participant):
    def __init__(self, name, default_system_message=None, system_messages={}, model='', **kwargs):
        super().__init__(name, "assistant", **kwargs)
        self.model = model
        print("\n\nSystem Messages\n&&&&&&&&&&&&&&&"+str(system_messages)+"\n&&&&&&&&&&&&&&&\n")
        print("\n\ndefault System Messages\n&&"+str(default_system_message)+"\n&&\n")
        if self.name in system_messages:
            self.system_message = system_messages[self.name]
        else:
            self.system_message = default_system_message

    def set_system_message(self, message, transcript):
        self.system_message = message
        transcript.add_content(f"Setting system message for {self.name} to [{message}].", "SystemAlert")

    def _get_api_response(self, transcript_view, gpt_host_model, request_uuid, initial_delay=20.0, max_attempts=5):
        print("=====1.=AIParticipant(Participant)._get_api_response():role:", self.name, gpt_host_model, request_uuid,)
        print("=====2.=AIParticipant(Participant)._get_api_response():inquire_texr:", type(transcript_view.api_messages))
        #print("=====3.=AIParticipant(Participant)._get_api_response():self.system_message:", self.system_message)
        [gpt_host, gpt_model] = gpt_host_model.split("::")
        gptmodel_instance = None
        openai_instance = None
        api_base = None
        if(gpt_host == 'Azure'):
            gptmodel_instance = getAzureGptInstance()
            openai_instance  = gptmodel_instance.get_openai_instance()
            api_base = gptmodel_instance.get_api_base()
        if(gpt_host == 'OpenAi'):
            gptmodel_instance = getOpenAiGptInstance()
            openai_instance  = gptmodel_instance.get_openai_instance()
            api_base = gptmodel_instance.get_api_base()
        print("===gptmodel_instance:api_base:", request_uuid, api_base, gpt_host, gpt_model)

        for attempt in range(max_attempts):
            try:
                needs_truncation = False
                try:
                    startTime = datetime.datetime.now()
                    print(f"===--------API start time: {request_uuid}, {startTime}, {gpt_host}, {gpt_model}", flush=True)
                    response = None
                    
                    
                    
                    if(gpt_host == 'Azure'):
                        print(f"===--------!!!---call Azure Gpt Api: {request_uuid}, {gpt_host}, {gpt_model}", flush=True)
                        #response = openai.ChatCompletion.create(model=self.model, messages=transcript_view.api_messages)

                        response = openai_instance.ChatCompletion.create(engine=gpt_model, messages=transcript_view.api_messages,
                            temperature=0.7, max_tokens=800,  top_p=0.95,  frequency_penalty=0,  presence_penalty=0, stop=None)
                    if(gpt_host == 'OpenAi'):
                        print(f"===--------!!!---call OpenAi Gpt Api: {request_uuid}, {gpt_host}, {gpt_model}", flush=True)
                        response = openai_instance.ChatCompletion.create(model=gpt_model, messages=transcript_view.api_messages)
                    
                    print("\n\nInput to Model\n\n********************\n"+str(transcript_view.api_messages)+"\n********************\nResponse\n\n"+str(response))

                    endTime = datetime.datetime.now()
                    print(f"===--------{self.name}: API end time and response time(seconds): {request_uuid}, {endTime.timestamp() - startTime.timestamp()} endTimestamp:{endTime} usage:{response['usage']}", flush=True)
                except openai_instance.error.InvalidRequestError as e:
                    if "maximum context length" in str(e):
                        needs_truncation = True
                print("===-------!!!---API:response:2:", self.name, request_uuid, response['usage'])
                finish_reason = 'length' if needs_truncation else response['choices'][0]['finish_reason']
                if finish_reason == 'length':
                    transcript_view.truncate()
                    #sreturn self._get_api_response_az(self, transcript_view, gpt_model)
                elif finish_reason == 'content_filter':
                    print('[AIParticipant] WARNING: az-gpt API call failed due to content filter.')
                elif finish_reason == 'null':
                    print('[AIParticipant] WARNING: az-gpt API call failed.')
                return response['choices'][0]['message']['content'], response['usage']['total_tokens']
            
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
        return "", 0
    
    def _get_api_response_openai(self, transcript_view, gpt_model, initial_delay=20.0, max_attempts=5):
        print("===AIParticipant(Participant)._get_api_response_openai():1.role::", self.name, self.model)
        gptmodel_instance = getOpenAiGptInstance()
        openai_instance  = gptmodel_instance.get_openai_instance()
        api_base = gptmodel_instance.get_api_base()
        print("===openai_gptmodel_instance:api_base:", api_base)
        response = None
        for attempt in range(max_attempts):
            try:
                needs_truncation = False
                try:
                    startTime = datetime.datetime.now()
                    print(f"===-----------openai api start time::: {startTime}, {openai_instance}, {transcript_view.api_messages}", flush=True)
                    response = openai_instance.ChatCompletion.create(model=gpt_model, messages=transcript_view.api_messages)
#                     response = openai_instance.ChatCompletion.create(
#   model="gpt-4",
#   messages=[
#     {"role": "system", "content": "You are a helpful assistant."},
#     {"role": "user", "content": "What are some famous astronomical observatories?"}
#   ]
# )
                    print('=================1...response:', response)    
                    endTime = datetime.datetime.now()
                    print("===-----------openai api end time and response time(seconds):", endTime, endTime.timestamp() - startTime.timestamp(),  response['usage'], flush=True)
                except openai_instance.error.InvalidRequestError as e:
                    if "maximum context length" in str(e):
                        needs_truncation = True
                except Exception as e:
                    print('=================2.response:', response)    
                print('=================3.response:', response)    
                # finish_reason = 'length' if needs_truncation else response['choices'][0]['finish_reason']
                # if finish_reason == 'length':
                #     transcript_view.truncate()
                #     return self._get_api_response(self, transcript_view)
                # elif finish_reason == 'content_filter':
                #     print('[AIParticipant] WARNING: API call failed due to content filter.')
                # elif finish_reason == 'null':
                #     print('[AIParticipant] WARNING: API call failed.')
                # return response['choices'][0]['message']['content'], response['usage']['total_tokens']
            
            except openai_instance.error.RateLimitError as e:
                #delay = initial_delay * (2 ** attempt)
                delay = initial_delay
                print(f"!!!!!![AIParticipant:OpenaiAPI] RateLimitError: Retrying in {delay} seconds.", e)
                time.sleep(delay)
            except openai_instance.error.APIConnectionError as e:
                delay = initial_delay
                print(f"!!!!!![AIParticipant:OpenaiAPI] APIConnectionError: Retrying in {delay} seconds.", e)
                time.sleep(delay)
            except Exception as e:
                exception_type = type(e).__name__
                print(f"!!!!!!--[AIParticipant:OpenaiAPI]: {type(e)}: An unexpected error occurred: {exception_type},  {e}")
                break
        return "", 0

class Clinician(AIParticipant): #Therapist
    def __init__(self, selected_belief, **kwargs):
        
        """
        import os
        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        print(script_dir)
        print("---------------")
        rel_path = "output.txt"
        abs_file_path = os.path.join(script_dir, rel_path)

        with open(abs_file_path, 'r') as file:
            belief = file.read()
        belief=belief.lower()
        print("HERE->>>>>>>")
        print(belief)
        """
        flag=0
        if (selected_belief['Therapist']== '')and  (selected_belief['Supservisor']== ''):
            flag=1
        belief=selected_belief['selected_belief']
        print("$$$$:"+str(selected_belief))
        belief=belief.lower()

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

        temp=""
        if flag==1:
            temp = "You are a practice patient with the goal of helping the user practice Socratic dialogue. Please mimic responses of a trauma survivor. Act like you are human who suffered from a " + str(belief) + " trauma and start talking about your trauma such as "+str(here[random.randint(0, 2)])
        else:
            temp=selected_belief['Therapist']
        print("\n\n\n\n\n\nTTe DEAGUT MSG FOR THERAPSI IS"+str(temp)+'\n\n\n\n\n\n\n\n'+str(flag)+"\n\n\n")        
        default_system_message=temp
        
        
        #default_system_message = "You are a practice patient with the goal of helping the user practice Socratic dialogue. Please mimic responses of a trauma survivor. Start with the belief such as It was my fault because of how I acted or dressed."
        
        super().__init__("Therapist", default_system_message=default_system_message, **kwargs)
        self.direct_messages = []

    def _process_content(self, content):
        processed_content = []
        for item in content:
            if item.get("name") == "Therapist":
                processed_content.append({"role" : "assistant", "content" : item['message']})
            elif item.get("name") == "Patient":
                processed_content.append({"role" : "user", "content" : item['message']})
        return processed_content

    def direct_message(self, message):
        self.direct_messages.append(message)

    def get_next_response(self, selected_belief,transcript, gpt_model, request_uuid, first_message=False):
        if first_message:
            transcript.clear()
        transcript_view = self.get_transcript_view(transcript)
        print("\n===Clinician/AI Patiient/Therapist:get_next_response():\n", transcript)
        print("\n\n\n\nlen(transcript_view.messages)"+str(len(transcript_view.messages))+"\n\n\n")
        if len(transcript_view.messages) == 1:
            """import os
            script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
            print(script_dir)
            print("---------------")
            rel_path = "output.txt"
            abs_file_path = os.path.join(script_dir, rel_path)

            with open(abs_file_path, 'r') as file:
                belief = file.read()"""
            flag=0
            if selected_belief['Therapist']=='' and  selected_belief['Supservisor']=='':
                flag=1
            belief=selected_belief['selected_belief']
            belief=belief.lower()
            print("HERE->>>>>>>")
            print(belief)
            #response = "Hello, I am Socrates Coach 1.0, an AI language model. I am here to help you practice your Socratic dialogue skills. Please select a type of trauma from the dropdown menu above. I will then roleplay a trauma patient who has experienced this trauma to help you practice. When you're ready, please ask me what belief I would like to work on."
            #response = "Hello, I am practice patient with the goal of helping the user practice Socratic dialogue."
            response =  "Hello, I am Socrates Coach 1.0, an AI language model. I am here to help you practice your Socratic dialogue skills. I will roleplay a trauma patient who has experienced this trauma to help you practice. When you're ready, please ask me what belief I would like to work on. My trauma type is "+str(belief)
            
        else:
            if self.direct_messages:
                for message in self.direct_messages:
                    transcript_view.add_message("assistant", message)
                self.direct_messages = []
            response, tokens = self._get_api_response(transcript_view, gpt_model, request_uuid)
            transcript.add_tokens(tokens)
            if not response:
                response = "I'm sorry, theres seems to have been an error in generating a response. Can you try asking again?"
        return "loud", response

class Supervisor(AIParticipant):
    def __init__(self, selected_belief,name="Supervisor", default_system_message=None, clinician=None, **kwargs):
        flag=0
        if  (selected_belief['Therapist']== '')and  (selected_belief['Supservisor']== ''):
            flag=1
        if default_system_message is None:
            if flag==1:
                default_system_message = "You are Socrates with the goal of improving the Trainee's Socratic dialogue. Read the following transcript, and offer the Trainee concise advice on how to improve the Socratic dialogue."
            else:
                default_system_message=selected_belief['Supservisor']
        
        super().__init__(name, default_system_message=default_system_message, **kwargs)
        self.clinician = clinician

    def _process_content(self, content, sparsity=5):
        message = ""
        cycles = 0
        for item in content:
            if item.get("name") in ["Therapist", "Patient"]:
                message += f"{item['name']}: {item['message']}\n\n"
                if item.get("name") == "Patient":
                    cycles += 1
        if cycles % sparsity != sparsity-1:
            return []
        return [{"role" : "user", "content" : message}]
    
    def get_next_response(self, selected_belief,transcript, gpt_model, request_uuid, first_message=False):
        
        transcript_view = self.get_transcript_view(transcript)
        print("\n===Supervisor:get_next_response():\n", transcript_view )
        if first_message or len(transcript_view.api_messages) < 2:
            return "quiet", ""
        res, tokens = self._get_api_response(transcript_view, gpt_model, request_uuid,)
        transcript.add_tokens(tokens)
        response = f"{res}"
        self.clinician.direct_message(response)
        return "loud", response

class Assessor(Supervisor):
    def __init__(self, selected_belief, field, check_threshold=lambda x : False, **kwargs):
        default_system_message = ""
        super().__init__(selected_belief,name="Assessor", default_system_message=default_system_message, **kwargs)
        self.field = field
        self.check_threshold = check_threshold
        self.state = "working"

    def _process_content(self, content):
        return super()._process_content(content, sparsity=1)
    
    def get_next_response(self, selected_belief,transcript, gpt_model, request_uuid):
        transcript_view = self.get_transcript_view(transcript)

        #response, tokens = self._get_api_response(transcript_view, gpt_model, request_uuid)
        print("\n===Assessor Skipped:get_next_response():\n", transcript_view )
        response, tokens = "", 0
        transcript.add_tokens(tokens)
        match = re.search(rf'{self.field}: ([\d\.]+)%', response.lower())
        rating = float(match.group(1)) / 100. if match else None
        # This logic is ugly, try to remove eventually or simplify to look like the Supervisor
        # START ugly
        stop = False
        if isinstance(rating, float):
            stop = self.check_threshold(rating)
        if stop and self.state == "working":
            message = f"[The patient's {self.field} is now {rating * 100.}%. " \
                      "This is beyond the threshold we were trying to reach.]"
            self.clinician.direct_message(message)
            response += "\n" + message + "\n"
            self.state = "finished"
        if not stop:
            self.state = "working"
        # END ugly
        return "quiet", response

class CliPatient(Participant):
    def __init__(self, io_handler, **kwargs):
        self.io_handler = io_handler
        super().__init__("Patient", "user", **kwargs)

    def get_next_response(self, selected_belief,transcript, gpt_model, request_uuid):
        user_input = self.io_handler.get_user_input()
        if user_input.lower() == "exit":
            self.recipient = None
        return "silent", user_input

class AsyncPatient(Participant):
    def __init__(self, **kwargs):
        super().__init__("Patient", "user", **kwargs)
        self.pending_response = None

    def set_pending_response(self, content):
        self.pending_response = content

    def get_next_response(self,selected_belief,transcript, gpt_model, request_uuid):
        #print("===AsyncPatient(Participant).get_next_response(self, transcript):", transcript)
        return "silent", self.pending_response

class Moderator():
    def __init__(self, participants, starting_participant=None):
        self.participants = participants
        self.cur_participant = None
        for participant in self.participants:
            if participant.name == starting_participant:
                self.cur_participant = participant
                break

    def get_participant(self):
        return self.cur_participant

    def set_participant(self, participant):
        self.cur_participant = participant

    def increment_participant(self):
        #print("===increment_participant(self).self.cur_participant:1:", self.cur_participant)
        if self.cur_participant is not None:
            for participant in self.participants:
                if participant.name == self.cur_participant.recipient:
                    self.cur_participant = participant
                    #print("===increment_participant(self).self.cur_participant:2:", self.cur_participant)
                    return
        self.cur_participant = None

class Room():
    def __init__(self, participants, io_handler, starting_participant=None, file_suffix="log", transcript_content=[], verbose=False):
        self.participants = participants
        self.moderator = Moderator(participants, starting_participant)
        self.transcript = Transcript(transcript_content)
        self.io_handler = io_handler
        self.file_suffix = file_suffix
        self.verbose = verbose

        # yuck
        self.version = 3.2

    def _run_participant(self, selected_belief,participant, gpt_model, request_uuid, **kwargs):
        print("===Room()._run_participant(self, participant, 1....)", request_uuid, participant, participant.name)
        volume, response = participant.get_next_response(selected_belief,self.transcript, gpt_model, request_uuid, **kwargs)
        print(f"===Room()._run_participant(self, participant, 2....), volume: {volume}, response:{type(response)}")
        self.transcript.add_content(response, participant.name)
        #print("===Room()._run_participant(self, participant, 3...), self.transcript:", self.transcript)
        if volume == "loud":
            quiet = False
        elif volume == "quiet":
            quiet = not self.verbose
        else:
            quiet = True
        if not quiet:
            return self.io_handler.deliver_output(response)

    def _run_participants_from(self, selected_belief,participant, gpt_model, request_uuid, **kwargs):
        #print("===Room()._run_participants_from(self, participant, ..).01:", participant)
        responses = []
        self.moderator.set_participant(participant)
        while participant is not None:
            #print("===Room()._run_participants_from(self, participant, ..).02:", participant)
            response = self._run_participant(selected_belief,participant, gpt_model, request_uuid, **kwargs)
            if response is not None:
                responses.append({"name" : participant.name, "message" : response})
            self.moderator.increment_participant()
            participant = self.moderator.get_participant()
            #print("===Room()._run_participants_from() after increment_participant().02:", participant)
        return responses

    def record(self):
        header = f"Version={self.version}\nTokens Used: {self.transcript.get_tokens()}"
        metadata = ["Participants:"]
        for participant in self.participants:
            metadata.append(f"  {participant.name}:")
            metadata.append(f"  - role: {participant.role}")
            if participant.get_system_message():
                metadata.append(f"  - system message: {participant.get_system_message()}")
        transcript = self.transcript.to_string()
        return header + "\n\n" + "\n".join(metadata) + "\n\n" + transcript

class SocraticDialogueRoom(Room):
    def __init__(self, selected_belief, patient, io_handler, transcript_content=[], system_messages={}, verbose=False):
        print("\n$$$$$$$$$$:"+str(selected_belief)+"\n")
        therapist = Clinician(selected_belief=selected_belief,system_messages=system_messages)
        supervisor = Supervisor(
            selected_belief=selected_belief,
            clinician=therapist,
            system_messages=system_messages
        )
        therapist.recipient = supervisor.name
        assessor = Assessor(
            selected_belief,
            field="belief strength",
            check_threshold=lambda x : x < 0.3,
            clinician=therapist,
            recipient=therapist.name,
            system_messages=system_messages
        )
        patient.recipient = assessor.name
        participants = [therapist, supervisor, assessor, patient]
        super().__init__(
            participants,
            io_handler,
            starting_participant=therapist.name,
            file_suffix="dialogue",
            transcript_content=transcript_content,
            verbose=verbose
        )

class CliSocraticDialogueRoom(SocraticDialogueRoom):
    def __init__(self, io_handler, verbose=False):
        patient = CliPatient(io_handler)
        super().__init__(patient, io_handler, verbose=verbose)
        self.participants[0].recipient = patient.name

    def run_room(self):
        participant = self.moderator.get_participant()
        self._run_participants_from(participant)

class AsyncSocraticDialogueRoom(SocraticDialogueRoom):
    def __init__(self, selected_belief,io_handler, transcript_content, system_messages={}, verbose=False):
        patient = AsyncPatient()
        print("\n$$$$:"+str(selected_belief)+"\n")
        super().__init__(selected_belief, patient, io_handler, transcript_content=transcript_content, system_messages=system_messages, verbose=verbose)

    def send_first_message(self, selected_belief, gpt_model, request_uuid):
        #print("===AsyncSocraticDialogueRoom(SocraticDialogueRoom).send_first_message(self)..FF11:")
        therapist = self.participants[0]
        allresponses = self._run_participants_from(selected_belief,therapist, gpt_model, request_uuid, first_message=True)
        #print("===AsyncSocraticDialogueRoom(SocraticDialogueRoom).send_first_message(self)..FF22:allresponses:", allresponses)
        return allresponses

    def handle_user_input(self, selected_belief, input, gpt_model, request_uuid):
        patient = self.participants[-1]
        #print("===AsyncSocraticDialogueRoom(SocraticDialogueRoom).handle_user_input(self, input):..AA11", input, patient)
        patient.set_pending_response(input)
        allresponses = self._run_participants_from(selected_belief,patient, gpt_model, request_uuid)
        #print("===AsyncSocraticDialogueRoom(SocraticDialogueRoom).handle_user_input(self, input):..AA22", input, patient)
        return allresponses
