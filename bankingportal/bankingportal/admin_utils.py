from django.contrib import admin
from django.apps import apps
from django.db import models
from import_export.admin import ImportExportModelAdmin
from import_export import resources

def register_app_models(app_label):
    """
    Dynamically registers all models for a given app label with Import/Export support.
    sets list_display for all fields and smart list_filter for relations/choices.
    """
    app_config = apps.get_app_config(app_label)
    for model_name, model in app_config.models.items():
        if admin.site.is_registered(model):
            continue

        # Get all non-many-to-many fields
        fields = [field.name for field in model._meta.fields]
        
        # Select fields for list_filter (Relations, Booleans, Choices)
        filter_fields = []
        for field in model._meta.fields:
            if field.is_relation or isinstance(field, models.BooleanField) or getattr(field, 'choices', None):
                if not field.primary_key:
                    filter_fields.append(field.name)

        # Dynamic Resource Class for Import/Export
        resource_class = type(
            f"{model_name.capitalize()}Resource",
            (resources.ModelResource,),
            {'Meta': type('Meta', (), {'model': model})}
        )

        # Dynamic Admin Class
        admin_class = type(
            f"{model_name.capitalize()}Admin",
            (ImportExportModelAdmin,),
            {
                'resource_class': resource_class,
                'list_display': fields,
                'list_filter': filter_fields,
                'search_fields': [f.name for f in model._meta.fields if isinstance(f, (models.CharField, models.TextField))]
            }
        )

        admin.site.register(model, admin_class)