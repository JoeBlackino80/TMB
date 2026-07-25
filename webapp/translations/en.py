# English translation of the VORU in-app UI strings (_SK_APP in webapp/webi18n.py).

APP = {
    # sidebar menu and footer
    "m_overview": "Overview", "m_mailboxes": "Mailboxes",
    "m_settings": "Settings", "m_billing": "Subscription",
    "m_logout": "Sign out",
    "f_terms": "Terms", "f_privacy": "Privacy",
    # overview
    "d_verify": "Please confirm your email address — we've sent you a link. "
                "Nothing arrived?",
    "d_verify_btn": "Resend",
    "d_paused": "Your service is paused — the trial has ended or the "
                "subscription has expired. <a href='/billing'>Activate a "
                "subscription</a>.",
    "d_trial": "Trial ends on <b>{date}</b>. <a href='/billing'>Upgrade to a "
               "subscription</a> — €4.99/month or €49/year.",
    "d_start_title": "Start by adding a mailbox",
    "d_start_body": "VORU needs access to the mailbox where your invoices arrive.",
    "d_start_btn": "Add mailbox",
    "d_demo": "This is <b>sample data</b> so you can see what your overview "
              "will look like. It disappears automatically once you add a "
              "mailbox.",
    "d_demo_btn": "Remove sample data",
    "d_overdue": "overdue", "d_unpaid": "outstanding",
    "d_this_month": "due by the end of the month", "d_next_month": "next month",
    "d_open_tasks": "open tasks",
    "d_missing_title": "Recurring invoices that haven't arrived",
    "d_missing_last": "last received {d}", "d_missing_exp": "expected by {d}",
    "d_missing_note": "Check whether the invoice landed in spam or is being "
                      "sent to a different address.",
    "d_payments_title": "Outstanding payments",
    "th_supplier": "Supplier", "th_amount": "Amount", "th_due": "Due date",
    "d_other_iban": "different IBAN — verify!", "d_today": "today",
    "d_qr_btn": "QR payment", "d_paid_btn": "Paid",
    "d_ignore_btn": "Ignore", "d_ignore_confirm": "Ignore this payment?",
    "d_qr_alt": "Payment QR code",
    "d_qr_note": "Scan it in your banking app — the amount, IBAN and payment "
                 "reference are pre-filled.",
    "d_pay_note": "You'll find payment QR codes in your email digests. "
                  "Payments are also ticked off by your bank statement or "
                  "by replying “paid 3” (the payment number) to the email.",
    "d_sepa_btn": "Bulk payment order (SEPA XML)",
    "d_sepa_note": "Upload the file to your online banking and confirm all "
                   "payments at once.",
    "d_no_payments": "No unpaid payments on record.",
    "d_renewals_title": "Expiring soon", "d_done_btn": "Done",
    "d_renewals_note": "Insurance policies, vehicle inspections, domains and "
                       "subscriptions VORU found in your mail. Tick off "
                       "what's handled so we stop reminding you.",
    "d_tax_title": "Tax deadlines (next 30 days)",
    "d_bundle_title": "Documents for your accountant",
    "d_bundle_note": "A ZIP with invoices (PDF) and a monthly payment "
                     "summary — send it to your accountant in one click.",
    "d_tasks_title": "Tasks", "d_task_due": "by {d}", "d_task_done": "Done",
    "d_no_tasks": "No open tasks.",
    # mailboxes
    "mb_title": "Email mailboxes",
    "mb_fwd_title": "Your forwarding address",
    "mb_fwd_body": "Don't want to enter your mailbox password? Just forward "
                   "invoices to this address (manually or with a rule in "
                   "your email client) and VORU will process them the same "
                   "way. The address is unique to your account — don't "
                   "share it publicly.",
    "mb_verify_title": "Confirm your email first",
    "mb_verify_body": "Connecting a mailbox unlocks once you confirm your "
                      "email address — click the link in the welcome email "
                      "(check spam too).",
    "mb_verify_btn": "Resend verification email",
    "mb_gmail_title": "Gmail in one click",
    "mb_gmail_body": "Connect Gmail without an app password — sign in with "
                     "Google and allow VORU to read your mailbox. You can "
                     "revoke access at any time at myaccount.google.com.",
    "mb_gmail_btn": "Connect Gmail with Google",
    "mb_none": "No mailbox yet — add your first one below.",
    "th_name": "Name", "th_server": "Server", "th_login": "Login",
    "mb_remove": "Remove", "mb_remove_confirm": "Remove this mailbox?",
    "mb_add_title": "Add a mailbox",
    "mb_add_lead": "Pick your provider — we'll fill in the server settings "
                   "for you. The login is verified right away. Step-by-step "
                   "guide: <a href='/navod' target='_blank'>connection "
                   "guide</a>.",
    "mb_where": "Where is your email hosted?",
    "mb_pick": "— pick a provider —",
    "mb_other_provider": "Other / custom domain",
    "mb_name_label": "Name (e.g. “mycompany”)",
    "mb_host_label": "IMAP server",
    "mb_port_label": "Port",
    "mb_user_label": "Login email",
    "mb_pass_label": "Mailbox password / app password",
    "mb_sec_label": "Security",
    "mb_sec_ssl": "SSL (standard, port 993)",
    "mb_sec_starttls": "STARTTLS (e.g. Proton Bridge)",
    "mb_sec_plain": "no encryption",
    "mb_submit": "Verify and add",
    "hint_gmail": "Gmail requires an <b>app password</b> (not your regular "
                  "password): turn on two-step verification and create one at "
                  "<a href='https://myaccount.google.com/apppasswords' "
                  "target='_blank' rel='noopener'>myaccount.google.com/"
                  "apppasswords</a>.",
    "hint_webmail": "Use your full email address and mailbox password (the "
                    "one you enter in webmail).",
    "hint_m365": "Microsoft 365: if sign-in fails, your admin needs to enable "
                 "IMAP and app passwords in the Microsoft 365 settings.",
    "hint_icloud": "iCloud requires an <b>app password</b>: create one at "
                   "<a href='https://account.apple.com' target='_blank' "
                   "rel='noopener'>account.apple.com</a> → Sign-In and "
                   "Security → App-Specific Passwords.",
    "hint_simple": "Use your full address and the password you sign in with.",
    "hint_other": "The server is usually <b>mail.yourdomain.com</b>, or you "
                  "can find it in your hosting provider's documentation "
                  "under “IMAP”. Not sure? Write to us at "
                  "<a href='mailto:obchod@sorbxt.sk'>"
                  "obchod@sorbxt.sk</a> — we'll help.",
    # settings
    "s_account_type": "Account type",
    "s_type_business": "business / sole trader",
    "s_type_personal": "private individual",
    "s_type_both": "both — business and personal",
    "s_reminder_to": "Where to send digests and alerts",
    "s_pdf": "Passwords for protected PDFs (bank statements) — separate "
             "multiple with commas",
    "s_pdf_ph": "e.g. your personal ID number (rodné číslo) or the password "
                "from your bank",
    "s_pdf_note": "The password is only used locally to unlock PDF "
                  "statements, so VORU can tick off paid payments "
                  "automatically.",
    "s_iban": "Your account IBAN (for the bulk payment order)",
    "s_name": "Company name / your name (appears on the order)",
    "s_name_ph": "My Company Ltd.",
    "s_remind": "Morning payment digest (with QR codes)",
    "s_workdays": "weekdays", "s_daily": "every day",
    "s_weekly": "Fridays only (weekly summary)", "s_off": "don't send",
    "s_at": "at {h}:00",
    "s_digest": "Incoming mail summary",
    "s_digest_note": "On Fridays you always get a summary of the whole week. "
                     "The email is only sent when there's something to say.",
    "s_report": "Monthly expense report (1st of the month)",
    "s_tax": "Tax calendar — what applies to you",
    "s_tax_note": "VORU reminds you of statutory deadlines (VAT, social and "
                  "health contributions, advance tax payments) in your "
                  "morning digests.",
    "s_save": "Save",
    "s_pw_title": "Change password",
    "s_pw_ok": "Your password has been changed.",
    "s_pw_old": "Current password",
    "s_pw_new": "New password (min. 8 characters)",
    "s_pw_btn": "Change password",
    "err_pw_old": "The current password is incorrect.",
    "err_pw_short": "The new password must be at least 8 characters long.",
    "s_totp_title": "Two-factor authentication (2FA)",
    "s_totp_on": "<b>Enabled.</b> <span class='muted'>Signing in requires a "
                 "code from your authenticator app in addition to your "
                 "password.</span>",
    "s_totp_off_pw": "Password (to confirm turning it off)",
    "s_totp_off_btn": "Turn off 2FA",
    "s_totp_step1": "1. Add this key to your authenticator app (Google "
                    "Authenticator, Aegis, 1Password…):",
    "s_totp_link": "or open this link on your phone:",
    "s_totp_add": "add to app",
    "s_totp_step2": "2. Enter the code from the app",
    "s_totp_on_btn": "Turn on 2FA",
    "s_totp_lead": "A second layer of account protection: signing in requires "
                   "a code from the app on your phone in addition to your "
                   "password. We recommend turning it on.",
    "err_totp_code": "That code is incorrect — try again.",
    "err_totp_pw": "Incorrect password.",
    "s_push_title": "Push notifications",
    "s_push_lead": "A morning alert about pending payments straight to your "
                   "phone — works once you install VORU to your home screen "
                   "(see Mobile app below).",
    "s_push_unsupported": "This browser doesn't support push notifications.",
    "s_push_nokeys": "The server doesn't have notification keys configured yet.",
    "s_push_on": "Turn on notifications", "s_push_off": "Turn off notifications",
    "s_push_active": "Notifications are enabled on this device.",
    "s_push_denied": "Couldn't turn on notifications (permission denied?).",
    "s_data_title": "Your data",
    "s_data_lead": "A complete export of your records (payments, tasks, mail "
                   "log, renewal watches) as CSV in a ZIP archive.",
    "s_data_btn": "Download data export",
    "s_del_title": "Delete account",
    "s_del_lead": "Permanently deletes your account and all data (mailboxes, "
                  "payments, tasks, files). If you need anything, download "
                  "your export first.",
    "s_del_pw": "Password (to confirm)",
    "s_del_btn": "Delete account and all data",
    "s_del_confirm": "Really delete your account and all data permanently?",
    "err_del_pw": "Incorrect password.",
    "s_app_title": "Mobile app",
    "s_app_lead": "Install VORU to your phone's home screen — it works like a "
                  "regular app, no App Store needed.",
    "s_app_ios": "<b>iPhone:</b> open voru.sk in Safari → the Share button "
                 "<span class='muted'>(square with an arrow)</span> → "
                 "<b>Add to Home Screen</b>.",
    "s_app_android": "<b>Android:</b> open voru.sk in Chrome → the ⋮ menu → "
                     "<b>Add to Home screen / Install app</b>.",
    # subscription
    "b_status": "Account status:",
    "b_active": "active subscription",
    "b_trial": "trial until {date}",
    "b_inactive": "inactive",
    "b_pick": "Pick a plan — payment is handled securely by Stripe:",
    "b_monthly": "€4.99 / month",
    "b_yearly": "€49 / year — 2 months free",
    "b_auto": "After payment your account activates automatically within a "
              "minute.",
    "b_manual": "Our payment gateway is on its way — write to us at "
                "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a> "
                "and we'll activate you manually.",
    "b_thanks": "Thank you for using VORU. To cancel your subscription: use "
                "the link in your Stripe confirmation, or write to us at "
                "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a>.",
    "b_ref_title": "Recommend VORU — get a month free",
    "b_ref_lead": "For each person who signs up through your link, you get "
                  "<b>+30 days</b> of service for free — and the new user "
                  "gets an extra <b>+14 days</b> of trial.",
    "b_ref_count": "Sign-ups through your link so far:",
    # forgotten password / reset
    "fp_title": "Forgot your password?",
    "fp_lead": "We'll email you a link to set a new password.",
    "fp_email": "Account email",
    "fp_btn": "Send link",
    "fp_back": "Back to sign-in",
    "fp_sent_title": "Email sent",
    "fp_sent_body": "If the account exists, we've sent it a password reset "
                    "link. Check your inbox (and spam).",
    "rp_title": "Set a new password",
    "rp_pw": "New password (min. 8 characters)",
    "rp_btn": "Save password",
    "rp_invalid_title": "Invalid link",
    "rp_invalid_body": "The password reset link has expired or is broken — "
                       "request a new one.",
    "rp_done_title": "Password changed",
    "rp_done_body": "Sign in with your new password.",
    "reset_mail_subject": "VORU — password reset",
    "reset_mail_title": "Password reset",
    "reset_mail_lead": "Click to set a new password (the link is valid for "
                       "2 hours):",
    "reset_mail_btn": "Set new password",
    "reset_mail_ignore": "If you didn't request a reset, just ignore this "
                         "email.",
    "reset_mail_pre": "The link to set a new password is valid for 2 hours.",
    # email verification / system pages
    "v_ok_title": "Email verified",
    "v_ok_body": "Thank you, your address is confirmed. Mailboxes and "
                 "digests are unlocked.",
    "v_bad_title": "Invalid link",
    "v_bad_body": "The verification link is broken or has expired. Sign in "
                  "and request a new one.",
    "v_gate_title": "Confirm your email first",
    "v_gate_body": "Connecting a mailbox unlocks once you confirm your email "
                   "address — click the link in the welcome email. You can "
                   "request a new link with the button on the overview.",
    "v_gate_cta": "Back to overview",
    "login_cta": "Sign in",
    "home_cta": "Go to overview",
    # action pages (one click from email)
    "a_title": "Confirmation",
    "a_invalid_title": "Invalid link",
    "a_invalid_body": "The link is broken or incomplete. Open it again from "
                      "the email, or handle the item after signing in on "
                      "the overview.",
    "a_done_title": "Done",
    "a_done_count": ("We marked {n} payment as paid.",
                     "We marked {n} payments as paid.",
                     "We marked {n} payments as paid."),
    "a_done_single": "Done — “{label}” completed successfully.",
    "a_already_title": "Already done",
    "a_already_bulk": "There was nothing to mark — either nothing was "
                      "selected, or the selected payments have been paid in "
                      "the meantime.",
    "a_already_single": "This item has changed state in the meantime — you "
                        "probably ticked it off already, or it was matched "
                        "by a bank statement.",
    "a_confirm_q": "Really {label}?",
    "a_bulk_q": "Really {label}? Untick the payments that haven't been "
                "paid yet.",
    "a_bulk_empty": "You have no unpaid payments right now.",
    "a_bulk_btn": "Mark selected as paid",
    "a_no_due": "no due date",
    "a_yes": "Yes, confirm",
    "a_safe": "If you didn't open this link yourself, simply close the "
              "page — nothing will happen.",
    "a_label_paid": "mark the payment as paid",
    "a_label_snooze": "snooze the reminder for 3 days",
    "a_label_done": "mark the task as done",
    "a_label_bulk": "mark the selected payments as paid",
    # SEPA
    "sepa_missing_title": "Your IBAN is missing",
    "sepa_missing_body": "The bulk payment order needs the IBAN of the "
                         "account the payments will be made from.",
    "sepa_missing_cta": "Add it in Settings",
}

