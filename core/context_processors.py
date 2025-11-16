from .models import Restaurant

def restaurant_info(request):
    """
    Context processor to make restaurant information available in all templates
    """
    try:
        restaurant = Restaurant.objects.first()
    except:
        restaurant = None
    
    return {
        'restaurant': restaurant
    }



