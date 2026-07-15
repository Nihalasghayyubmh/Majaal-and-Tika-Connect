# CREATE THE ACTION

# ACTION NAME: Quotation WhatsApp Automation
# MODEL: sale.order
# TRIGGER: On Save (Create & Update)
# TRIGGER FIELDS: state, partner_id, order_line, amount_total, validity_date, payment_term_id
# ACTION: Execute Python Code

# =====================================================
# Majaal Quotation WhatsApp Automation
# =====================================================

template_name = 'majaal_new_quotation_message_template'
allowed_company_name = 'Majaal'
# allowed_customer_name = 'المعرض الرئيسي'

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

# Only quotations
if record.state not in ['draft', 'sent']:
    is_valid = False

# =====================================================
# DUPLICATE PREVENTION
# =====================================================

existing_log = env['mail.message'].search([
    ('model', '=', 'sale.order'),
    ('res_id', '=', record.id),
    ('body', 'ilike', 'QUOTATION SENT:')
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
                    f"QUOTATION SENT: "
                    f"Message sent to {formatted_phone}"
                )
            )

        except Exception as e:

            # =====================================================
            # ERROR LOG
            # =====================================================

            record.message_post(
                body=f"QUOTATION SCRIPT ERROR: {str(e)}"
            )

    else:

        # =====================================================
        # INVALID PHONE
        # =====================================================

        record.message_post(
            body="ERROR: No valid customer phone number found."
        )