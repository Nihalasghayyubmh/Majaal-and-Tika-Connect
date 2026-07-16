# CREATE Automated Action

# Action Name: 48 Hour Delivery Reminder Automation
# Model: stock.picking
# TRIGGER: Based on Timed Condition
# Date Field: Scheduled Date
# Setting	Value
# Execute	Before
# Delay	48
# Unit	Hours
# ACTION: Execute Python Code


template_name = 'Tika Delivery Schedule Message Template'
allowed_company_name = 'TIKA'
# allowed_customer_name = ''

# =====================================================
# VALIDATION
# =====================================================

is_valid = True

# Outgoing deliveries only
if record.picking_type_code != 'outgoing':
    is_valid = False

# Valid states only
if record.state not in ['confirmed', 'assigned']:
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
    '|',
    ('body', 'ilike', '48H DELIVERY REMINDER SENT'),
    ('body', 'ilike', 'ERROR'),
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
                    f"48H DELIVERY REMINDER SENT "
                    f"to {formatted_phone}"
                )
            )

        except Exception as e:

            # =====================================================
            # ERROR LOG
            # =====================================================

            record.message_post(
                body=(
                    f"DELIVERY REMINDER ERROR: "
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