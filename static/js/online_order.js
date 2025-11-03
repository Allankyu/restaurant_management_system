// static/js/online_order.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Online order JS loaded');
    
    // Order items management
    let orderItems = {};
    let itemCounter = 0;
    
    const orderItemsList = document.getElementById('onlineOrderItemsList');
    const subtotalElement = document.getElementById('onlineSubtotal');
    const totalElement = document.getElementById('onlineTotal');
    const totalAmountInput = document.getElementById('onlineTotalAmount');
    const submitBtn = document.getElementById('submitOnlineOrderBtn');
    const deliveryFee = 100;

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

    console.log('Elements found:', {
        orderItemsList: !!orderItemsList,
        subtotalElement: !!subtotalElement,
        totalElement: !!totalElement,
        totalAmountInput: !!totalAmountInput,
        submitBtn: !!submitBtn,
        customBaseSelect: !!customBaseSelect,
        customSourceSelect: !!customSourceSelect,
        addCustomComboBtn: !!addCustomComboBtn
    });

    // Initialize quantity buttons
    function initializeQuantityButtons() {
        console.log('Initializing quantity buttons...');
        
        // Quantity button handlers for plus buttons
        document.querySelectorAll('.plus-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                console.log('Plus button clicked');
                const itemId = this.getAttribute('data-item');
                console.log('Item ID:', itemId);
                
                const input = document.getElementById('qty_' + itemId);
                if (!input) {
                    console.error('Input not found for item:', itemId);
                    return;
                }
                
                const currentValue = parseInt(input.value) || 0;
                const newValue = currentValue + 1;
                input.value = newValue;
                console.log('New quantity:', newValue);
                
                updateMenuItemQuantity(itemId, newValue);
            });
        });

        // Quantity button handlers for minus buttons
        document.querySelectorAll('.minus-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                console.log('Minus button clicked');
                const itemId = this.getAttribute('data-item');
                console.log('Item ID:', itemId);
                
                const input = document.getElementById('qty_' + itemId);
                if (!input) {
                    console.error('Input not found for item:', itemId);
                    return;
                }
                
                const currentValue = parseInt(input.value) || 0;
                if (currentValue > 0) {
                    const newValue = currentValue - 1;
                    input.value = newValue;
                    console.log('New quantity:', newValue);
                    updateMenuItemQuantity(itemId, newValue);
                }
            });
        });
        
        console.log('Quantity buttons initialized. Found:', 
            document.querySelectorAll('.plus-btn').length, 'plus buttons and',
            document.querySelectorAll('.minus-btn').length, 'minus buttons'
        );
    }

    // Initialize custom combo functionality
    function initializeCustomCombos() {
        console.log('Initializing custom combo functionality...');
        
        if (addCustomComboBtn) {
            addCustomComboBtn.addEventListener('click', addCustomCombo);
            console.log('Custom combo button initialized');
        }
        
        if (addProteinOnlyBtn) {
            addProteinOnlyBtn.addEventListener('click', addProteinOnly);
            console.log('Protein only button initialized');
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
            // Show combo preview
            const baseNames = [];
            let totalPrice = 0;
            
            baseOptions.forEach(function(option) {
                const baseName = option.text.split(' (+Ksh')[0];
                const basePrice = parseFloat(option.dataset.price) || 0;
                const baseType = option.dataset.type;
                
                if (baseType === 'priced') {
                    baseNames.push(baseName + ' (+Ksh ' + basePrice + ')');
                    totalPrice += basePrice;
                } else {
                    baseNames.push(baseName);
                }
            });

            const sourceOption = customSourceSelect.options[customSourceSelect.selectedIndex];
            const sourceName = sourceOption.text.split(' - Ksh')[0];
            const sourcePrice = parseFloat(sourceOption.dataset.price) || 0;
            
            totalPrice += sourcePrice;

            if (comboPreviewText) comboPreviewText.textContent = baseNames.join(' + ') + ' with ' + sourceName + ' × ' + quantity;
            if (comboPreviewPrice) comboPreviewPrice.textContent = 'Ksh ' + (totalPrice * quantity).toFixed(2);
            if (customComboPreview) customComboPreview.style.display = 'block';

        } else if (!baseOptions.length && sourceId) {
            // Show protein only preview
            const sourceOption = customSourceSelect.options[customSourceSelect.selectedIndex];
            const sourceName = sourceOption.text.split(' - Ksh')[0];
            const sourcePrice = parseFloat(sourceOption.dataset.price) || 0;
            const totalPrice = sourcePrice * quantity;

            if (proteinPreviewText) proteinPreviewText.textContent = sourceName + ' × ' + quantity;
            if (proteinPreviewPrice) proteinPreviewPrice.textContent = 'Ksh ' + totalPrice.toFixed(2);
            if (proteinOnlyPreview) proteinOnlyPreview.style.display = 'block';
        } else if (baseOptions.length > 0 && !sourceId) {
            // Show base only preview for priced base foods
            const pricedBases = baseOptions.filter(function(option) {
                return option.dataset.type === 'priced';
            });
            if (pricedBases.length > 0) {
                const baseNames = [];
                let totalPrice = 0;
                
                pricedBases.forEach(function(option) {
                    const baseName = option.text.split(' (+Ksh')[0];
                    const basePrice = parseFloat(option.dataset.price) || 0;
                    baseNames.push(baseName + ' (+Ksh ' + basePrice + ')');
                    totalPrice += basePrice;
                });

                if (comboPreviewText) comboPreviewText.textContent = baseNames.join(' + ') + ' × ' + quantity;
                if (comboPreviewPrice) comboPreviewPrice.textContent = 'Ksh ' + (totalPrice * quantity).toFixed(2);
                if (customComboPreview) customComboPreview.style.display = 'block';
            }
        }
    }

    function addCustomCombo() {
        if (!customBaseSelect || !customSourceSelect || !customQuantity) return;
        
        const baseOptions = Array.from(customBaseSelect.selectedOptions);
        const sourceId = customSourceSelect.value;
        const quantity = parseInt(customQuantity.value) || 1;

        // Check if we have priced base foods without protein (base only)
        const pricedBases = baseOptions.filter(function(option) {
            return option.dataset.type === 'priced';
        });
        
        if (baseOptions.length > 0 && !sourceId && pricedBases.length > 0) {
            // Handle priced base foods without protein
            addBaseOnlyItems(baseOptions, quantity);
        } else if (baseOptions.length > 0 && sourceId) {
            // Handle custom combo with base + protein
            addCustomComboWithProtein(baseOptions, sourceId, quantity);
        } else {
            alert('Please select at least one base food and a protein source, or priced base foods only.');
            return;
        }

        // Reset form
        customBaseSelect.selectedIndex = -1;
        customSourceSelect.selectedIndex = 0;
        customQuantity.value = 1;
        if (customComboPreview) customComboPreview.style.display = 'none';

        updateOrderTotal();
    }

    function addCustomComboWithProtein(baseOptions, sourceId, quantity) {
        const sourceOption = customSourceSelect.options[customSourceSelect.selectedIndex];
        
        // Calculate total price
        let totalPrice = 0;
        baseOptions.forEach(function(option) {
            totalPrice += parseFloat(option.dataset.price) || 0;
        });
        totalPrice += parseFloat(sourceOption.dataset.price) || 0;

        // Build display name
        const baseNames = baseOptions.map(function(option) {
            const baseName = option.text.split(' (+Ksh')[0];
            const basePrice = parseFloat(option.dataset.price) || 0;
            const baseType = option.dataset.type;
            
            if (baseType === 'priced') {
                return baseName + ' (+' + basePrice + ')';
            }
            return baseName;
        });
        
        const sourceName = sourceOption.text.split(' - Ksh')[0];
        const displayName = 'Custom: ' + baseNames.join(' + ') + ' with ' + sourceName;
        const baseIds = baseOptions.map(function(option) {
            return option.value;
        });

        // Create hidden inputs
        createHiddenInput('custom_base_items[]', baseIds.join(','));
        createHiddenInput('custom_source_items[]', sourceId);
        createHiddenInput('custom_quantities[]', quantity);
        createHiddenInput('custom_types[]', 'custom_combo');

        // Add to order items (check for duplicates)
        addOrderItem(displayName, totalPrice, quantity, 'custom_combo');
    }

    function addBaseOnlyItems(baseOptions, quantity) {
        const pricedBases = baseOptions.filter(function(option) {
            return option.dataset.type === 'priced';
        });
        
        pricedBases.forEach(function(baseOption) {
            const baseName = baseOption.text.split(' (+Ksh')[0];
            const basePrice = parseFloat(baseOption.dataset.price) || 0;
            const displayName = baseName + ' (Base Only)';

            // Create hidden inputs for each priced base
            createHiddenInput('custom_base_items[]', baseOption.value);
            createHiddenInput('custom_source_items[]', '');
            createHiddenInput('custom_quantities[]', quantity);
            createHiddenInput('custom_types[]', 'base_only');

            // Add to order items (check for duplicates)
            addOrderItem(displayName, basePrice, quantity, 'base_only');
        });
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
        const sourceName = sourceOption.text.split(' - Ksh')[0];
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
        console.log('Created hidden input:', name, value);
    }

    function updateMenuItemQuantity(itemId, quantity) {
        console.log('=== UPDATE MENU ITEM QUANTITY ===');
        console.log('Item ID:', itemId, 'Quantity:', quantity);
        
        const input = document.getElementById('qty_' + itemId);
        if (!input) {
            console.error('Input not found for update:', itemId);
            return;
        }
        
        // Get price from data attribute
        const priceText = input.getAttribute('data-price');
        console.log('Price text:', priceText);
        
        const price = parseFloat(priceText);
        if (isNaN(price)) {
            console.error('Invalid price for item:', itemId, 'Price text:', priceText);
            return;
        }
        console.log('Parsed price:', price);
        
        // Find the card and get display name - use a more reliable selector
        let card = null;
        let displayName = '';
        
        // Try multiple ways to find the card and name
        const cardElement = input.closest('.card');
        if (cardElement) {
            card = cardElement;
            const titleElement = cardElement.querySelector('.card-title');
            if (titleElement) {
                displayName = titleElement.textContent.trim();
            }
        }
        
        // If not found, try finding by data-item attribute
        if (!displayName) {
            const itemElement = document.querySelector('[data-item="' + itemId + '"]');
            if (itemElement) {
                const parentCard = itemElement.closest('.card');
                if (parentCard) {
                    const titleElement = parentCard.querySelector('.card-title');
                    if (titleElement) {
                        displayName = titleElement.textContent.trim();
                    }
                }
            }
        }
        
        // If still not found, create a generic name
        if (!displayName) {
            displayName = 'Menu Item ' + itemId;
        }
        
        console.log('Found display name:', displayName);
        
        // Find if this item already exists
        const existingItemKey = findExistingItem(displayName, 'regular');
        console.log('Existing item key:', existingItemKey);
        
        if (quantity === 0) {
            if (existingItemKey) {
                console.log('Removing item:', displayName);
                delete orderItems[existingItemKey];
            }
        } else {
            if (existingItemKey) {
                // Update existing item
                console.log('Updating existing item:', displayName, 'New quantity:', quantity);
                orderItems[existingItemKey].quantity = quantity;
                orderItems[existingItemKey].total_price = price * quantity;
            } else {
                // Add new item
                const itemKey = 'item_' + itemCounter++;
                console.log('Adding new item:', displayName, 'Quantity:', quantity, 'Price:', price);
                orderItems[itemKey] = {
                    quantity: quantity,
                    unit_price: price,
                    total_price: price * quantity,  // FIXED: Changed = to :
                    display_name: displayName,
                    type: 'regular'
                };
            }
        }
        
        console.log('Current order items:', orderItems);
        updateOrderDisplay();
        updateOrderTotal();
    }

    function findExistingItem(displayName, type) {
        const key = Object.keys(orderItems).find(function(itemKey) {
            const item = orderItems[itemKey];
            return item.display_name === displayName && item.type === type;
        });
        console.log('findExistingItem result for', displayName, ':', key);
        return key;
    }

    function addOrderItem(displayName, unitPrice, quantity, type) {
        console.log('=== ADD ORDER ITEM ===');
        console.log('Display Name:', displayName, 'Unit Price:', unitPrice, 'Quantity:', quantity, 'Type:', type);
        
        // Check if this item already exists to avoid duplicates
        const existingItemKey = findExistingItem(displayName, type);
        
        if (existingItemKey) {
            // Update existing item instead of creating duplicate
            console.log('Updating existing item:', displayName);
            orderItems[existingItemKey].quantity += quantity;
            orderItems[existingItemKey].total_price = orderItems[existingItemKey].unit_price * orderItems[existingItemKey].quantity;
        } else {
            // Add new item
            const itemKey = 'item_' + itemCounter++;
            console.log('Adding new item:', displayName, 'Quantity:', quantity, 'Price:', unitPrice);
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
        console.log('=== UPDATE ORDER DISPLAY ===');
        console.log('Order items count:', Object.keys(orderItems).length);
        
        if (!orderItemsList) {
            console.error('Order items list element not found');
            return;
        }
        
        orderItemsList.innerHTML = '';
        
        if (Object.keys(orderItems).length === 0) {
            orderItemsList.innerHTML = '<p class="text-muted text-center small">No items added yet</p>';
            console.log('Display: No items added');
            return;
        }

        // Display all items
        let hasItems = false;
        Object.keys(orderItems).forEach(function(key) {
            const item = orderItems[key];
            if (item.quantity > 0) {
                hasItems = true;
                const itemElement = document.createElement('div');
                itemElement.className = 'd-flex justify-content-between align-items-center border-bottom py-2 small';
                itemElement.innerHTML = '<div class="flex-grow-1">' +
                    '<div class="fw-medium">' + item.display_name + '</div>' +
                    '<small class="text-muted">' + item.quantity + ' × Ksh ' + item.unit_price.toFixed(2) + '</small>' +
                    '</div>' +
                    '<div class="text-end">' +
                    '<div class="fw-bold">Ksh ' + item.total_price.toFixed(2) + '</div>' +
                    '</div>';
                orderItemsList.appendChild(itemElement);
                console.log('Added to display:', item.display_name, 'Qty:', item.quantity);
            }
        });
        
        if (!hasItems) {
            orderItemsList.innerHTML = '<p class="text-muted text-center small">No items added yet</p>';
            console.log('Display: No items with quantity > 0');
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
        
        const total = subtotal + deliveryFee;
        
        console.log('=== UPDATE ORDER TOTAL ===');
        console.log('Subtotal:', subtotal, 'Total:', total);
        
        if (subtotalElement) {
            subtotalElement.textContent = 'Ksh ' + subtotal.toFixed(2);
        }
        if (totalElement) {
            totalElement.textContent = 'Ksh ' + total.toFixed(2);
        }
        if (totalAmountInput) {
            totalAmountInput.value = total.toFixed(2);
        }
        
        // Update button state
        if (submitBtn) {
            const shouldDisable = subtotal === 0;
            submitBtn.disabled = shouldDisable;
            console.log('Submit button disabled:', shouldDisable);
            
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

    // === FORM SUBMISSION HANDLER ===
    function setupFormSubmission() {
        const form = document.getElementById('onlineOrderForm');
        if (!form) {
            console.error('Online order form not found');
            return;
        }

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('=== ONLINE ORDER SUBMISSION STARTED ===');
            
            // Get customer information
            const customerName = document.getElementById('customer_name').value.trim();
            const customerPhone = document.getElementById('customer_phone').value.trim();
            const customerEmail = document.getElementById('customer_email').value.trim();
            const deliveryAddress = document.getElementById('delivery_address').value.trim();
            const orderNotes = document.getElementById('order_notes').value.trim();
            const preferredDeliveryTime = document.getElementById('preferred_delivery_time') ? 
                document.getElementById('preferred_delivery_time').value : 'asap';
            
            console.log('Customer details:', {
                customerName, customerPhone, customerEmail, deliveryAddress, orderNotes, preferredDeliveryTime
            });

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

            console.log('All validations passed, submitting order...');

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

            console.log('Total amount:', totalAmount);

            // Add regular menu items
            Object.keys(orderItems).forEach(function(key) {
                const item = orderItems[key];
                if (item.quantity > 0 && item.type === 'regular') {
                    // Extract menu item ID from the display name
                    const itemId = findMenuItemId(item.display_name);
                    if (itemId) {
                        formData.append(`qty_${itemId}`, item.quantity);
                        console.log(`Added regular item: qty_${itemId} = ${item.quantity}`);
                    }
                }
            });

            // Add custom combo items from hidden inputs
            const customBaseItems = document.querySelectorAll('input[name="custom_base_items[]"]');
            const customSourceItems = document.querySelectorAll('input[name="custom_source_items[]"]');
            const customQuantities = document.querySelectorAll('input[name="custom_quantities[]"]');
            const customTypes = document.querySelectorAll('input[name="custom_types[]"]');

            console.log(`Custom items: ${customBaseItems.length} base, ${customSourceItems.length} source, ${customQuantities.length} quantities`);

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

            // === FIXED URL - Match your actual URL structure ===
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
                console.log('Server response:', data);
                
                if (data.success) {
                    // Success - show message and redirect
                    showAlert(data.message || 'Order placed successfully!', 'success');
                    console.log(`Order #${data.order_number} created successfully`);
                    
                    // Redirect to success page after delay - FIXED URL
                    setTimeout(() => {
                        window.location.href = `/orders/online/success/${data.order_id}/`;
                    }, 2000);
                } else {
                    throw new Error(data.error || 'Failed to place order');
                }
            })
            .catch(error => {
                console.error('Order submission error:', error);
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
        console.log('Finding menu item ID for:', displayName);
        
        // Look through all menu item cards
        const menuCards = document.querySelectorAll('.card');
        for (let card of menuCards) {
            const titleElement = card.querySelector('.card-title');
            if (titleElement && titleElement.textContent.trim() === displayName) {
                // Look for quantity input in this card
                const input = card.querySelector('input[id^="qty_"]');
                if (input) {
                    const itemId = input.id.replace('qty_', '');
                    console.log('Found item ID:', itemId);
                    return itemId;
                }
            }
        }
        
        // For custom items, we don't need to find a specific menu item ID
        // as they're handled by the custom combo system
        if (displayName.includes('Custom:') || displayName.includes('Protein Only:') || displayName.includes('(Base Only)')) {
            console.log('Custom item detected, no specific menu item ID needed');
            return null;
        }
        
        console.warn('Could not find menu item ID for:', displayName);
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
        return (subtotal + deliveryFee).toFixed(2);
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
    
    console.log('=== INITIALIZATION COMPLETE ===');
    console.log('Order items:', orderItems);
    console.log('Ready for user interaction');
});