# WhatsApp Business API Integration — Odoo 17
### Majaal & Tika

---

## Overview

This project integrates the WhatsApp Business API (Meta Cloud API) with Odoo 17 to automate customer communications for two companies — **Majaal** and **Tika**. Automated WhatsApp messages are triggered by business events such as delivery confirmations, invoice sends, sales order confirmations, and new customer registrations.

---

## Architecture

```
Odoo 17 (Automation Rules)
        ↓
whatsapp.composer
        ↓
Meta Cloud API (Graph API v17)
        ↓
Customer WhatsApp
        ↑
Customer Reply → Meta Webhook → Odoo Discuss
```

---

## Companies & WhatsApp Accounts

| Company | Odoo WA Account | Meta Account |
|---|---|---|
| Majaal | MajaalAccount | WhatsApp Business Account (WABA) |
| Tiks | TikaAccount | Same Meta App, separate phone number |

Both companies share the **same Meta App and webhook URL**. Odoo routes incoming messages to the correct account using the Phone Number ID in the webhook payload.

---

## Automated Messages

### 1. Delivery Confirmation
- **Trigger:** Transfer (`stock.picking`) marked as Done + Signature captured
- **Model:** `stock.picking`
- **Template:** `majaal_delivery_order_confirmation_message_template` `Tika Delivery Order Confirmation Message Template`
- **PDF Attached:** Delivery Slip (`stock.report_deliveryslip`) — includes customer signature
- **Guards:** Blocks returns (`Return of` in origin), incoming pickings, duplicate sends

### 2. NPS Survey
- **Trigger:** Transfer (`stock.picking`) marked as Done (date-based, 7 days after `scheduled_date`)
- **Model:** `stock.picking`
- **Template:** `Majaal Feedback Message template` `Tika Feedback Message Template`
- **Guards:** Specific customer filter, duplicate prevention, company check

### 3. Invoice
- **Trigger:** Invoice (`account.move`) posted
- **Model:** `account.move`
- **Template:** `majaal_invoice_message_template` `Tika Invoice Message Template`
- **PDF Attached:** Invoice (`account.account_invoices`)
- **Guards:** Blocks credit notes (`out_refund`), draft invoices, duplicate sends

### 4. Sales Order / Quotation
- **Trigger:** Sale Order (`sale.order`) state changes to `sent` (Quotation Sent)
- **Model:** `sale.order`
- **Template:** `majaal_quotation_message_template` `Tika Sales Order Message Template`
- **PDF Attached:** Quotation/Order (`sale.report_saleorder`)
- **Guards:** Blocks draft state (prevents autosave triggers), duplicate sends

---

## Template Configuration

All templates are created in Meta WhatsApp Manager and synced into Odoo.

### Template Standards
- **Category:** Utility (transactional) and Marketing
- **Language:** Arabic
- **Header Type:** Document (where PDF attached), Text (body-only messages)
- **Phone Field:** phone field of Contact or Sales Order models

### Report Bindings (PDF attachments)
| Template | Report | Technical Name |
|---|---|---|
| Delivery Confirmation | Delivery Slip | `stock.report_deliveryslip` |
| Invoice | Invoice | `account.account_invoices` |
| Sales Order | Quotation/Order | `sale.report_saleorder` |

### Template Submission Flow
1. Build template in Odoo (WhatsApp app → Templates) or Meta WhatsApp Manager
2. Click **Submit for Approval** in Odoo (pushes to Meta for review)
3. Wait for Meta approval (minutes to hours)
4. Click **Sync Template** in Odoo after approval
5. Any variable mapping changes require resubmission to Meta

---


## Automation Rule Pattern

All automation scripts follow the same structure:

```python
# 1. Set template name and company
template_name = 'template_name_here'
allowed_company_name = 'Company Name'

# 2. Validation block (is_valid = True/False)

# 3. Duplicate prevention (search mail.message chatter)

# 4. Template search

# 5. Phone sanitization (Libya +218 formatting)

# 6. whatsapp.composer create + action_send_whatsapp_template()

# 7. Success/error logging to chatter
```

