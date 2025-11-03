# inventory/forms.py
from django import forms
from .models import MenuItem, FoodCategory

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            'name', 'description', 'category', 'item_type', 'pricing_type', 
            'price', 'cost_price', 'image', 'preparation_time', 'is_available',
            'base_item', 'protein_source', 'compatible_sources'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preparation_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'item_type': forms.Select(attrs={'class': 'form-control'}),
            'pricing_type': forms.Select(attrs={'class': 'form-control'}),
            'base_item': forms.Select(attrs={'class': 'form-control'}),
            'protein_source': forms.Select(attrs={'class': 'form-control'}),
            'compatible_sources': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter choices for related fields
        self.fields['base_item'].queryset = MenuItem.objects.filter(item_type='base')
        self.fields['protein_source'].queryset = MenuItem.objects.filter(item_type='source')
        self.fields['compatible_sources'].queryset = MenuItem.objects.filter(item_type='source')
        
        # Make fields not required initially
        self.fields['price'].required = False
        self.fields['base_item'].required = False
        self.fields['protein_source'].required = False
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                if field_name != 'is_available':
                    field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'