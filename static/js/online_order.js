// static/js/online_order.js
document.addEventListener('DOMContentLoaded', function() {
    // Order items management
    let orderItems = {};
    let itemCounter = 0;
    
    const orderItemsList = document.getElementById('onlineOrderItemsList');
    const subtotalElement = document.getElementById('onlineSubtotal');
    const totalElement = document.getElementById('onlineTotal');
    const totalAmountInput = document.getElementById('onlineTotalAmount');
    const submitBtn = document.getElementById('submitOnlineOrderBtn');

    // Custom combo elements
    const customBaseSelect = document.getElementById('customBaseSelect');
    const customSourceSelect = document.getElementById('customSourceSelect');
    const customQuantity = document.getElementById('customQuantity');
    const addCustomComboBtn = document.getElementById('addCustomCombo');
    const addProteinOnlyBtn = document.getElementById('addProteinOnly');
    const customComboPreview = document.getElementById('customComboPreview');
    const comboPreviewText = document.getElementById('comboPreviewText');
    const comboPreviewPrice = document.getElementById('comboPreviewPrice');
    const proteinOnlyPreview = document.getElementById('proteinOnlyPreview');
    const proteinPreviewText = document.getElementById('proteinPreviewText');
    const proteinPreviewPrice = document.getElementById('proteinPreviewPrice');
    const customComboInputs = document.getElementById('customComboInputs');

    // Initialize quantity buttons
    function initializeQuantityButtons() {
        // Quantity button handlers for plus buttons
        document.querySelectorAll('.plus-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const itemId = this.getAttribute('data-item');
                const input = document.getElementById('qty_' + itemId);
                if (!input) return;
                
                const currentValue = parseInt(input.value) || 0;
                const newValue = currentValue + 1;
                input.value = newValue;
                
                updateMenuItemQuantity(itemId, newValue);
            });
        });

        // Quantity button handlers for minus buttons
        document.querySelectorAll('.minus-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const itemId = this.getAttribute('data-item');
                const input = document.getElementById('qty_' + itemId);
                if (!input) return;
                
                const currentValue = parseInt(input.value) || 0;
                if (currentValue > 0) {
                    const newValue = currentValue - 1;
                    input.value = newValue;
                    updateMenuItemQuantity(itemId, newValue);
                }
            });
        });
    }

    // Initialize custom combo functionality
    function initializeCustomCombos() {
        if (addCustomComboBtn) {
            addCustomComboBtn.addEventListener('click', addCustomCombo);
        }
        
        if (addProteinOnlyBtn) {
            addProteinOnlyBtn.addEventListener('click', addProteinOnly);
        }
        
        // Update preview when selections change
        if (customBaseSelect) {
            customBaseSelect.addEventListener('change', updateComboPreview);
        }
        if (customSourceSelect) {
            customSourceSelect.addEventListener('change', updateComboPreview);
        }
        if (customQuantity) {
            customQuantity.addEventListener('input', updateComboPreview);
        }
    }

    function updateComboPreview() {
        if (!customBaseSelect || !customSourceSelect || !customQuantity) return;
        
        const baseOptions = Array.from(customBaseSelect.selectedOptions);
        const sourceId = customSourceSelect.value;
        const quantity = parseInt(customQuantity.value) || 1;

        // Hide both previews initially
        if (customComboPreview) customComboPreview.style.display = 'none';
        if (proteinOnlyPreview) proteinOnlyPreview.style.display = 'none';

        if (baseOptions.length > 0 && sourceId) {
            // Show combo preview - include ALL base foods (free and priced)
            const baseNames = [];
            let totalPrice = 0;
            
            baseOptions.forEach(function(option) {
                const baseName = option.text.split(' (+Ugx')[0].trim();
                const basePrice = parseFloat(option.dataset.price) || 0;
                const baseType = option.dataset.type;
                
                if (baseType === 'priced') {
                    baseNames.push(baseName + ' (+Ugx ' + basePrice + ')');
                    totalPrice += basePrice;
                } else {
                    baseNames.push(baseName);
                }
            });

            const sourceOption = customSourceSelect.options[customSourceSelect.selectedIndex];
            const sourceName = sourceOption.text.split(' - Ugx')[0].trim();
            const sourcePrice = parseFloat(sourceOption.dataset.price) || 0;
            
            totalPrice += sourcePrice;

            // Format price display - leave blank for free items
            let priceDisplay = '';
            if (totalPrice > 0) {
                priceDisplay = 'Ugx ' + (totalPrice * quantity).toFixed(2);
            }

            if (comboPreviewText) comboPreviewText.textContent = baseNames.join(' + ') + ' with ' + sourceName + ' × ' + quantity;
            if (comboPreviewPrice) comboPreviewPrice.textContent = priceDisplay;
            if (customComboPreview) customComboPreview.style.display = 'block';

        } else if (!baseOptions.length && sourceId) {
            // Show protein only preview
            const sourceOption = customSourceSelect.options[customSourceSelect.selectedIndex];
            const sourceName = sourceOption.text.split(' - Ugx')[0].trim();
            const sourcePrice = parseFloat(sourceOption.dataset.price) || 0;
            const totalPrice = sourcePrice * quantity;

            // Format price display - leave blank for free items
            let priceDisplay = '';
            if (totalPrice > 0) {
                priceDisplay = 'Ugx ' + totalPrice.toFixed(2);
            }

            if (proteinPreviewText) proteinPreviewText.textContent = sourceName + ' × ' + quantity;
            if (proteinPreviewPrice) proteinPreviewPrice.textContent = priceDisplay;
            if (proteinOnlyPreview) proteinOnlyPreview.style.display = 'block';
        }
        // Removed base-only preview since base foods alone are not allowed
    }

    function addCustomCombo() {
        if (!customBaseSelect || !customSourceSelect || !customQuantity) return;
        
        const baseOptions = Array.from(customBaseSelect.selectedOptions);
        const sourceId = customSourceSelect.value;
        const quantity = parseInt(customQuantity.value) || 1;

        // Validate: Base foods must be paired with protein source
        if (baseOptions.length > 0 && !sourceId) {
            alert('Please select a protein source to go with your base food(s). Base foods cannot be ordered alone.');
            return;
        }

        // Validate: Must have either base+protein or protein only
        if (baseOptions.length === 0 && !sourceId) {
            alert('Please select at least one base food with a protein source, or a protein source alone.');
            return;
        }

        // Allow base foods with protein OR protein only
        if (baseOptions.length > 0 && sourceId) {
            addCustomComboWithProtein(baseOptions, sourceId, quantity);
        } else if (!baseOptions.length && sourceId) {
            addProteinOnly();
        }

        // Reset form
        customBaseSelect.selectedIndex = -1;
        customSourceSelect.selectedIndex = 0;
        customQuantity.value = 1;
        if (customComboPreview) customComboPreview.style.display = 'none';
        if (proteinOnlyPreview) proteinOnlyPreview.style.display = 'none';

        updateOrderTotal();
    }

    function addCustomComboWithProtein(baseOptions, sourceId, quantity) {
        const sourceOption = customSourceSelect.options[customSourceSelect.selectedIndex];
        
        // Calculate total price - include ALL base options (free and priced)
        let totalPrice = 0;
        const baseNames = [];
        const baseIds = [];
        
        baseOptions.forEach(function(option) {
            const baseName = option.text.split(' (+Ugx')[0].trim();
            const basePrice = parseFloat(option.dataset.price) || 0;
            const baseType = option.dataset.type;
            
            // Add to base names for display
            if (baseType === 'priced') {
                baseNames.push(baseName + ' (+Ugx ' + basePrice + ')');
                totalPrice += basePrice;
            } else {
                baseNames.push(baseName);
            }
            
            baseIds.push(option.value);
        });
        
        // Add protein price
        const sourcePrice = parseFloat(sourceOption.dataset.price) || 0;
        totalPrice += sourcePrice;
        
        const sourceName = sourceOption.text.split(' - Ugx')[0].trim();
        const displayName = 'Custom: ' + baseNames.join(' + ') + ' with ' + sourceName;

        // Create hidden inputs for ALL base foods (free and priced)
        createHiddenInput('custom_base_items[]', baseIds.join(','));
        createHiddenInput('custom_source_items[]', sourceId);
        createHiddenInput('custom_quantities[]', quantity);
        createHiddenInput('custom_types[]', 'custom_combo');

        // Add to order items (check for duplicates)
        addOrderItem(displayName, totalPrice, quantity, 'custom_combo');
    }

    function addProteinOnly() {
        if (!customSourceSelect || !customQuantity) return;
        
        const sourceId = customSourceSelect.value;
        const quantity = parseInt(customQuantity.value) || 1;

        if (!sourceId) {
            alert('Please select a protein source.');
            return;
        }

        const sourceOption = customSourceSelect.options[customSourceSelect.selectedIndex];
        const sourceName = sourceOption.text.split(' - Ugx')[0].trim();
        const unitPrice = parseFloat(sourceOption.dataset.price) || 0;
        const displayName = 'Protein Only: ' + sourceName;

        // Create hidden input
        createHiddenInput('custom_base_items[]', '');
        createHiddenInput('custom_source_items[]', sourceId);
        createHiddenInput('custom_quantities[]', quantity);
        createHiddenInput('custom_types[]', 'protein_only');

        // Add to order items (check for duplicates)
        addOrderItem(displayName, unitPrice, quantity, 'protein_only');

        // Reset form
        customSourceSelect.selectedIndex = 0;
        customQuantity.value = 1;
        if (proteinOnlyPreview) proteinOnlyPreview.style.display = 'none';

        updateOrderTotal();
    }

    function createHiddenInput(name, value) {
        if (!customComboInputs) return;
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value;
        customComboInputs.appendChild(input);
    }

    function updateMenuItemQuantity(itemId, quantity) {
        const input = document.getElementById('qty_' + itemId);
        if (!input) return;
        
        // Get price from data attribute
        const priceText = input.getAttribute('data-price');
        const price = parseFloat(priceText);
        if (isNaN(price)) return;
        
        // Find the card and get display name
        let displayName = '';
        const cardElement = input.closest('.card');
        if (cardElement) {
            const titleElement = cardElement.querySelector('.card-title');
            if (titleElement) {
                displayName = titleElement.textContent.trim();
            }
        }
        
        // If not found, create a generic name
        if (!displayName) {
            displayName = 'Menu Item ' + itemId;
        }
        
        // Find if this item already exists
        const existingItemKey = findExistingItem(displayName, 'regular');
        
        if (quantity === 0) {
            if (existingItemKey) {
                delete orderItems[existingItemKey];
            }
        } else {
            if (existingItemKey) {
                // Update existing item
                orderItems[existingItemKey].quantity = quantity;
                orderItems[existingItemKey].total_price = price * quantity;
            } else {
                // Add new item
                const itemKey = 'item_' + itemCounter++;
                orderItems[itemKey] = {
                    quantity: quantity,
                    unit_price: price,
                    total_price: price * quantity,
                    display_name: displayName,
                    type: 'regular'
                };
            }
        }
        
        updateOrderDisplay();
        updateOrderTotal();
    }

    function findExistingItem(displayName, type) {
        return Object.keys(orderItems).find(function(itemKey) {
            const item = orderItems[itemKey];
            return item.display_name === displayName && item.type === type;
        });
    }

    function addOrderItem(displayName, unitPrice, quantity, type) {
        // Check if this item already exists to avoid duplicates
        const existingItemKey = findExistingItem(displayName, type);
        
        if (existingItemKey) {
            // Update existing item instead of creating duplicate
            orderItems[existingItemKey].quantity += quantity;
            orderItems[existingItemKey].total_price = orderItems[existingItemKey].unit_price * orderItems[existingItemKey].quantity;
        } else {
            // Add new item
            const itemKey = 'item_' + itemCounter++;
            orderItems[itemKey] = {
                quantity: quantity,
                unit_price: unitPrice,
                total_price: unitPrice * quantity,
                display_name: displayName,
                type: type
            };
        }
        updateOrderDisplay();
        updateOrderTotal();
    }

    function updateOrderDisplay() {
        if (!orderItemsList) return;
        
        orderItemsList.innerHTML = '';
        
        if (Object.keys(orderItems).length === 0) {
            orderItemsList.innerHTML = '<p class="text-muted text-center small">No items added yet</p>';
            return;
        }

        // Display all items
        let hasItems = false;
        Object.keys(orderItems).forEach(function(key) {
            const item = orderItems[key];
            if (item.quantity > 0) {
                hasItems = true;
                
                // Format price display - leave blank for items with price 0
                let priceDisplay = '';
                let subtotalDisplay = '';
                
                if (item.unit_price > 0) {
                    priceDisplay = 'Ugx ' + item.unit_price.toFixed(2);
                    subtotalDisplay = 'Ugx ' + item.total_price.toFixed(2);
                }
                
                const itemElement = document.createElement('div');
                itemElement.className = 'd-flex justify-content-between align-items-center border-bottom py-2 small';
                
                let priceHtml = '';
                if (priceDisplay) {
                    priceHtml = '<small class="text-muted">' + item.quantity + ' × ' + priceDisplay + '</small>';
                }
                
                let subtotalHtml = '';
                if (subtotalDisplay) {
                    subtotalHtml = '<div class="fw-bold">' + subtotalDisplay + '</div>';
                }
                
                itemElement.innerHTML = '<div class="flex-grow-1">' +
                    '<div class="fw-medium">' + item.display_name + '</div>' +
                    priceHtml +
                    '</div>' +
                    '<div class="text-end">' +
                    subtotalHtml +
                    '</div>';
                orderItemsList.appendChild(itemElement);
            }
        });
        
        if (!hasItems) {
            orderItemsList.innerHTML = '<p class="text-muted text-center small">No items added yet</p>';
        }
    }

    function updateOrderTotal() {
        let subtotal = 0;
        Object.keys(orderItems).forEach(function(key) {
            const item = orderItems[key];
            if (item.quantity > 0) {
                subtotal += item.total_price;
            }
        });
        
        // No delivery fee - Total is same as subtotal
        const total = subtotal;
        
        if (subtotalElement) {
            subtotalElement.textContent = 'Ugx ' + subtotal.toFixed(2);
        }
        if (totalElement) {
            totalElement.textContent = 'Ugx ' + total.toFixed(2);
        }
        if (totalAmountInput) {
            totalAmountInput.value = total.toFixed(2);
        }
        
        // Update button state
        if (submitBtn) {
            const shouldDisable = subtotal === 0;
            submitBtn.disabled = shouldDisable;
            
            // Visual feedback
            if (shouldDisable) {
                submitBtn.classList.add('btn-secondary');
                submitBtn.classList.remove('btn-success');
            } else {
                submitBtn.classList.remove('btn-secondary');
                submitBtn.classList.add('btn-success');
            }
        }
    }

    // Form submission handler
    function setupFormSubmission() {
        const form = document.getElementById('onlineOrderForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get customer information
            const customerName = document.getElementById('customer_name').value.trim();
            const customerPhone = document.getElementById('customer_phone').value.trim();
            const customerEmail = document.getElementById('customer_email').value.trim();
            const deliveryAddress = document.getElementById('delivery_address').value.trim();
            const orderNotes = document.getElementById('order_notes').value.trim();
            const preferredDeliveryTime = document.getElementById('preferred_delivery_time') ? 
                document.getElementById('preferred_delivery_time').value : 'asap';

            // Validate required fields
            if (!customerName) {
                showAlert('Please enter your name', 'danger');
                document.getElementById('customer_name').focus();
                return;
            }

            if (!customerPhone) {
                showAlert('Please enter your phone number', 'danger');
                document.getElementById('customer_phone').focus();
                return;
            }

            if (!deliveryAddress) {
                showAlert('Please enter your delivery address', 'danger');
                document.getElementById('delivery_address').focus();
                return;
            }

            // Check if there are order items
            let hasItems = false;
            Object.keys(orderItems).forEach(function(key) {
                if (orderItems[key].quantity > 0) {
                    hasItems = true;
                }
            });

            if (!hasItems) {
                showAlert('Please add at least one item to your order', 'danger');
                return;
            }

            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Placing Order...';

            // Create FormData for submission
            const formData = new FormData();

            // Add customer information
            formData.append('customer_name', customerName);
            formData.append('customer_phone', customerPhone);
            formData.append('customer_email', customerEmail);
            formData.append('delivery_address', deliveryAddress);
            formData.append('order_notes', orderNotes);
            formData.append('preferred_delivery_time', preferredDeliveryTime);
            
            // Add total amount
            const totalAmount = totalAmountInput ? totalAmountInput.value : calculateTotalAmount();
            formData.append('total_amount', totalAmount);

            // Add regular menu items
            Object.keys(orderItems).forEach(function(key) {
                const item = orderItems[key];
                if (item.quantity > 0 && item.type === 'regular') {
                    // Extract menu item ID from the display name
                    const itemId = findMenuItemId(item.display_name);
                    if (itemId) {
                        formData.append(`qty_${itemId}`, item.quantity);
                    }
                }
            });

            // Add custom combo items from hidden inputs
            const customBaseItems = document.querySelectorAll('input[name="custom_base_items[]"]');
            const customSourceItems = document.querySelectorAll('input[name="custom_source_items[]"]');
            const customQuantities = document.querySelectorAll('input[name="custom_quantities[]"]');
            const customTypes = document.querySelectorAll('input[name="custom_types[]"]');

            customBaseItems.forEach(input => {
                if (input.value) {
                    formData.append('custom_base_items[]', input.value);
                }
            });
            customSourceItems.forEach(input => {
                if (input.value) {
                    formData.append('custom_source_items[]', input.value);
                }
            });
            customQuantities.forEach(input => {
                if (input.value) {
                    formData.append('custom_quantities[]', input.value);
                }
            });
            customTypes.forEach(input => {
                if (input.value) {
                    formData.append('custom_types[]', input.value);
                }
            });

            // Submit order
            fetch('/orders/online/submit/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Success - show message and redirect
                    showAlert(data.message || 'Order placed successfully!', 'success');
                    
                    // Redirect to success page after delay
                    setTimeout(() => {
                        window.location.href = `/orders/online/success/${data.order_id}/`;
                    }, 2000);
                } else {
                    throw new Error(data.error || 'Failed to place order');
                }
            })
            .catch(error => {
                showAlert('Error placing order: ' + error.message, 'danger');
            })
            .finally(() => {
                // Reset button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i> Place Order';
            });
        });
    }

    // Helper function to find menu item ID from display name
    function findMenuItemId(displayName) {
        // Look through all menu item cards
        const menuCards = document.querySelectorAll('.card');
        for (let card of menuCards) {
            const titleElement = card.querySelector('.card-title');
            if (titleElement && titleElement.textContent.trim() === displayName) {
                // Look for quantity input in this card
                const input = card.querySelector('input[id^="qty_"]');
                if (input) {
                    const itemId = input.id.replace('qty_', '');
                    return itemId;
                }
            }
        }
        
        // For custom items, we don't need to find a specific menu item ID
        if (displayName.includes('Custom:') || displayName.includes('Protein Only:') || displayName.includes('(Base Only)') || displayName.includes('Free Base:')) {
            return null;
        }
        
        return null;
    }

    function calculateTotalAmount() {
        let subtotal = 0;
        Object.keys(orderItems).forEach(function(key) {
            const item = orderItems[key];
            if (item.quantity > 0) {
                subtotal += item.total_price;
            }
        });
        return subtotal.toFixed(2);
    }

    function showAlert(message, type) {
        // Remove existing alerts
        document.querySelectorAll('.online-order-alert').forEach(alert => alert.remove());
        
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3 online-order-alert`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert before the form
        const form = document.getElementById('onlineOrderForm');
        if (form) {
            form.parentNode.insertBefore(alertDiv, form);
            
            // Auto remove after 5 seconds for success messages
            if (type === 'success') {
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.remove();
                    }
                }, 5000);
            }
        } else {
            // Fallback to top of page
            document.body.insertBefore(alertDiv, document.body.firstChild);
        }
    }

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Remove invalid class when user starts typing
    const form = document.getElementById('onlineOrderForm');
    if (form) {
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('input', function() {
                if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                }
            });
        });
    }

    // Initialize everything
    initializeQuantityButtons();
    initializeCustomCombos();
    setupFormSubmission();
    updateOrderTotal();
});