### Phone Sanitization (Libya +218)
```python
raw_phone = record.partner_id.mobile or record.partner_id.phone or ""
digits = "".join(filter(str.isdigit, raw_phone))

if digits.startswith('0'):
    digits = '218' + digits[1:]
elif len(digits) == 9:
    digits = '218' + digits

formatted_phone = '+' + digits if len(digits) >= 12 else None
```

### Duplicate Prevention Pattern
```python
existing_log = env['mail.message'].search([
    ('model', '=', 'stock.picking'),
    ('res_id', '=', record.id),
    ('body', 'ilike', 'MESSAGE SENT')
], limit=1)

if existing_log:
    is_valid = False
```

---

## Known Constraints

| Constraint | Detail |
|---|---|
| `import requests` blocked | Odoo sandboxes automation rule Python — no external imports allowed |
| `return` statements blocked | Use nested `if` blocks instead of early returns |
| One webhook URL per Meta app | Both Majaal and Tika share Majaal's webhook URL — Odoo routes by Phone Number ID |
| Template variable changes need resubmission | Any edit to Variables tab requires Submit for Approval again |
| `import` workaround | Use `whatsapp.composer` instead of direct API calls |

---

## Meta Configuration

### Webhook Setup
- **Callback URL:** From Odoo → WhatsApp Business Account record
- **Verify Token:** From Odoo → WhatsApp Business Account record
- **Subscribed Fields:** `messages`
- **Location:** Meta Developer Console → App → WhatsApp → Configuration

### Phone Number Registration
New numbers require a registration API call before they activate:
```
POST https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/register
{
  "messaging_product": "whatsapp",
  "pin": "YOUR_6_DIGIT_PIN"
}
```
Use Graph API Explorer at developers.facebook.com/tools/explorer

### Display Name Policy
- Must match business name on website/social media
- No special characters (`|`, `*`, `#`)
- Max 25 characters
- Bilingual format: `Xtreme إكستريم` (space-separated, no pipe)

---

## Template Quality Management

### Quality Rating States
| Status | Meaning | Can Send? |
|---|---|---|
| Active - Quality Pending | Newly approved, collecting feedback | ✅ Yes |
| Active | Healthy quality rating | ✅ Yes |
| Active - Low Quality | Negative feedback accumulating | ✅ Yes (warning) |
| Paused | Quality too low — temporarily blocked | ❌ No |
| Disabled | Permanently blocked after repeated pauses | ❌ No |

### Category Reclassification Appeals
If Meta reclassifies Utility → Marketing:
1. WhatsApp Manager → Message Templates → notification banner
2. Click **"Review category updates in Business Support Home"**
3. Select template → **Request Review**
4. If rejected: file ticket at business.facebook.com/direct-support

---

## Customer Notifications (CS Team)

| Event | Notification Method |
|---|---|
| Brand new incoming message | "Notify users" field on WhatsApp Business Account |

CS team manages all conversations via **Odoo Discuss app** — the WhatsApp number cannot be opened on WhatsApp App simultaneously (API restriction).


## Files & Locations in Odoo

| Item | Location in Odoo |
|---|---|
| Automation Rules | Settings → Technical → Automation → Automated Actions |
| WhatsApp Templates | WhatsApp app → Templates |
| WhatsApp Business Accounts | WhatsApp app → Configuration → WhatsApp Business Accounts |
| Custom Fields | Settings → Technical → Fields |
| Reports | Settings → Technical → Reports |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Message not sending, no chatter log | Automation rule not firing | Check trigger, domain filter, model |
| "Template quality rating too low" | Template paused by Meta | Wait for pause to lift, check WhatsApp Manager |
| `{{variable}}` renders blank in message | Wrong field mapped in Variables tab, not resubmitted | Fix field mapping |
| Body shows `/` for invoice number | Invoice in draft state when automation fired | Add `record.state != 'posted'` guard |
| PDF attached but no signature | Delivery not fully done when report rendered | Ensure `state == 'done'` check is in place |
| Return orders getting messages | Missing return guard | Add `move_type != 'out_refund'` / `'Return of' in origin` |

---

*Last updated: July 2026*
*Odoo Version: 17*
*Meta Graph API Version: v25.0*
