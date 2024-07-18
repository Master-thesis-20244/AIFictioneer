from django.db import models

# Create your models here.from django.db import models

from django.db import models


class Ontology(models.Model):
    name = models.CharField(max_length=255)
    ttl_definition = models.TextField(blank=True, null=True)
    protostory_template = models.TextField(blank=True, null=True) 
    coherence_analysis_output_structure = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Ontologies"
        
        

class Prompt(models.Model):
    name = models.TextField()
    content = models.TextField()
    ontology = models.ForeignKey(Ontology, on_delete=models.SET_NULL, null=True, blank=True, related_name="prompts")

    def __str__(self):
        return self.name
        
        
        
