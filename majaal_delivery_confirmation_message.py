# CREATE Automation Actions

# Action Name: Delivery Confirmation WhatsApp Automation
# Model: stock.picking
# TRIGGER: On Save (Create & Update)
# TRIGGER FIELDS: state, signature

# ACTION: Execute Python Code


# =====================================================
# Majaal Delivery Confirmation WhatsApp Automation
# =====================================================

template_name = 'majaal_delivery_order_confirmation_message_template'
allowed_company_name = 'Majaal'
# allowed_customer_name = 'المعرض الرئيسي'

# =====================================================
# VALIDATION
# =====================================================

is_valid = True

# Outgoing deliveries only
if record.picking_type_code != 'outgoing':
    is_valid = False

# Delivery must be completed
if record.state != 'done':
    is_valid = False

# Must contain signature
if not record.signature:
    is_valid = False

# Company check
if record.company_id.name != allowed_company_name:
    is_valid = False

# # Customer check
# if record.partner_id.name != allowed_customer_name:
#     is_valid = False

# =====================================================
# DUPLICATE PREVENTION
# =====================================================

existing_log = env['mail.message'].search([
    ('model', '=', 'stock.picking'),
    ('res_id', '=', record.id),
    ('body', 'ilike', 'DELIVERY CONFIRMATION SENT')
], limit=1)

if existing_log:
    is_valid = False

# =====================================================
# TEMPLATE SEARCH
# =====================================================

template = env['whatsapp.template'].search([
    ('name', '=', template_name)
], limit=1)

if not template:

    is_valid = False

    record.message_post(
        body=f"ERROR: Template '{template_name}' not found."
    )

# =====================================================
# PROCESS
# =====================================================

if is_valid:

    # =====================================================
    # PHONE SANITIZATION
    # =====================================================

    raw_phone = (
        record.partner_id.mobile
        or record.partner_id.phone
        or ""
    )

    digits = "".join(filter(str.isdigit, raw_phone))

    # Libya formatting
    if digits.startswith('0'):
        digits = '218' + digits[1:]

    elif len(digits) == 9:
        digits = '218' + digits

    formatted_phone = (
        '+' + digits
        if len(digits) >= 12
        else None
    )

    # =====================================================
    # VALID PHONE
    # =====================================================

    if formatted_phone:

        try:

            # =====================================================
            # CREATE WHATSAPP COMPOSER
            # =====================================================

            composer = env['whatsapp.composer'].with_context(
                active_model='stock.picking',
                active_ids=[record.id],
                active_id=record.id,
            ).create({
                'wa_template_id': template.id,
                'res_model': 'stock.picking',
                'res_ids': str([record.id]),
            })

            # =====================================================
            # SEND WHATSAPP
            # =====================================================

            composer.action_send_whatsapp_template()

            # =====================================================
            # SUCCESS LOG
            # =====================================================

            record.message_post(
                body=(
                    f"DELIVERY CONFIRMATION SENT "
                    f"to {formatted_phone}"
                )
            )

        except Exception as e:

            # =====================================================
            # ERROR LOG
            # =====================================================

            record.message_post(
                body=(
                    f"DELIVERY CONFIRMATION ERROR: "
                    f"{str(e)}"
                )
            )

    else:

        # =====================================================
        # INVALID PHONE
        # =====================================================

        record.message_post(
            body=(
                "ERROR: No valid customer "
                "phone number found."
            )
        )