# kľúče doplnené po prvom preklade (systémové hlášky)
APP.update({
    "sepa_empty_title": "Nothing to pay",
    "sepa_empty_body": "No unpaid payment with an IBAN in EUR.",
    "g_fail_title": "Connecting Gmail failed",
    "g_fail_auth": "The Google sign-in was interrupted or expired. "
                   "Please try again.",
    "g_fail_token": "Google did not return access credentials. "
                    "Please try again.",
    "mb_back": "Back to mailboxes",
    "mb_conn_fail": "Connection failed: {err}",
    "rp_new_btn": "Request a new one",
    "rp_err": "The link has expired or the password is shorter than "
              "8 characters.",
    "s_del_done_title": "Account deleted",
    "s_del_done_body": "We have deleted your account and all data. "
                       "Thank you for trying VORU.",
})
APP["back_btn"] = "Back"

# trial-ending emails
APP.update({
    "trial_mail_subject_warn": "VORU — your trial ends on {date}",
    "trial_mail_subject_end": "VORU — your trial has ended",
    "trial_mail_warn_title": "Your trial is ending soon",
    "trial_mail_warn_lead": "Your trial ends on {date}. To keep VORU tracking "
                            "your invoices, payments and deadlines, activate "
                            "a subscription — €4.99 a month or €49 a year "
                            "(2 months free).",
    "trial_mail_end_title": "Your trial has ended",
    "trial_mail_end_lead": "Your trial ended today and the service is paused — "
                           "digests and reminders are not being sent for now. "
                           "All your data is kept safe; subscribing brings it "
                           "back instantly.",
    "trial_mail_btn": "Activate subscription",
    "trial_mail_footer": "Questions? Just reply to this email.",
})

# app language + calendar feed
APP.update({
    "s_lang": "Language of the app and emails",
    "s_cal_title": "Deadline calendar",
    "s_cal_lead": "Add this link to your calendar and due dates, tax "
                  "deadlines and expiry dates will show up right in it. "
                  "The link is private — don't share it.",
    "s_cal_how": "Google Calendar: Other calendars → + → From URL. "
                 "Apple Calendar: File → New Calendar Subscription.",
    "ics_cal_name": "VORU — payments and deadlines",
    "ics_pay": "Pay: {s}",
})

# prihlásenie cez Google
APP.update({
    "g_login_btn": "Continue with Google",
    "g_login_or": "or",
    "g_login_fail_title": "Google sign-in failed",
    "g_login_fail_body": "Please try again or use email and password.",
})
