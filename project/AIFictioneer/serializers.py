from rest_framework import serializers

class BackgroundStoryGenerationSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)
    genre = serializers.CharField(max_length=50)
    initial_story_outline = serializers.CharField()
    max_words_background_story = serializers.IntegerField(required=False) 
    character_profiles = serializers.ListField(
        child=serializers.DictField(), required=False, default=[]
    )


class BackgroundStoryRefinementSerializer(serializers.Serializer):
    background_story = serializers.CharField(required=True, allow_blank=False)
    narrative_engineer_feedback = serializers.CharField(required=True, allow_blank=False)    
    

class ProtoStoryGenerationSerializer(serializers.Serializer):
    background_story = serializers.CharField(required=True)
    protostory_template = serializers.JSONField(required=False)    
    narrative_engineer_input = serializers.CharField(required=False,allow_blank=True)
    number_of_events = serializers.CharField(required=False, allow_blank=True)
    number_of_endings = serializers.CharField(required=False, allow_blank=True)
    number_of_characters = serializers.CharField(required=False, allow_blank=True)
    number_of_locations = serializers.CharField(required=False, allow_blank=True)
    number_of_interactive_objects = serializers.CharField(required=False, allow_blank=True)



class ProtoStoryRefinementSerializer(serializers.Serializer):
    protostory = serializers.JSONField(required=True)  # Accept any JSON structure
    narrative_engineer_feedback = serializers.CharField(required=True)

        
class ProtoStoryCoherenceAnalysisSerializer(serializers.Serializer):
    coherence_analysis_output_structure = serializers.JSONField(required=False, allow_null=True)

     