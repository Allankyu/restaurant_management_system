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
    const waiterSelect = document.getElementById('waiter');
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
                    total_price: price * quantity,  // FIXED: Changed = to :
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
                total_price: unitPrice * quantity,  // FIXED: Changed = to :
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
                // Format price display - leave blank for items with price 0
                let priceDisplay = '';
                let subtotalDisplay = '';
                
                if (item.unit_price > 0) {
                    priceDisplay = `Ugx ${item.unit_price.toFixed(2)}`;
                    subtotalDisplay = `Ugx ${item.total_price.toFixed(2)}`;
                }
                
                const itemElement = document.createElement('div');
                itemElement.className = 'd-flex justify-content-between align-items-center border-bottom py-2';
                
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
        
        if (orderTotalElement) orderTotalElement.textContent = 'Ugx ' + total.toFixed(2);
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

    // New Customer AJAX functionality
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
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
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
        })
        .catch(error => {
            showAlert('Error creating customer: ' + error.message, 'danger');
        })
        .finally(() => {
            saveCustomerBtn.disabled = false;
            saveCustomerBtn.innerHTML = 'Save Customer';
        });
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

    // Initial update
    updateOrderTotal();
});  
