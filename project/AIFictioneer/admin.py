from django.contrib import admin
from .models import Prompt, Ontology

class OntologyAdmin(admin.ModelAdmin):
    list_display = ('name', 'protostory_template')   

class PromptAdmin(admin.ModelAdmin):
    list_display = ('name', 'content', 'display_ontology')  
    search_fields = ('name', 'ontology__name')  
    list_filter = ('ontology__name',)  

    def display_ontology(self, obj):
        return obj.ontology.name
    display_ontology.short_description = 'Ontology'

admin.site.register(Prompt, PromptAdmin)
admin.site.register(Ontology, OntologyAdmin)

