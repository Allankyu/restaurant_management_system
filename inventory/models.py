from django.db import models
from django.core.validators import MinValueValidator
import os
import uuid

class FoodCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class FoodSource(models.Model):
    """Food sources like Fish, Beef, Chicken (with prices)"""
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - Ugx{self.price}"

def menu_item_image_path(instance, filename):
    """Generate file path for menu item images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('menu_items/', filename)

class MenuItem(models.Model):
    PRICING_TYPES = [
        ('direct', 'Direct Price'),
        ('base', 'Base Item (Requires Source)'),
        ('source', 'Protein Source'),
        ('combo', 'Pre-defined Combo'),
    ]
    
    ITEM_TYPES = [
        ('base', 'Base Food'),
        ('source', 'Protein Source'), 
        ('combo', 'Complete Meal'),
        ('beverage', 'Beverage'),
        ('side', 'Side Dish'),
    ]
    
    BASE_CATEGORIES = [
        ('free', 'Free Base Food'),
        ('premium', 'Premium Base Food'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey('FoodCategory', on_delete=models.CASCADE)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPES, default='combo')
    
    # NEW FIELD: Distinguish between free and premium base foods
    base_category = models.CharField(
        max_length=10, 
        choices=BASE_CATEGORIES, 
        blank=True, 
        null=True,
        help_text="Only for base items - indicates if base is free or premium"
    )
    
    # Pricing system
    pricing_type = models.CharField(
        max_length=10, 
        choices=PRICING_TYPES, 
        default='direct'
    )
    
    # Price for direct pricing or combo pricing
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        null=True, 
        blank=True
    )
    
    # For base items - what sources they can be combined with
    compatible_sources = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False
    )
    
    # For combo items - fixed combinations
    base_item = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combo_as_base'
    )
    protein_source = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combo_as_source'
    )
    
    # Existing fields
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    
    # Image field
    image = models.ImageField(
        upload_to=menu_item_image_path,
        null=True, 
        blank=True,
        help_text="Upload image for this menu item"
    )
    
    is_available = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(help_text="Preparation time in minutes")
    branches = models.ManyToManyField('core.Branch', through='BranchMenuItem')  # Use string reference
    
    class Meta:
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Automatically set base_category for base items based on price"""
        if self.item_type == 'base':
            if self.price == 0 or self.price is None:
                self.base_category = 'free'
            else:
                self.base_category = 'premium'
        else:
            self.base_category = None
            
        super().save(*args, **kwargs)
    
    @property
    def actual_price(self):
        """Get the actual price based on pricing type and item type"""
        if self.item_type == 'combo' and self.base_item and self.protein_source:
            # Combo price = base price + source price
            base_price = self.base_item.actual_price or 0
            source_price = self.protein_source.actual_price or 0
            return base_price + source_price
        elif self.pricing_type == 'direct':
            return self.price or 0
        elif self.item_type == 'base':
            return self.price or 0
        elif self.item_type == 'source':
            return self.price or 0
        return self.price or 0
    
    @property
    def display_name(self):
        """Display name for orders"""
        if self.item_type == 'combo' and self.base_item and self.protein_source:
            return f"{self.base_item.name} with {self.protein_source.name}"
        return self.name
    
    @property
    def has_image(self):
        """Check if menu item has an image"""
        return bool(self.image)
    
    @property
    def is_customizable_component(self):
        """Check if this item is a base or source (used in custom combos)"""
        return self.item_type in ['base', 'source']
    
    @property
    def is_predefined_meal(self):
        """Check if this is a predefined meal that should show image"""
        return self.item_type in ['combo', 'beverage', 'side']
    
    @property
    def is_free_base(self):
        """Check if this is a free base food"""
        return self.item_type == 'base' and self.base_category == 'free'
    
    @property
    def is_premium_base(self):
        """Check if this is a premium base food"""
        return self.item_type == 'base' and self.base_category == 'premium'

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name

class Recipe(models.Model):
    menu_item = models.ForeignKey('MenuItem', on_delete=models.CASCADE)  # Use string reference
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)  # Use string reference
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.ingredient.name}"

class Stock(models.Model):
    branch = models.ForeignKey(
        'core.Branch',  # Use string reference
        on_delete=models.CASCADE, 
        related_name='stocks',
        null=True,
        blank=True
    )
    ingredient = models.ForeignKey(
        'Ingredient',  # Use string reference
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    alert_level = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    def __str__(self):
        branch_name = self.branch.name if self.branch else "No Branch"
        return f"{self.ingredient.name} - {self.quantity} {self.ingredient.unit} ({branch_name})"
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.alert_level
    
    class Meta:
        unique_together = ['branch', 'ingredient']
        verbose_name_plural = "Stocks"
    
    @classmethod
    def get_low_stock_items(cls):
        return cls.objects.filter(quantity__lte=models.F('alert_level'))

class Utensil(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    condition = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('needs_repair', 'Needs Repair'),
        ('broken', 'Broken')
    ])
    last_maintenance = models.DateField(null=True, blank=True)
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, null=True, blank=True)  # Use string reference
    
    def __str__(self):
        return self.name

class BranchMenuItem(models.Model):
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE)  # Use string reference
    menu_item = models.ForeignKey('MenuItem', on_delete=models.CASCADE)  # Use string reference
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['branch', 'menu_item']
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.branch.name}"
    
    @property
    def actual_price(self):
        return self.price