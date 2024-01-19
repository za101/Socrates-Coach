$(document).ready(function () {
    var warningShow50 = true
    var warningShow75 = true
    var warningShow90 = true
    var promptMap = {};
    var g_thumbicon_clickable = true
    var g_dialog_content = []
    var g_dialog_feedbacks = [] //0: no feedback, -1: thumbdown, 1: thumbup
    var g_transcript = { //refer to transcripts table in SQL database
        "id": 0,
        "userid": "",
        "username": "",
        "created_at": "",
        "updated_at": "",
        "dialog_title": "",
        "dialog_content": [],
        "transcript": "",
        "status": 0,
        "dialog_feedbacks": []
    }; 

    function getCookie(name) {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith(name + '='));
            
        if (cookieValue) {
            return cookieValue.split('=')[1];
        } else {
            return null;
        }
    }

    function insertDialog(name, message) {
        // let dialogSeqNumber = 0
        // if (g_dialog_content && g_dialog_content.length > 0) {
        //     dialogSeqNumber = g_dialog_content.length
        // }
        let dialog = {
            //"dialogSeqNumber": dialogSeqNumber, //dialog sequence in a transcript
            "name": name,    //role name: Therapist, Supervisor, Patient, Assessor
            "message": message
        }
        g_dialog_content.push(dialog)
        //console.log("===insertDialog():g_dialog_content:", g_dialog_content)
        return g_dialog_content.length
    }

    function buildDialogSelectOptions(dialogs) {
        let dialogListOptions = '<OPTION value="0"></option>'
        for(let dialog of dialogs) {
            let option = `<OPTION value=${dialog.id}>${dialog.dialog_title}</option>`
            dialogListOptions = dialogListOptions + option
        }
        return dialogListOptions
    }

    function buildUserMessage(userInput) {
        return `<div class="user-message">${userInput}</div>`
    }

    function buildAppMessage(appInput, dialogSeqNumber, withoutThumbIcon, feedback) {
        //console.log("===buildAppMessage::", appInput, dialogSeqNumber, withoutThumbIcon, feedback)
        if(withoutThumbIcon === 1) {
            return `<div class="app-message">${appInput}</div>`
        }else {
            let divThumb = ''
            if (feedback == 1) {
                divThumb = `
                <div class="socr-flex-container">
                    <div class="app-message">${appInput}</div>
                    <div class="socr-icon-container">
                        <i id="dialog-${dialogSeqNumber}-upoff" class="thumb-up-off-alt-black" style="display: none;"></i>
                        <i id="dialog-${dialogSeqNumber}-upon" class="thumb-up-alt-black" ></i>
                        <i id="dialog-${dialogSeqNumber}-downoff" class="thumb-down-off-alt-black" style="display: none;"></i>
                        <i id="dialog-${dialogSeqNumber}-downon" class="thumb-down-alt-black" style="display: none;"></i>
                    </div>
                </div>
                `
            } else if (feedback == -1) {
                divThumb = `
                <div class="socr-flex-container">
                    <div class="app-message">${appInput}</div>
                    <div class="socr-icon-container">
                        <i id="dialog-${dialogSeqNumber}-upoff" class="thumb-up-off-alt-black" style="display: none;"></i>
                        <i id="dialog-${dialogSeqNumber}-upon" class="thumb-up-alt-black" style="display: none;"></i>
                        <i id="dialog-${dialogSeqNumber}-downoff" class="thumb-down-off-alt-black" style="display: none;"></i>
                        <i id="dialog-${dialogSeqNumber}-downon" class="thumb-down-alt-black"></i>
                    </div>
                </div>
                `
            } else {
                divThumb = `
                <div class="socr-flex-container">
                    <div class="app-message">${appInput}</div>
                    <div class="socr-icon-container">
                        <i id="dialog-${dialogSeqNumber}-upoff" class="thumb-up-off-alt-black"></i>
                        <i id="dialog-${dialogSeqNumber}-upon" class="thumb-up-alt-black" style="display: none;"></i>
                        <i id="dialog-${dialogSeqNumber}-downoff" class="thumb-down-off-alt-black"></i>
                        <i id="dialog-${dialogSeqNumber}-downon" class="thumb-down-alt-black" style="display: none;"></i>
                    </div>
                </div>
                `
            }
            return divThumb
        }
    }

    function buildAuxMessage(auxInput) {
        return `<div class="aux-message">${auxInput}</div>`
    }

    function adjustTextareaHeight(textarea) {
        textarea.style.height = 'auto'; // Reset the height
        textarea.style.height = (textarea.scrollHeight) + 'px'; // Set the new height
    }

    function getDialogList() {
        //console.log("===getDialogList()....")
        $.ajax({
            url: '/get_dialog_list', 
            type: 'GET',
            contentType: 'application/json',
            beforeSend: function() {
                $('#spinner').show();
            },
            success: function (data) {
                $('#spinner').hide();
                //console.log("===data:", data)
                $('#transcriptList').empty();
                $('#transcriptList').append(buildDialogSelectOptions(data.dialogs))
            },
            error: function (error) {
                $('#spinner').hide();
                console.error('Error:', error);
            }
        });
    }

    function getLastTherapistDialogSeqNumber() {
       let therapistDialogSeqNumber = 0
       for(let i = 0; i < g_dialog_content.length; i++) {
        if(g_dialog_content[i].name === "Therapist") {
            therapistDialogSeqNumber++
        }
       }
       return therapistDialogSeqNumber - 1
    }
    function parseTokenUsage(tokenUsage) {
        try {
            return parseFloat(tokenUsage.replace('%', ''))/100
        } catch(e) {
            return 0
        }
    }
    function sendMessage() {
        const userInput = $("#user-input").val();
        if (userInput) {
            insertDialog("Patient", userInput)
            let userMsg = buildUserMessage(userInput)
            $("#chat").append(userMsg);
            $("#user-input").val('');
            $("#user-input").prop("disabled", true);
            let selected_gpt_model = $("#gpt-models option:selected").val();
            console.log("===:selected_gpt_model:", selected_gpt_model)
            
            var skillsSelect = document.getElementById("belief-names");
            var selectedText = skillsSelect.options[skillsSelect.selectedIndex].text;
            new_prompts = {}
            new_prompts['Therapist'] = document.getElementById('therapist-text').value
            new_prompts['Supservisor'] = document.getElementById('supervisor-text').value
            
    
            $.ajax({
                url: '/send_input', 
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ user_input: userInput, gpt_host:'azure', gpt_model: selected_gpt_model,selected_belief: selectedText,'Therapist':new_prompts['Therapist'],'Supservisor':new_prompts['Supservisor']}),
                beforeSend: function() {
                    $('#spinner').show();
                },
                success: function (data) {
                    //console.log("===sendMessage():data:", data.usage, data)
                    tokenUsage = parseTokenUsage(data.usage)
                    //console.log("=== tokenUsage:", tokenUsage)
                    $('#spinner').hide();
                    $("#user-input").prop("disabled", false);
                    if (data.no_remaining_tokens){
                        alert('You have used all your available tokens.')
                    } else if (tokenUsage > 0.9 && warningShow90) {
                        alert('You have used 90% of your tokens.')
                        warningShow90 = false
                        warningShow75 = false
                        warningShow50 = false
                    } else if (tokenUsage > 0.75 && warningShow75){
                        alert('You have used 75% of your tokens.')
                        warningShow75 = false
                        warningShow50 = false
                    } else if (tokenUsage > 0.5 && warningShow50){
                        alert('You have used 50% of your tokens.')
                        warningShow50 = false
                    }
                    for (const response of data.responses) {
                        if (response.name === "Therapist") {
                            let dialogSeqNumber = insertDialog("Therapist", response.message)
                            let lastTherapistDialogSeqNumber = getLastTherapistDialogSeqNumber()
                            let appMsg = buildAppMessage(response.message, lastTherapistDialogSeqNumber, 0, 0)
                            $("#chat").append(appMsg);
                        }
                        else {
                            let auxMsg = buildAuxMessage(response.message)
                            $("#chat").append(auxMsg);
                        }
                    }
                    // Scroll the chat container to the bottom
                    $(".chat-container").scrollTop($(".chat-container")[0].scrollHeight);
                    //console.log("===send msg: placeholder:", $("#user-input").attr('placeholder'))
                    $("#user-input").attr('placeholder', `Respond to Socrates. Please DO NOT enter any personal or sensitive information.`);
                },
                error: function (error) {
                    $('#spinner').hide();
                    $("#user-input").prop("disabled", false);
                    console.error('Error:', error);
                }
            });
        }
    }

    function showChat() {
        $(".chat-container").show();
        $(".side-by-side-right").show();
        $(".user-input-container").show();
        $(".input-menu-container").show();
    }

    function hideChat() {
        $(".chat-container").hide();
        $(".side-by-side-right").hide();
        $(".user-input-container").hide();
        $(".input-menu-container").hide();
    }

    function disableChat() {
        //console.log("===disableChat().....")
        $("#dialogpanel :input").prop("disabled", true);
        $("#end-chat").prop("disabled", true);
        g_thumbicon_clickable = false;
        $("#chat").css("opacity", "0.5");
    }

    function enableChat() {
        $("#dialogpanel :input").prop("disabled", false);
        $("#end-chat").prop("disabled", false);
        g_thumbicon_clickable = true;
        $("#chat").css("opacity", "");
    }

    function resetChat() {
        $("#chat").empty();
        $("#transcriptDateList").val('');
        g_dialog_content = []
        g_dialog_feedbacks = []

        var skillsSelect = document.getElementById("belief-names");
        var selectedText = skillsSelect.options[skillsSelect.selectedIndex].text;
        
        new_prompts = {}
        new_prompts['Therapist'] = document.getElementById('therapist-text').value
        new_prompts['Supservisor'] = document.getElementById('supervisor-text').value
        
        //console.log("===resetChat():g_dialog_feedbacks, g_dialog_content:", g_dialog_feedbacks, g_dialog_content)
        console.log("promptssss:")
        console.log(new_prompts)
        $.ajax({
            url: '/new_chat',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ selected_belief: selectedText ,'Therapist':new_prompts['Therapist'],'Supservisor':new_prompts['Supservisor']}),
            success: function (data) {
                if (data.responses[0].name === "Therapist") {
                    let appMsg = buildAppMessage(data.responses[0].message, 0, 1, 0)
                    insertDialog("Therapist", data.responses[0].message)
                    g_transcript.id = data.user_state_id
                    $("#chat").append(appMsg);
                    enableChat()
                }
                else {
                    let auxMsg = buildAuxMessage(response.content)
                    $("#chat").val(auxMsg);
                }
                //console.log("===reset msg: placeholder:", $("#user-input").attr('placeholder'))
                $("#user-input").attr('placeholder', `Respond to Socrates. Please DO NOT enter any personal or sensitive information.`);
            },
            error: function (error) {
                console.error('Error clearing chat:', error);
            }
        });
    }

    function getFeedbackRating(thumbIconName) {
        if(thumbIconName === "UPON") {
            return 1
        }
        if(thumbIconName === "DOWNON") {
            return -1
        }
        return 0
    }

    function feedbackExist(feedbacks, seqNumber) {
        for(let i = 0; i < feedbacks.length; i++) {
            if (feedbacks[i].dialogSeqNumber == seqNumber) {
                return i
            }
        }
        return -1
    }

    function updateTranscriptFeedback(thumbId, thumbIconName) {
        let therapistDialogSeqNumber =  parseInt(thumbId.match(/\d+/)[0])
        let feedbackRating = getFeedbackRating(thumbIconName)
        let dialog_content = g_dialog_content
        let feedbacks = g_dialog_feedbacks || []
        //let therapistDialogCount = 0
        //console.log("===updateTranscriptFeedback(1):", thumbId, thumbIconName, feedbackRating, dialog_content,feedbacks, g_dialog_feedbacks)
        for(let i = 0; i < dialog_content.length; i++) {
            if (dialog_content[i].name === "Therapist") {
                //if (therapistDialogSeqNumber === therapistDialogCount) {
                    let feedbackIndex = feedbackExist(feedbacks, therapistDialogSeqNumber)
                    //console.log("===updateTranscriptFeedback(2):feedbackExist?", feedbackIndex)
                    if (feedbackIndex >= 0) {
                        feedbacks[feedbackIndex]["rating"] = feedbackRating
                    } else {
                        let feedback = {
                            "name": "Therapist",
                            "dialogSeqNumber": therapistDialogSeqNumber,
                            "rating": feedbackRating
                        }
                        //console.log("===updateTranscriptFeedback(3):",feedback)
                        feedbacks.push(feedback)
                    }
                }
                //therapistDialogCount = therapistDialogCount + 1
            //}
        }
        g_dialog_feedbacks = feedbacks
        //console.log("===updateTranscriptFeedback(4):", feedbacks)
    }

    function sendFeedback(thumbId, thumbIcon) { 
        //console.log("====sendFeedback():thumbId, thumbIcon:", thumbId, thumbIcon)
        updateTranscriptFeedback( thumbId, thumbIcon)
        //console.log("====sendFeedback():after feedback:", g_dialog_feedbacks)
        $.ajax({
            url: '/feedback', 
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ "transcript": g_transcript, "dialog_feedbacks": g_dialog_feedbacks }),
            beforeSend: function() {
                $('#spinner').show();
            },
            success: function (data) {
                $('#spinner').hide();
            },
            error: function (error) {
                $('#spinner').hide();
                console.error('Error:', error);
            }
        });
    }

    $(document).on('click', '.thumb-up-off-alt-black',function () {
        let thumbId = this.id
        if(g_thumbicon_clickable) {
            sendFeedback(thumbId, "UPON")
            $(this).siblings(".thumb-up-alt-black").show();
            $(this).hide();
            $(this).siblings(".thumb-down-off-alt-black").hide()
            $(this).siblings(".thumb-down-alt-black").hide()
        } else {
            alert("This dialog is closed, you can not make comment, please contact administrator for support.")
        }
    });
    $(document).on("click", ".thumb-up-alt-black", function () {
        let thumbId = this.id
        if(g_thumbicon_clickable) {
            sendFeedback(thumbId, "UPOFF")
            $(this).siblings(".thumb-up-off-alt-black").show();
            $(this).hide();
            $(this).siblings(".thumb-down-off-alt-black").show()
        } else {
            alert("This dialog is closed, you can not make comment, please contact administrator for support.")
        }
    });
    $(document).on('click', '.thumb-down-off-alt-black', function () {
        let thumbId = this.id
        if(g_thumbicon_clickable) {
            sendFeedback(thumbId, "DOWNON")
            $(this).siblings(".thumb-down-alt-black").show();
            $(this).hide();
            $(this).siblings(".thumb-up-alt-black").hide();
            $(this).siblings(".thumb-up-off-alt-black").hide();
        } else {
            alert("This dialog is closed, you can not make comment, please contact administrator for support.")
        }
        });
    $(document).on("click", ".thumb-down-alt-black", function () {
        let thumbId = this.id
        if(g_thumbicon_clickable) {
            sendFeedback(thumbId, "DOWNOFF")
            $(this).hide();
            $(this).siblings(".thumb-down-off-alt-black").show();
            $(this).siblings(".thumb-up-off-alt-black").show();
        } else {
            alert("This dialog is closed, you can not make comment, please contact administrator for support.")
        }
    });

    // Send message on hitting the "Enter" key
    $("#user-input").on('keydown', function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });

    $("#send-response").on('click', function () {
        sendMessage();
    });

     $("#user-input").on('input', function () {
        adjustTextareaHeight(this);
    });

    
     
    $("#new-chat").on('click', function () {
        $("#transcriptList").val("0");
        console.log("promptssss:")
        resetChat();
        showChat();
        enableChat();
        getDialogList()
    });

    // $(document).ready(function() {
    //     var currentURL = window.location.href;
    //     var indexURL = currentURL.split('/').pop();
    //     console.log("===doc.ready:indexURL:", indexURL, "===currentURL", currentURL)
    //     if (indexURL === '' || indexURL === 'index') {
    //         console.log("===resetchat() is called.")
    //         resetChat();
    //     }
    // });

    /*
    $("#belief-names").change(function() {
        var selectedBelief = $(this).val();
        $.ajax({
            url: '/create_clinician', // Replace with your actual backend endpoint
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ selected_belief: selectedBelief }),
            success: function(response) {
                console.log('Success:', response);
            },
            error: function(error) {
                console.error('Error:', error);
            }
        });
    });
    */

    $("#end-chat").on("click", function() {
       $('#overlay-survey').removeClass('hidden')
    });

    $("#end-chat-bk").on("click", function() {
        $.ajax({
            url: '/end_chat',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({"transcriptId": g_transcript.id}),
            success: function (response) {
                disableChat()
                getDialogList()
                window.open(`https://docs.google.com/forms/d/e/1FAIpQLSdSdkDbEHjudPZEQv5epugRglQi3TubiVBjlZ4WVOzQpHFcjA/viewform?usp=pp_url&entry.1917585647=${response.user_key}`, '_blank');
            },
            error: function (error) {
                console.error('Error clearing chat:', error);
            }
        });
        //hideChat();
    });

    $(window).on('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'ArrowUp') {
            $('#overlay-developer').removeClass('hidden');
            $('#developer-password').removeClass('hidden')
        }
    });

    //var promptMap = {};
    function showDeveloperControls() {
        $('#therapist-textarea').val(promptMap["Therapist"]);
        $('#supervisor-textarea').val(promptMap["Supervisor"]);
        $('#assessor-textarea').val(promptMap["Assessor"]);
        $('#developer-controls').removeClass('hidden');
        $('#developer-password').addClass('hidden')
    }

    function hideDeveloperControlsAndOverlay() {
        $('#developer-controls').addClass('hidden');
        $('#overlay-developer').addClass('hidden');
    }

    $('#developer-password').on('keydown', function(e) {
        if (e.key === 'Enter') {
            var skillsSelect = document.getElementById("belief-names");
            var selectedText = skillsSelect.options[skillsSelect.selectedIndex].text;
            e.preventDefault();
            var entered_password = $(this).val();
            $.ajax({
                url: '/validate_password',
                method: 'POST',
                data: {
                    password: entered_password, selected_belief: selectedText
                },
                success: function(response) {
                    if (response.is_correct) {
                        $('#incorrect-password').addClass('hidden');
                        $('#developer-password').val('');
                        promptMap = response.system_messages
                        showDeveloperControls();
                    } else {
                        $('#incorrect-password').removeClass('hidden');
                        $('#developer-password').val('');
                    }
                }
            });
        }
    });

    $('#submit-prompts').on('click', function() {
        var therapistValue = $('#therapist-textarea').val();
        var supervisorValue = $('#supervisor-textarea').val();
        var assessorValue = $('#assessor-textarea').val();

        var skillsSelect = document.getElementById("belief-names");
        var selectedText = skillsSelect.options[skillsSelect.selectedIndex].text;
        
        $.ajax({
            url: '/submit_developer_prompts',
            method: 'POST',
            data: {
                therapist_prompt: therapistValue,
                supervisor_prompt: supervisorValue,
                assessor_prompt: assessorValue,
                selected_belief: selectedText
            },
            success: function(response) {
                hideDeveloperControlsAndOverlay();
                getTranscriptById(getCookie('user_state_id'))
            }
        });
    });

    $('#close-btn').on('click', function() {
        $('#overlay-developer').addClass('hidden');
        $('#developer-controls').addClass('hidden');
    });

    $("#report-issue").on("click", function() {
        $('#issue-content').removeClass('hidden');
    });

    $('#issue-close-btns').on('click', function() {
        $('#suggestion-content').addClass('hidden');
    });

    function analysis_html(dialogs) {
        let dialogListOptions = `<p>${dialogs}</p>`
        return dialogListOptions
    }
    $("#suggestion-button").on("click", function() {
        $('#suggestion-content').removeClass('hidden');
        
        //new_prompts['Therapist'] = document.getElementById('therapist-text').value
        
        console.log("\n\n\n\nSUGGESTION:\n\n\n")
        document.getElementById("suggest-head").innerHTML="Analyzing Socratic Dialog"
        document.getElementById("suggest-boxs").innerHTML="Please wait ..."
        $.ajax({
            url: '/suggest',
            type: 'POST',
            //contentType: 'application/json',
            //data: JSON.stringify({ a: 'a'}),
            success: function (data) {
                console.log("ABCDSSSSSS")
                document.getElementById("suggest-head").innerHTML="Complete Analysis of Socratic Dialog"
                document.getElementById("suggest-head").style.color = "green";
                //document.getElementById("suggest-box").innerHTML=`<p>DONE</p>`
                //document.getElementById("suggest-boxs").innerHTML=analysis_html(data.op[0])
                document.getElementById("suggest-boxs").innerHTML=data
                //$("#suggest-box").append(analysis_html(data.op[0]));
            },
            error: function (error) {
                console.log("ABCDSSSSSSQQQQQQQQQ")
                console.error('Error clearing chat:', error);
            }
        });
        
    });

    $('#issue-close-btn').on('click', function() {
        $('#issue-content').addClass('hidden');
    });

    $('#submit-issue').on('click', function() {
        var issueValue = $('#issue-textarea').val();

        $.ajax({
            url: '/report_issue',
            method: 'POST',
            data: {
                issue: issueValue,
            },
            success: function(response) {
                $('#issue-content').addClass('hidden');
                $('#issue-textarea').val('');
            }
        });
    });

    $('#submit-survey').on('click', function() {
        
        var surveyFeedbackValue = $('#survey-feedback-textarea').val();
        var selectedExperienceValue = $('input[name="experienceGroup"]:checked').val();
        var selectedHelpfulValue = $('input[name="helpfulGroup"]:checked').val();
        $.ajax({
            url: '/survey',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({     
                "surveyFeedback": surveyFeedbackValue,
                "surveyExperience": selectedExperienceValue,
                "surveyHelpful": selectedHelpfulValue
            }),          
            success: function(response) {
                $('#overlay-survey').addClass('hidden');
                $('#survey-feedback-textarea').val('');
                $('input[name="experienceGroup"]').prop('checked', false);
                $('input[name="helpfulGroup"]').prop('checked', false);
                disableChat()
                getDialogList()
            }
        });

        
    });

    $('#cancel-survey').on('click', function() {
        $('#overlay-survey').addClass('hidden');
        $('#survey-feedback-textarea').val('');
        $('input[name="experienceGroup"]').prop('checked', false);
        $('input[name="helpfulGroup"]').prop('checked', false);
    });

    function getFeedbackBySeq(countThrapist) {
        let feedbacks = g_dialog_feedbacks || []
        for(let i = 0; i < feedbacks.length; i++) {
            if(feedbacks[i].dialogSeqNumber == countThrapist) {
                return feedbacks[i].rating
            }
        }
        return 0
    }

    function buildChatContentByTranscript() { //The fisrt message: 1
        let dialogs = []
        let jsonDialogs = g_dialog_content
        let countThrapist = 0
        //console.log("===build dialog:",getCookie('verbose'), jsonDialogs)
        for(let i = 0; i < jsonDialogs.length; i++) {
            //console.log("===buildChatContentByTranscript():dialog:", jsonDialogs[i])
            if(jsonDialogs[i].name === "Therapist" && i == 0) {
                //console.log("===buildChatContentByTranscript(0):dialog:Therapist:1st:", jsonDialogs[i])
                dialogs.push(buildAppMessage(jsonDialogs[i].message, 0, 1, 0))
            } else if (jsonDialogs[i].name === "Therapist") {
                //console.log("===buildChatContentByTranscript(>0):dialog:Therapist:", jsonDialogs[i])
                countThrapist = countThrapist + 1
                let feedback = getFeedbackBySeq(countThrapist)
                dialogs.push(buildAppMessage(jsonDialogs[i].message, countThrapist, 0, feedback))
            } else if (jsonDialogs[i].name === "Patient") {
                dialogs.push(buildUserMessage(jsonDialogs[i].message))
            } else {
                if (getCookie('verbose') == 'True') {
                    dialogs.push(buildAuxMessage(jsonDialogs[i].message))
                }
            }
        }
        return dialogs
    }

    function getTranscriptById(tId) {
        $.ajax({
            url: `/get_transcript_by_id?transcriptId=${tId}`, 
            type: 'GET',
            contentType: 'application/json',
            beforeSend: function() {
                $('#spinner').show();
            },
            success: function (data) {
                $('#spinner').hide();
                //document.cookie = `user_state_id=${data.transcripts[0].id}; expires=Session; path=/`;
                //console.log("===getTranscriptById():data:", data)
                g_dialog_content = JSON.parse(data.transcripts[0].dialog_content)
                g_dialog_feedbacks = JSON.parse(data.transcripts[0].dialog_feedbacks)
                g_transcript.id = data.transcripts[0].id
                g_transcript.transcript = data.transcripts[0].transcript
                g_transcript.created_at = data.transcripts[0].created_at
                g_transcript.updated_at = data.transcripts[0].updated_at
                g_transcript.username = data.transcripts[0].username
                g_transcript.userid = data.transcripts[0].userid
                g_transcript.dialog_title = data.transcripts[0].dialog_title
                g_transcript.dialog_content = []
                g_transcript.status = data.transcripts[0].status
                g_transcript.dialog_feedbacks = []
                let appMsg = buildChatContentByTranscript()
                $("#chat").empty();
                $("#chat").append(appMsg);
                showChat();
                if (g_transcript.status == 1) {
                    disableChat()
                } else {
                    enableChat()
                }
            },
            error: function (error) {
                $('#spinner').hide();
                console.error('Error:', error);
            }
        });
    }

    $('#transcriptList').change(function(){
        getTranscriptById(this.value)
    });

    $('#terms-checkbox').change(function() {
        // Enable the login button if the checkbox is checked, disable it otherwise
        $('#disclaimer-accept').prop('disabled', !$(this).prop('checked'));
        $('#username').prop('disabled', !$(this).prop('checked'));
        $('#password').prop('disabled', !$(this).prop('checked'));
      });
    //$('#disclaimer').addClass('hidden');
    $('#disclaimer-accept').on('click', function() {
        $('#spinnerDisclaimer').show();
        var usernameValue = $('#username').val();
        var passwordValue = $('#password').val();
        $("#gpt-models").css("display", "none");

        $.ajax({
            url: '/accept_disclaimer',
            method: 'POST',
            data: {
                username: usernameValue,
                password: passwordValue,
            },
            success: function(response) {
                g_dialog_content = []
                g_dialog_feedbacks = []
                if (response.is_correct) {
                    $('#incorrect-login').addClass('hidden');
                    if(response.showModelSelection) {
                      $("#gpt-models").css("display", "block");
                    }
                    $('#username').val('');
                    $('#password').val('');
                    $('#disclaimer').addClass('hidden');
                    $('#transcriptList').empty()
                    $('#transcriptList').append(buildDialogSelectOptions(response.dialogs))
                } else {
                    $('#incorrect-login').removeClass('hidden');
                    $('#password').val('');
                }
                $('#spinnerDisclaimer').hide();
            },
            error: function (error) {
                $('#spinnerDisclaimer').hide();
                //console.error('Error:', error);
            }
        });
    });

    $("#refreshIcon").on('click', function(){
        //console.log("===refresh....", getCookie("username"))
        getDialogList()
    })
});