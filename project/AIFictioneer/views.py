from django.shortcuts import render
from decouple import Csv, config
from django.http import JsonResponse
from rest_framework.reverse import reverse
from django.views.decorators.csrf import csrf_exempt
from .models import Prompt
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import * 
import openai
from openai import OpenAI
import json
from django.contrib.auth.decorators import login_required

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication, SessionAuthentication


###################################### GPT-4 API CALL ####################################################################################################

# GPT-4 API Configuration
api_key = config('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def call_gpt4_api(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-05-13", #gpt-4o-2024-05-13
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Please modify and regenerate the content based on this input."}
            ],
            max_tokens=4000
        )
        generated_text = response.choices[0].message.content
        return generated_text
    except Exception as e:
        # print(f"An error occurred: {str(e)}")
        return f"An error occurred: {str(e)}"   
          
        
###################################### INDEX #############################################################################################################
def index(request):
    return render(request, 'AIFictioneer/index.html')        

###################################### IDIATION STAGE ####################################################################################################      

# Background Story Generation Logic Function        
def generate_background_story(title, genre, initial_story_outline, character_profiles, max_words_background_story):
    try:
        background_story_generation_prompt_obj = Prompt.objects.get(name='BACKGROUND_STORY_GENERATION_PROMPT')
        background_story_generation_prompt_content = background_story_generation_prompt_obj.content
    except Prompt.DoesNotExist:
        return "Error: BACKGROUND_STORY_GENERATION_PROMPT not found in the database."

    # include max words in the prompt if specified and greater than 0
    if max_words_background_story and max_words_background_story > 0:
        max_words_clause = f"Max Words: {max_words_background_story}."
    else:
        max_words_clause = "No word count limit."

        # Prepare the formatted prompt
    formatted_prompt = background_story_generation_prompt_content.format(
        title=title,
        genre=genre,
        initial_story_outline=initial_story_outline,
        character_profiles=character_profiles,  # Ensure this is formatted correctly for the prompt
        max_words_background_story=max_words_clause  # Include the max words clause, adjusted above
    )

    # call_gpt4_api to make the API call and generate the background story
    generated_text = call_gpt4_api(formatted_prompt)

    return generated_text


# Background Story Refinement Logic Function
def refine_background_story(background_story, narrative_engineer_feedback):
    try:
        background_story_refinement_prompt_obj = Prompt.objects.get(name='BACKGROUND_STORY_REFINEMENT_PROMPT')
        background_story_refinement_content = background_story_refinement_prompt_obj.content
    except Prompt.DoesNotExist:
        return "Error: BACKGROUND_STORY_REFINEMENT_PROMPT not found in the database."

    # Format the prompt to include the background story and narrative_engineer feedback
    formatted_prompt = background_story_refinement_content.format(
        background_story=background_story,
        narrative_engineer_feedback=narrative_engineer_feedback
    )

    # Use call_gpt4_api to make the API call and refine the background story
    # print(formatted_prompt)
    refined_text = call_gpt4_api(formatted_prompt)

    return refined_text

@login_required
def ideation(request):
    context = {
        'generated_background_story': None,
        'refined_background_story': None,
        'form_data': {
            'title': '',
            'genre': '',
            'initial_story_outline': '',
            'character_profiles': [],
            'max_words_background_story': 0,
            'edited_story': '',
            'narrative_engineer_feedback_prompt': ''
        }
    }

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'generate':
            # Extracting data from the POST request
            title = request.POST.get('title', '')
            genre = request.POST.get('genreSelect')
            initial_story_outline = request.POST.get('initial_story_outline')
            max_words_str = request.POST.get('max_words_background_story', '').strip()
            max_words_background_story = int(max_words_str) if max_words_str.isdigit() else None

            # Preparing character profiles from the POST data
            character_profiles = []
            for key in request.POST:
                if key.startswith('characterName'):
                    index = key[len('characterName'):]
                    character_profiles.append({
                        'name': request.POST.get(key),
                        'traits': request.POST.get(f'characterTraits{index}'),
                        'background': request.POST.get(f'characterBackground{index}')
                    })

            # Call logic function for background story generation
            generated_background_story = generate_background_story(title, genre, initial_story_outline,
                                                                   character_profiles, max_words_background_story)
            # Updating context with the form data and generated story
            context['form_data'].update({
                'title': title,
                'genre': genre,
                'initial_story_outline': initial_story_outline,
                'character_profiles': character_profiles,
                'max_words_background_story': max_words_background_story
            })
            context['generated_background_story'] = generated_background_story

        elif action == 'refine':
            # Extracting data for story refinement
            background_story = request.POST.get('edited_story', '')
            narrative_engineer_feedback = request.POST.get('narrative_engineer_feedback', '')

            refined_background_story = refine_background_story(background_story, narrative_engineer_feedback)
            context['refined_background_story'] = refined_background_story

    return render(request, 'AIFictioneer/ideation.html', context)


