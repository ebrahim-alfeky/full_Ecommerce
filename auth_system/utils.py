import random
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from .models import Code  # تأكد المسار صحيح
CODE_EXPIRY_MINUTES = 1  # غير الرقم لو عايز

def generate_and_store_code(user, purpose):
    code = f"{random.randint(0, 999999):06d}"
    expires_at = timezone.now() + timedelta(minutes=CODE_EXPIRY_MINUTES)
    Code.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=expires_at
    )
    return code

def send_code_email(email, code, purpose):
    """
    إرسال الكود لأي غرض:
    - purpose: 'verify_email', 'reset_password', 'change_email', ...
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    # تحديد عنوان الإيميل حسب الغرض
    if purpose == 'verify_email':
        subject = "🔐 Email Verification Code"
        message_intro = "Use the verification code below to verify your email address."
    elif purpose == 'reset_password':
        subject = "🔑 Password Reset Code"
        message_intro = "Use the code below to reset your password."
    elif purpose == 'change_email':
        subject = "📧 Change Email Verification Code"
        message_intro = "Use the code below to confirm your new email address."
    else:
        subject = "🔔 Your Verification Code"
        message_intro = "Use the code below for the requested action."

    # نص plain text
    text_content = f"""
{message_intro}
Your code is: {code}
It will expire in {CODE_EXPIRY_MINUTES} minutes.
"""

    # HTML
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 30px;">
            <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="color: #333; text-align: center;">{subject}</h2>
                <p style="font-size: 16px; color: #555; text-align: center;">
                    {message_intro}
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <span style="
                        display: inline-block;
                        background-color: #007bff;
                        color: white;
                        font-size: 24px;
                        letter-spacing: 3px;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-weight: bold;
                    ">
                        {code}
                    </span>
                </div>

                <p style="color: #777; text-align: center;">
                    ⚠️ This code will expire in <strong>{CODE_EXPIRY_MINUTES} minute(s)</strong>.
                </p>

                <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
                <p style="font-size: 13px; color: #999; text-align: center;">
                    If you didn’t request this, you can safely ignore this email.
                </p>
            </div>
        </body>
    </html>
    """

    # إرسال الإيميل
    email_msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email_msg.attach_alternative(html_content, "text/html")
    email_msg.send()

def verify_code(user, code, purpose):
    try:
        code_obj = Code.objects.get(user=user, code=code, purpose=purpose)
    except Code.DoesNotExist:
        return False

    # تحقق من الصلاحية
    if timezone.now() > code_obj.expires_at:
        code_obj.delete()  # حذف الكود منتهي الصلاحية
        return False

    # الكود صالح → نحذف الكود
    code_obj.delete()
    return True

