# CREATE ACTION

# Action Name: Sales Order WhatsApp Automation
# Model: sale.order
# TRIGGER: On Save (Create & Update)
# TRIGGER FIELDS: state
# ACTION: Execute Python Code


# =====================================================
# Tika Sale Orders WhatsApp Automation
# =====================================================

template_name = 'Tika Sales Order Message Template'
allowed_company_name = 'TIKA'
# allowed_customer_name = ''

# =====================================================
# VALIDATION
# =====================================================

is_valid = True

# Company check
if record.company_id.name != allowed_company_name:
    is_valid = False

# # Customer check
# if record.partner_id.name != allowed_customer_name:
#     is_valid = False

# Only confirmed sales orders
if record.state not in ['sale', 'done']:
    is_valid = False

# Block cancelled orders
if record.state == 'cancel':
    is_valid = False

# Block returns — return pickings have 'Return of' in origin
if record.origin and 'Return of' in record.origin:
    is_valid = False


# =====================================================
# DUPLICATE PREVENTION
# =====================================================

existing_log = env['mail.message'].search([
    ('model', '=', 'sale.order'),  
    ('res_id', '=', record.id),
    '|',
    ('body', 'ilike', 'SALES ORDER SENT:'),
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

    formatted_phone = '+' + digits if len(digits) >= 12 else None

    # =====================================================
    # VALID PHONE
    # =====================================================

    if formatted_phone:

        try:

            # =====================================================
            # CREATE WHATSAPP COMPOSER
            # =====================================================

            composer = env['whatsapp.composer'].with_context(
                active_model='sale.order',
                active_ids=[record.id],
                active_id=record.id,
            ).create({
                'wa_template_id': template.id,
                'res_model': 'sale.order',
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
                    f"SALES ORDER SENT: "
                    f"Message sent to {formatted_phone}"
                )
            )

        except Exception as e:

            # =====================================================
            # ERROR LOG
            # =====================================================

            record.message_post(
                body=f"SALES ORDER SCRIPT ERROR: {str(e)}"
            )

    else:

        # =====================================================
        # INVALID PHONE
        # =====================================================

        record.message_post(
            body="ERROR: No valid customer phone number found."
        )