# API version
class GenerateBackgroundStoryAPIView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = BackgroundStoryGenerationSerializer(data=request.data)
        if serializer.is_valid():
            # Extract validated data from the serializer
            title = serializer.validated_data['title']
            genre = serializer.validated_data['genre']
            initial_story_outline = serializer.validated_data['initial_story_outline']
            character_profiles = serializer.validated_data['character_profiles']
            max_words_background_story = serializer.validated_data.get('max_words_background_story',
                                                                       300)  # Default to 300 if not provided

            # Call the story generation function with the validated data
            generated_background_story = generate_background_story(
                title=title,
                genre=genre,
                initial_story_outline=initial_story_outline,
                character_profiles=character_profiles,
                max_words_background_story=max_words_background_story  # Pass the max words parameter
            )

            # Return the generated story in the response
            return Response({"generated_background_story": generated_background_story})
        else:
            # If the data is not valid, return the errors
            return Response(serializer.errors, status=400)


# Function for API
class RefineBackgroundStoryAPIView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = BackgroundStoryRefinementSerializer(data=request.data)
        if serializer.is_valid():
            background_story = serializer.validated_data['background_story']
            narrative_engineer_feedback = serializer.validated_data['narrative_engineer_feedback']

            refined_background_story = refine_background_story(background_story, narrative_engineer_feedback)

            return Response({"refined_background_story": refined_background_story})
        else:
            return Response(serializer.errors, status=400)

            
################################################################################################# Meaning Making #####################################################################################
@login_required
def meaning_making(request):
    # initialize the context with default values
    initial_context = {
        'current_background_story': '',
        'narrative_engineer_input': '',
        'number_of_events': '',
        'number_of_endings': '',
        'number_of_characters': '',
        'number_of_locations': '',
        'number_of_interactive_objects': '',
        'generated_narrative': '',
        'narrative_engineer_feedback': '',
        'suggestions': []
    }

    context = initial_context.copy()

    if request.method == 'POST':
        # Retrieve data from the POST request
        edited_story = request.POST.get('edited_story', '')
        background_story_content = request.POST.get('background_story_content', '')

        # determine the source of the request & update the context accordingly
        context['generated_ideas'] = edited_story if 'edited_story' in request.POST else background_story_content

        # Update context with the values from the POST request
        context.update({
            'current_background_story': background_story_content,
            'narrative_engineer_input': request.POST.get('narrative_engineer_input', ''),
            'number_of_events': request.POST.get('number_of_events', ''),
            'number_of_endings': request.POST.get('number_of_endings', ''),
            'number_of_characters': request.POST.get('number_of_characters', ''),
            'number_of_locations': request.POST.get('number_of_locations', ''),
            'number_of_interactive_objects': request.POST.get('number_of_interactive_objects', ''),
            'generated_narrative': request.POST.get('generated_narrative', ''),
            'narrative_engineer_feedback': request.POST.get('narrative_engineer_feedback', '')
        })

        action = request.POST.get('action', '')
        if action == 'generate':
            generated_protostory = generate_protostory(
                background_story=context['current_background_story'],
                narrative_engineer_input=context['narrative_engineer_input'],
                events=context['number_of_events'],
                endings=context['number_of_endings'],
                characters=context['number_of_characters'],
                locations=context['number_of_locations'],
                interactive_objects=context['number_of_interactive_objects']
            )
            context['generated_narrative'] = generated_protostory

        elif action == 'refine':
            protostory = context['generated_narrative']
            narrative_engineer_feedback = context['narrative_engineer_feedback']
            updated_narrative = refine_protostory(protostory, narrative_engineer_feedback)
            context['generated_narrative'] = updated_narrative

        elif action == 'analyze_coherence':
            protostory = context['generated_narrative']
            suggestions = analyze_narrative_coherence(protostory)
            context['suggestions'] = suggestions if isinstance(suggestions, list) else []

        elif action.startswith('apply_suggestion_'):
            index = action.split('_')[-1]
            edited_suggestion = request.POST.get(f'edited_suggestion_{index}', '')
            if edited_suggestion:
                protostory = context['generated_narrative']
                apply_individual_suggestion(protostory, edited_suggestion, context)

        elif action == 'apply_all_selected':
            protostory = context['generated_narrative']
            for key in request.POST.keys():
                if key.startswith('suggestion_') and request.POST.get(key) == 'on':
                    index = key.split('_')[-1]
                    edited_suggestion = request.POST.get(f'edited_suggestion_{index}', '')
                    if edited_suggestion:
                        apply_individual_suggestion(protostory, edited_suggestion, context)

    return render(request, 'AIFictioneer/meaning_making.html', context)

