from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import FoodCategory, MenuItem, Ingredient, Recipe, Stock, Utensil, FoodSource, BranchMenuItem
from import_export.admin import ImportExportModelAdmin

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields optional initially
        self.fields['price'].required = False
        
        # Set field help texts
        self.fields['item_type'].help_text = """
        <strong>Item Types:</strong><br>
        • <strong>Base Food</strong>: Basic food items (rice, ugali, matooke)<br>
        • <strong>Protein Source</strong>: Meat/fish items (beef, chicken, fish)<br>
        • <strong>Complete Meal</strong>: Pre-defined combos (rice with fish)<br>
        • <strong>Beverage</strong>: Drinks (soda, juice)<br>
        • <strong>Side Dish</strong>: Side items (salad, fries)
        """
        
        self.fields['pricing_type'].help_text = """
        <strong>Pricing Options:</strong><br>
        • <strong>Direct Price</strong>: Enter price manually<br>
        • <strong>Base Item</strong>: Base food that requires protein source<br>
        • <strong>Protein Source</strong>: Protein item with its own price<br>
        • <strong>Pre-defined Combo</strong>: Fixed combination with auto-calculated price
        """
        
        # Limit choices for related fields - FIXED: Check if queryset exists
        try:
            if 'base_item' in self.fields:
                self.fields['base_item'].queryset = MenuItem.objects.filter(item_type='base')
                self.fields['base_item'].required = False
                
            if 'protein_source' in self.fields:
                self.fields['protein_source'].queryset = MenuItem.objects.filter(item_type='source')
                self.fields['protein_source'].required = False
                
            if 'compatible_sources' in self.fields:
                self.fields['compatible_sources'].queryset = MenuItem.objects.filter(item_type='source')
        except Exception:
            # If there's any error with the queryset, just skip it
            pass
    
    def clean(self):
        cleaned_data = super().clean()
        pricing_type = cleaned_data.get('pricing_type')
        item_type = cleaned_data.get('item_type')
        
        # Validation for direct pricing
        if pricing_type == 'direct' and not cleaned_data.get('price'):
            raise forms.ValidationError({
                'price': 'Price is required when using Direct Price pricing type.'
            })
        
        # Validation for combo items
        if item_type == 'combo':
            if not cleaned_data.get('base_item'):
                raise forms.ValidationError({
                    'base_item': 'Base item is required for combo meals.'
                })
            if not cleaned_data.get('protein_source'):
                raise forms.ValidationError({
                    'protein_source': 'Protein source is required for combo meals.'
                })
        
        return cleaned_data

@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

class BranchMenuItemInline(admin.TabularInline):
    model = BranchMenuItem
    extra = 1

@admin.register(MenuItem)
class MenuItemAdmin(ImportExportModelAdmin):
    form = MenuItemForm
    list_display = [
        'name', 
        'category', 
        'item_type', 
        'pricing_type', 
        'actual_price', 
        'cost_price', 
        'is_available',
        'image_preview'  # ADDED: Image preview in list view
    ]
    list_filter = ['category', 'item_type', 'pricing_type', 'is_available']
    search_fields = ['name', 'description']
    readonly_fields = ['actual_price_display', 'image_preview']  # ADDED: image_preview
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'image', 'image_preview', 'is_available')  # ADDED: image_preview
        }),
        ('Item Type & Pricing', {
            'fields': ('item_type', 'pricing_type', 'price', 'cost_price', 'actual_price_display'),
            'description': 'Configure the item type and pricing method'
        }),
        ('Combo Configuration', {
            'fields': ('base_item', 'protein_source', 'compatible_sources'),
            'classes': ('collapse',),
            'description': 'Only for combo items and base foods'
        }),
        ('Preparation', {
            'fields': ('preparation_time',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [BranchMenuItemInline]
    
    def actual_price_display(self, obj):
        """Display the actual calculated price"""
        if obj.pk:
            return f"Ugx {obj.actual_price}"
        return "Save to see calculated price"
    actual_price_display.short_description = 'Calculated Price'
    
    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', 
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Image Preview'
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        # Remove combo configuration for non-combo and non-base items
        if obj and obj.item_type not in ['combo', 'base']:
            fieldsets = [fs for fs in fieldsets if fs[0] != 'Combo Configuration']
        
        return fieldsets

@admin.register(FoodSource)
class FoodSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_available']
    list_filter = ['is_available']
    search_fields = ['name']

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['ingredient', 'branch', 'quantity', 'alert_level', 'is_low_stock']
    list_filter = ['branch', 'ingredient']
    search_fields = ['ingredient__name']

@admin.register(BranchMenuItem)
class BranchMenuItemAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'branch', 'price', 'is_available']
    list_filter = ['branch', 'is_available']
    search_fields = ['menu_item__name']

# Register other models
admin.site.register([Ingredient, Recipe, Utensil])



