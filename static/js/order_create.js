// static/js/order_create.js
document.addEventListener('DOMContentLoaded', function() {
    const orderForm = document.getElementById('orderForm');
    if (!orderForm) return;
    
    const isAdminWithoutBranch = orderForm.dataset.isAdminWithoutBranch === 'true';
    const isEditMode = window.isEditMode || false;
    
    // Single unified order items object to prevent duplicates
    let orderItems = {};
    let itemCounter = 0;
    
    const orderTotalElement = document.getElementById('orderTotal');
    const orderItemsList = document.getElementById('orderItemsList');
    const totalAmountInput = document.getElementById('totalAmountInput');
    const placeOrderBtn = document.getElementById('placeOrderBtn');
    const customerSelect = document.getElementById('customer');
    const waiterSelect = document.getElementById('waiter'); // Added waiter select
    const customComboInputs = document.getElementById('customComboInputs');

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

    // Initialize order type visibility
    updateOrderTypeVisibility();
    if (document.getElementById('order_type')) {
        document.getElementById('order_type').addEventListener('change', updateOrderTypeVisibility);
    }

    // Update custom combo preview
    if (customBaseSelect) {
        customBaseSelect.addEventListener('change', updateComboPreview);
    }
    if (customSourceSelect) {
        customSourceSelect.addEventListener('change', updateComboPreview);
    }
    if (customQuantity) {
        customQuantity.addEventListener('input', updateComboPreview);
    }

    // Add custom combo
    if (addCustomComboBtn) {
        addCustomComboBtn.addEventListener('click', addCustomCombo);
    }
    
    // Add protein only
    if (addProteinOnlyBtn) {
        addProteinOnlyBtn.addEventListener('click', addProteinOnly);
    }

    function updateOrderTypeVisibility() {
        const orderTypeSelect = document.getElementById('order_type');
        const dineInSection = document.getElementById('dineInSection');
        if (orderTypeSelect && dineInSection) {
            const orderType = orderTypeSelect.value;
            if (orderType === 'dine_in') {
                dineInSection.style.display = 'block';
            } else {
                dineInSection.style.display = 'none';
            }
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
    }

    // Quantity button handlers for regular menu items
    document.querySelectorAll('.plus-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.item;
            const input = document.getElementById('qty_' + itemId);
            if (!input) return;
            const currentValue = parseInt(input.value) || 0;
            input.value = currentValue + 1;
            updateMenuItemQuantity(itemId, currentValue + 1);
        });
    });

    document.querySelectorAll('.minus-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.item;
            const input = document.getElementById('qty_' + itemId);
            if (!input) return;
            const currentValue = parseInt(input.value) || 0;
            if (currentValue > 0) {
                input.value = currentValue - 1;
                updateMenuItemQuantity(itemId, currentValue - 1);
            }
        });
    });

    function updateMenuItemQuantity(itemId, quantity) {
        const input = document.getElementById('qty_' + itemId);
        if (!input) return;
        
        const price = parseFloat(input.dataset.price);
        const card = document.querySelector('[data-item="' + itemId + '"]');
        if (!card) return;
        
        const displayName = card.closest('.card').querySelector('.card-title').textContent;
        
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

    function findExistingItem(displayName, type) {
        return Object.keys(orderItems).find(function(key) {
            return orderItems[key].display_name === displayName && orderItems[key].type === type;
        });
    }

    function updateOrderDisplay() {
        if (!orderItemsList) return;
        
        orderItemsList.innerHTML = '';
        
        if (Object.keys(orderItems).length === 0) {
            orderItemsList.innerHTML = '<p class="text-muted text-center">No items added to order</p>';
            return;
        }

        // Display all items in a single unified list
        Object.keys(orderItems).forEach(function(key) {
            const item = orderItems[key];
            if (item.quantity > 0) {
                const itemElement = document.createElement('div');
                itemElement.className = 'd-flex justify-content-between align-items-center border-bottom py-2';
                itemElement.innerHTML = '<div class="flex-grow-1">' +
                    '<div class="fw-medium">' + item.display_name + '</div>' +
                    '<small class="text-muted">Ksh ' + item.unit_price.toFixed(2) + ' × ' + item.quantity + '</small>' +
                    '</div>' +
                    '<div class="text-end">' +
                    '<div class="fw-bold">Ksh ' + item.total_price.toFixed(2) + '</div>' +
                    '<button type="button" class="btn btn-sm btn-outline-danger remove-item" data-key="' + key + '">' +
                    '<i class="fas fa-times"></i>' +
                    '</button>' +
                    '</div>';
                orderItemsList.appendChild(itemElement);
            }
        });

        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-item').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const itemKey = this.dataset.key;
                delete orderItems[itemKey];
                updateOrderDisplay();
                updateOrderTotal();
            });
        });
    }

    function updateOrderTotal() {
        let total = 0;
        Object.keys(orderItems).forEach(function(key) {
            total += orderItems[key].total_price;
        });
        
        if (orderTotalElement) orderTotalElement.textContent = 'Ksh ' + total.toFixed(2);
        if (totalAmountInput) totalAmountInput.value = total.toFixed(2);
        
        // Update button state - INCLUDES WAITER VALIDATION
        if (placeOrderBtn) {
            const waiterSelect = document.getElementById('waiter');
            const hasWaiter = waiterSelect && waiterSelect.value;
            placeOrderBtn.disabled = total === 0 || !customerSelect || !customerSelect.value || !hasWaiter;
        }
    }

    // Customer quick selection
    document.querySelectorAll('.customer-quick-select').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const customerId = this.dataset.customerId;
            if (customerSelect) {
                customerSelect.value = customerId;
                updateOrderTotal();
            }
        });
    });

    // Form submission validation - INCLUDES WAITER VALIDATION
    if (orderForm) {
        orderForm.addEventListener('submit', function(e) {
            const waiterSelect = document.getElementById('waiter');
            
            if (Object.keys(orderItems).length === 0) {
                e.preventDefault();
                alert('Please add at least one item to the order.');
                return;
            }
            
            if (!customerSelect || !customerSelect.value) {
                e.preventDefault();
                alert('Please select a customer.');
                return;
            }

            // WAITER VALIDATION
            if (!waiterSelect || !waiterSelect.value) {
                e.preventDefault();
                alert('Please select a waiter.');
                return;
            }

            if (isAdminWithoutBranch && !document.getElementById('branch').value) {
                e.preventDefault();
                alert('Please select a branch.');
                return;
            }

            // Show loading state
            if (placeOrderBtn) {
                placeOrderBtn.disabled = true;
                placeOrderBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
        });
    }

    // Add event listener for waiter selection changes
    if (waiterSelect) {
        waiterSelect.addEventListener('change', updateOrderTotal);
    }

    // ===============================
    // NEW CUSTOMER AJAX FUNCTIONALITY
    // ===============================
    const saveCustomerBtn = document.getElementById('saveCustomerBtn');
    if (saveCustomerBtn) {
        saveCustomerBtn.addEventListener('click', createNewCustomer);
    }

    function createNewCustomer() {
        const name = document.getElementById('new_customer_name').value.trim();
        const phone = document.getElementById('new_customer_phone').value.trim();
        const email = document.getElementById('new_customer_email').value.trim();
        const address = document.getElementById('new_customer_address').value.trim();

        // Validation
        if (!name) {
            showAlert('Please enter customer name.', 'danger');
            return;
        }

        if (!phone) {
            showAlert('Please enter customer phone number.', 'danger');
            return;
        }

        // Phone validation - basic format check
        const phoneRegex = /^[0-9+\-\s()]{10,}$/;
        if (!phoneRegex.test(phone)) {
            showAlert('Please enter a valid phone number.', 'danger');
            return;
        }

        // Email validation (optional)
        if (email && !isValidEmail(email)) {
            showAlert('Please enter a valid email address.', 'danger');
            return;
        }

        // Create FormData for submission
        const formData = new FormData();
        formData.append('name', name);
        formData.append('phone', phone);
        formData.append('email', email || '');
        formData.append('address', address || '');

        // Show loading state
        saveCustomerBtn.disabled = true;
        saveCustomerBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Saving...';

        // AJAX request to create customer
        fetch('/orders/create-customer-ajax/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(handleResponse)
        .then(handleCustomerCreationSuccess)
        .catch(handleCustomerCreationError)
        .finally(resetSaveCustomerButton);
    }

    function handleResponse(response) {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }

    function handleCustomerCreationSuccess(data) {
        if (data.success) {
            // Add new customer to dropdown
            addCustomerToDropdown(data.customer);
            
            // Select the new customer
            if (customerSelect) {
                customerSelect.value = data.customer.id;
            }
            
            // Close modal and reset form
            closeCustomerModal();
            
            // Show success message
            showAlert('Customer created successfully!', 'success');
            updateOrderTotal();
        } else {
            throw new Error(data.error || 'Failed to create customer');
        }
    }

    function handleCustomerCreationError(error) {
        console.error('Customer creation error:', error);
        showAlert('Error creating customer: ' + error.message, 'danger');
    }

    function resetSaveCustomerButton() {
        saveCustomerBtn.disabled = false;
        saveCustomerBtn.innerHTML = 'Save Customer';
    }

    function addCustomerToDropdown(customer) {
        if (!customerSelect) return;
        
        const option = document.createElement('option');
        option.value = customer.id;
        option.textContent = `${customer.name} - ${customer.phone}`;
        customerSelect.appendChild(option);
    }

    function closeCustomerModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('newCustomerModal'));
        if (modal) {
            modal.hide();
        }
        // Reset form
        document.getElementById('newCustomerForm').reset();
    }

    function showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the form
        const form = document.getElementById('orderForm');
        if (form) {
            form.insertBefore(alertDiv, form.firstChild);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        } else {
            // Fallback to regular alert
            alert(message);
        }
    }

    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Helper function to get CSRF token from cookies
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
    if (orderForm) {
        const inputs = orderForm.querySelectorAll('input, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('input', function() {
                if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                }
            });
        });
    }

    // Initialize with existing order data if in edit mode
    if (isEditMode) {
        initializeEditMode();
    }

    function initializeEditMode() {
        // This function would populate the form with existing order data
        // For now, we'll just update the total display
        updateOrderTotal();
    }

    // Auto-save draft functionality (optional)
    let autoSaveTimer;
    function setupAutoSave() {
        // Clear existing timer
        if (autoSaveTimer) {
            clearTimeout(autoSaveTimer);
        }
        
        // Set new timer to save after 30 seconds of inactivity
        autoSaveTimer = setTimeout(saveOrderDraft, 30000);
    }

    function saveOrderDraft() {
        if (Object.keys(orderItems).length === 0) return;
        
        const draftData = {
            items: orderItems,
            customer_id: customerSelect ? customerSelect.value : null,
            waiter_id: waiterSelect ? waiterSelect.value : null, // Include waiter in draft
            order_type: document.getElementById('order_type') ? document.getElementById('order_type').value : null,
            total: totalAmountInput ? totalAmountInput.value : 0,
            timestamp: new Date().toISOString()
        };

        // Save to localStorage
        localStorage.setItem('orderDraft', JSON.stringify(draftData));
        console.log('Order draft saved');
    }

    function loadOrderDraft() {
        const draft = localStorage.getItem('orderDraft');
        if (draft) {
            try {
                const draftData = JSON.parse(draft);
                // Implement draft loading logic here
                console.log('Draft loaded:', draftData);
                
                // Ask user if they want to restore draft
                if (confirm('You have a saved order draft. Would you like to restore it?')) {
                    // Restore draft data
                    orderItems = draftData.items || {};
                    updateOrderDisplay();
                    updateOrderTotal();
                    
                    // Restore customer selection
                    if (customerSelect && draftData.customer_id) {
                        customerSelect.value = draftData.customer_id;
                    }
                    
                    // Restore waiter selection
                    if (waiterSelect && draftData.waiter_id) {
                        waiterSelect.value = draftData.waiter_id;
                    }
                    
                    // Restore order type
                    if (document.getElementById('order_type') && draftData.order_type) {
                        document.getElementById('order_type').value = draftData.order_type;
                        updateOrderTypeVisibility();
                    }
                }
            } catch (e) {
                console.error('Error loading draft:', e);
            }
        }
    }

    // Set up auto-save triggers
    document.addEventListener('input', setupAutoSave);
    document.addEventListener('change', setupAutoSave);

    // Load draft on page load
    if (!isEditMode) {
        loadOrderDraft();
    }

    // Clear draft when order is successfully submitted
    if (orderForm) {
        orderForm.addEventListener('submit', function() {
            localStorage.removeItem('orderDraft');
        });
    }

    // Initial update
    updateOrderTotal();
});