def generate_protostory(background_story, narrative_engineer_input, events, endings, characters, locations,
                             interactive_objects, protostory_template=None):
    try:
        protostory_generation_prompt_obj = Prompt.objects.get(name='PROTOSTORY_GENERATION_PROMPT')
        protostory_generation_prompt_content = protostory_generation_prompt_obj.content

        if protostory_template is None:
            protostory_template = protostory_generation_prompt_obj.ontology.protostory_template
    except Prompt.DoesNotExist:
        return "Error: PROTOSTORY_GENERATION_PROMPT not found in the database."

    formatted_prompt = f"""
    {protostory_generation_prompt_content.format(
        background_story_content=background_story,
        narrative_engineer_input=narrative_engineer_input,
        number_of_events=events,
        number_of_endings=endings,
        number_of_characters=characters,
        number_of_locations=locations,
        number_of_interactive_objects=interactive_objects,
        protostory_template=protostory_template or ''
    )}
    """
    generated_narrative = call_gpt4_api(formatted_prompt)
    cleaned_narrative = generated_narrative.replace("```json", "").replace("```", "")
    return cleaned_narrative

# Logic function interactive narrative refinement
def refine_protostory(protostory, narrative_engineer_feedback):
    try:
        protostory_refinement_prompt_obj = Prompt.objects.get(name='PROTOSTORY_REFINEMENT_PROMPT')
        protostory_refinement_content = protostory_refinement_prompt_obj.content
    except Prompt.DoesNotExist:
        return "Error: PROTOSTORY_REFINEMENT_PROMPT not found in the database."

    # Prepare the formatted prompt
    formatted_prompt = protostory_refinement_content.format(
        protostory=protostory,
        narrative_engineer_feedback=narrative_engineer_feedback
    )

    # Call the GPT-4 API or internal logic to apply feedback
    updated_narrative = call_gpt4_api(formatted_prompt)
    print(updated_narrative)
    cleaned_narrative = updated_narrative.replace("```json", "").replace("```", "")
    return cleaned_narrative

