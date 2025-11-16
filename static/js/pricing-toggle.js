document.addEventListener('DOMContentLoaded', function() {
    function togglePricingFields() {
        var pricingType = document.getElementById('id_pricing_type');
        var priceField = document.querySelector('.field-price');
        var sourceField = document.querySelector('.field-food_source');
        
        if (!pricingType || !priceField || !sourceField) {
            // Try again in case fields load slowly
            setTimeout(togglePricingFields, 100);
            return;
        }
        
        var selectedType = pricingType.value;
        
        // Hide all fields first
        priceField.style.display = 'none';
        sourceField.style.display = 'none';
        
        // Show relevant field based on pricing type
        if (selectedType === 'direct') {
            priceField.style.display = 'block';
            // Make price required
            var priceInput = document.getElementById('id_price');
            if (priceInput) {
                priceInput.required = true;
            }
        } else if (selectedType === 'source') {
            sourceField.style.display = 'block';
            // Make food_source required
            var sourceInput = document.getElementById('id_food_source');
            if (sourceInput) {
                sourceInput.required = true;
            }
        }
        // For 'free' type, both fields remain hidden
    }
    
    // Initial setup
    togglePricingFields();
    
    // Add event listener for pricing type changes
    var pricingTypeSelect = document.getElementById('id_pricing_type');
    if (pricingTypeSelect) {
        pricingTypeSelect.addEventListener('change', togglePricingFields);
    }
    
    // Handle dynamic form loading
    var observer = new MutationObserver(function(mutations) {
        for (var i = 0; i < mutations.length; i++) {
            if (mutations[i].type === 'childList') {
                togglePricingFields();
                break;
            }
        }
    });
    
    var formContainer = document.querySelector('form');
    if (formContainer) {
        observer.observe(formContainer, { childList: true, subtree: true });
    }
});