def analyze_narrative_coherence(protostory, coherence_analysis_output_structure=None):
    try:
        coherence_analysis_prompt = Prompt.objects.get(name='PROTOSTORY_COHERENCE_ANALYSIS_PROMPT')
        
        # Only get the default coherence_analysis_output_structure if it's not provided
        if coherence_analysis_output_structure is None:
            coherence_analysis_output_structure = coherence_analysis_prompt.ontology.coherence_analysis_output_structure

        # Prepare the formatted prompt using f-strings for the specific parts
        formatted_prompt = coherence_analysis_prompt.content.format(
            protostory=protostory,
            coherence_analysis_output_structure=f"{coherence_analysis_output_structure}"
        )

        analysis_result = call_gpt4_api(formatted_prompt)
        print(analysis_result)  #debug

        json_start_index = analysis_result.find('{')
        json_end_index = analysis_result.rfind('}') + 1
        
        if json_start_index != -1 and json_end_index != -1:
            json_str = analysis_result[json_start_index:json_end_index]
            coherence_feedback = json.loads(json_str)
            return coherence_feedback.get("Issues", [])
        else:
            return "Error: Valid JSON response not found."
    except Prompt.DoesNotExist:
        return "Error: PROTOSTORY_COHERENCE_ANALYSIS_PROMPT not found in the database."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def apply_individual_suggestion(protostory, edited_suggestion, context):
    # refine the narrative with the selected suggestion
    updated_narrative = refine_protostory(protostory, edited_suggestion)
    
    # Clean the generated narrative to remove code block markers if present
    cleaned_narrative = updated_narrative.replace("```json", "").replace("```", "")
    
    # Store the cleaned narrative in the context
    context['generated_narrative'] = cleaned_narrative

    # Check if there is an error message in the cleaned narrative and store it in the context
    if isinstance(cleaned_narrative, str) and "Error:" in cleaned_narrative:
        context['error'] = cleaned_narrative

def apply_all_selected_suggestions(request, protostory, context):
    selected_suggestions = []
    for key, value in request.POST.items():
        if key.startswith('suggestion_') and value == 'on':
            index = key.split('_')[-1]
            edited_suggestion = request.POST.get(f'edited_suggestion_{index}', '')
            if edited_suggestion:
                selected_suggestions.append(edited_suggestion)
    
    concatenated_suggestions = '\n'.join(selected_suggestions)
    if concatenated_suggestions:
        apply_individual_suggestion(protostory, concatenated_suggestions, context)
    else:
        context['error'] = "Error: No suggestions were selected to apply."     
        
        
        
        
        
        
        
        
# API Handeling
class GenerateProtoStoryAPIView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer = ProtoStoryGenerationSerializer(data=request.data)
        if serializer.is_valid():
            # Check if 'protostory_template is provided in the request, use None as default
            protostory_template = serializer.validated_data.get('protostory_template', None)

            narrative_json = generate_protostory(
                background_story=serializer.validated_data['background_story'],
                narrative_engineer_input=serializer.validated_data.get('narrative_engineer_input', ''),
                events=serializer.validated_data.get('number_of_events', ''),
                endings=serializer.validated_data.get('number_of_endings', ''),
                characters=serializer.validated_data.get('number_of_characters', ''),
                locations=serializer.validated_data.get('number_of_locations', ''),
                interactive_objects=serializer.validated_data.get('number_of_interactive_objects', '')
            )

            # If narrative_json is already a dictionary, no need to parse it
            if isinstance(narrative_json, dict):
                return Response(narrative_json)
            else:
                try:
                    # parse it if it's a string
                    narrative_json = json.loads(narrative_json)
                    return Response(narrative_json)
                except json.JSONDecodeError:
                    # Handle the case where the string cannot be parsed to JSON
                    return Response({"error": "Failed to parse the generated narrative into JSON."}, status=400)
        else:
            return Response(serializer.errors, status=400)


class RefineProtoStoryAPIView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer = ProtoStoryRefinementSerializer(data=request.data)
        if serializer.is_valid():
            updated_narrative_string = refine_protostory(
                protostory=serializer.validated_data['protostory'],
                narrative_engineer_feedback=serializer.validated_data['narrative_engineer_feedback']
            )
            cleaned_protostory = updated_narrative_string.replace("```json", "").replace("```", "")
            print(updated_narrative_string)  # debug
            try:
                # Parse the string back to a JSON object
                updated_narrative_json = json.loads(cleaned_protostory)
                return Response(updated_narrative_json)
            except json.JSONDecodeError:
                # Handle the case where the string cannot be parsed to JSON
                return Response({"error": "Failed to parse the updated interactive narrative into JSON."}, status=400)

        else:
            return Response(serializer.errors, status=400)


class AnalyzeNarrativeCoherenceAPIView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        data = request.data
        coherence_analysis_output_structure = data.get('coherence_analysis_output_structure', None)

        # Assuming the entire request body is the protostory but it also accept other strcutures such as knowledge graph
        protostory = data

        suggestions = analyze_narrative_coherence(
            protostory,
            coherence_analysis_output_structure=coherence_analysis_output_structure
        )

        if isinstance(suggestions, list):
            return Response({'suggestions': suggestions})
        else:
            return Response({'error': suggestions}, status=400)

########################################################################### Interaction ###########################################################################


api_key = config('OPENAI_API_KEY')
client = openai.OpenAI(api_key=api_key)

assistant_id = config('ASSISTANT_ID') 

# function to add a message to a thread
def add_message_to_thread(thread_id, role, content):
    # Adds a message to the existing thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=content
    )

# function to run the thread
def run_thread(thread_id):
    # Run the thread with the predefined assistant using the polling helper (https://github.com/openai/openai-python/blob/main/helpers.md)
    try:
        run_result = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
            poll_interval_ms=5000  # Check every 5 seconds
        )
        return run_result
    except Exception as e:
        return {"error": str(e)}

#function to retrieve the latest message
def retrieve_latest_message(thread_id):
    try:
        messages_response = client.beta.threads.messages.list(thread_id=thread_id, limit=30, order="asc")
        last_assistant_message = None
        for message in messages_response:
            if message.role == 'assistant':
                last_assistant_message = message
        if last_assistant_message:
            return last_assistant_message.content[0].text.value
    except Exception as e:
        return "No messages found or error: " + str(e)

@login_required
def interaction(request):
    context = {}
    if request.method == 'POST':
        protostory = ''   

        # Capturing narrative content based on the form field used
        if 'narrative_content' in request.POST:
            protostory = request.POST.get('narrative_content', '')
        elif 'interactive_narrative_content' in request.POST:
            protostory = request.POST.get('interactive_narrative_content', '')

        context['generated_narrative'] = protostory
        
        if request.POST.get('action') == 'start_interaction':
            narrative_content = request.POST.get('narrative_content')
            # Create a new thread
            thread = client.beta.threads.create()
            thread_id = thread.id
#            print(thread)
#            print(thread_id)
            #Create prompt            
            try:
                interaction_engine_prompt_obj = Prompt.objects.get(name='INTERACTION_ENGINE_PROMPT')
                interaction_engine_prompt_content = interaction_engine_prompt_obj.content
            except Prompt.DoesNotExist:
                return "Error: PROMPT not found in the database."            
            
            formatted_prompt = f""" {interaction_engine_prompt_content.format(narrative_content=narrative_content)}"""
#            print(formatted_prompt)

            # sending the initial content as the first message
            add_message_to_thread(thread_id, "user", formatted_prompt)

            # Run the thread to get a response
            run_result = run_thread(thread_id)
            latest_message = retrieve_latest_message(thread_id)


            return JsonResponse({'message': latest_message, 'thread_id': thread_id})

        elif request.POST.get('action') == 'send_message':
            user_input = request.POST.get('message')
            thread_id = request.POST.get('thread_id')

            # add user input to the existng thread
            add_message_to_thread(thread_id, "user", user_input)

            # run the thread again to get a response
            run_thread(thread_id)
            latest_message = retrieve_latest_message(thread_id)

            return JsonResponse({'message': latest_message})

    return render(request, 'AIFictioneer/interaction.html', context)


########################################################################### API CONFIGURATIONS ######################################################################

class APIRootView(APIView):

    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    """
    lists all available API endpoints.
    """
    def get(self, request, format=None):
        return Response({
            'generate-background-story': reverse('generate_background_story_api', request=request, format=format),
            'refine-background-story': reverse('refine_background_story_api', request=request, format=format),
            'generate-protostory': reverse('generate_protostory_api', request=request, format=format),
            'refine-protostory': reverse('refine_protostory_api', request=request, format=format),
            'analyze-protostory-coherence': reverse('analyze-protostory-coherence_api', request=request, format=format),

        })
