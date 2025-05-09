import logging
import os
from email.mime.image import MIMEImage
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_email(subject, recipients, template_name, context, attachments=None, from_email=None):
    """
    Send an email to one or more recipients using a template.
    
    Args:
        subject (str): Email subject
        recipients (list): List of email addresses to send to
        template_name (str): Name of the HTML template to render
        context (dict): Context data for the template
        attachments (list, optional): List of file paths to attach
        from_email (str, optional): Override the default from email address
    
    Returns:
        bool: True if successful, False otherwise
    """
    if from_email is None:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'ko.youssef.public@gmail.com')
    
    # Render the HTML content from template
    html_content = render_to_string(f'emails/{template_name}.html', context)
    # Create plain text version by stripping HTML
    text_content = strip_tags(html_content)
    
    # Create the email message
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipients,
    )
    
    # Attach HTML version
    email.attach_alternative(html_content, "text/html")
    
    # Add any attachments
    if attachments:
        for file_path in attachments:
            email.attach_file(file_path)
    
    # Try to send the email
    try:
        email.send()
        logger.info(f"Email '{subject}' sent to {', '.join(recipients)}")
        return True
    except SMTPException as e:
        logger.error(f"Failed to send email '{subject}': {str(e)}")
        return False


def send_newsletter(newsletter, recipients=None):
    """
    Send a newsletter to a list of recipients.
    
    Args:
        newsletter: Newsletter object containing content and metadata
        recipients (list, optional): List of email addresses to send to.
                                    If None, uses newsletter.recipients
    
    Returns:
        dict: A summary of the sending operation with success and failure counts
    """
    if recipients is None:
        recipients = newsletter.recipients
    
    context = {
        'title': newsletter.title,
        'content': newsletter.content,
        'author': newsletter.author,
        'publication_date': newsletter.publication_date,
        'issue_number': newsletter.issue_number,
        'site_url': settings.SITE_URL,
    }
    
    # Track success and failure
    results = {
        'success': 0,
        'failure': 0,
        'total': len(recipients)
    }
    
    # Send in batches to avoid server limits
    batch_size = getattr(settings, 'EMAIL_BATCH_SIZE', 50)
    
    # Get connection to reuse
    connection = get_connection()
    connection.open()
    
    for i in range(0, len(recipients), batch_size):
        batch = recipients[i:i+batch_size]
        
        # Create individual messages for each recipient
        messages = []
        for recipient in batch:
            email = EmailMultiAlternatives(
                subject=newsletter.title,
                body=strip_tags(newsletter.content),
                from_email=getattr(settings, 'NEWSLETTER_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                to=[recipient],
                connection=connection,
            )
            
            # Render HTML with context
            html_content = render_to_string('emails/newsletter_template.html', context)
            email.attach_alternative(html_content, "text/html")
            
            # Add embedded images if present
            if newsletter.featured_image:
                with open(newsletter.featured_image.path, 'rb') as img:
                    image = MIMEImage(img.read())
                    image.add_header('Content-ID', f'<{os.path.basename(newsletter.featured_image.name)}>')
                    email.attach(image)
            
            messages.append(email)
        
        # Send all emails in the batch
        try:
            connection.send_messages(messages)
            results['success'] += len(batch)
            logger.info(f"Sent newsletter '{newsletter.title}' to {len(batch)} recipients")
        except Exception as e:
            results['failure'] += len(batch)
            logger.error(f"Failed to send newsletter batch: {str(e)}")
    
    connection.close()
    return results


def send_notification_to_author(article, notification_type):
    """
    Send a notification email to an article author.
    
    Args:
        article: The article object
        notification_type (str): Type of notification (published, feedback, etc.)
    
    Returns:
        bool: True if successful, False otherwise
    """
    author_email = article.author.email
    
    context = {
        'article_title': article.title,
        'article_url': f"{settings.SITE_URL}/news/{article.slug}/",
        'author_name': article.author.get_full_name() or article.author.username,
    }
    
    subject_templates = {
        'published': "Your article has been published",
        'feedback': "You've received feedback on your article",
        'featured': "Your article has been featured!",
        'milestone': "Your article reached a milestone!"
    }
    
    template_names = {
        'published': 'author_article_published',
        'feedback': 'author_article_feedback',
        'featured': 'author_article_featured',
        'milestone': 'author_article_milestone'
    }
    
    # Add type-specific context
    if notification_type == 'feedback':
        context['feedback_count'] = article.feedback_set.count()
    elif notification_type == 'milestone':
        context['views_count'] = article.views_count
        context['milestone'] = f"{article.views_count//1000}K" if article.views_count >= 1000 else article.views_count
    
    return send_email(
        subject=subject_templates.get(notification_type, "Update on your article"),
        recipients=[author_email],
        template_name=template_names.get(notification_type, 'author_notification'),
        context=context
    )


def send_feedback_response(feedback, response_text):
    """
    Send a response to someone who provided feedback on an article.
    
    Args:
        feedback: The feedback object
        response_text (str): The response text
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not feedback.email:
        logger.warning("Can't send feedback response - no email provided")
        return False
    
    context = {
        'feedback_text': feedback.text,
        'response_text': response_text,
        'article_title': feedback.article.title,
        'article_url': f"{settings.SITE_URL}/articles/{feedback.article.slug}/",
    }
    
    return send_email(
        subject=f"Response to your feedback on '{feedback.article.title}'",
        recipients=[feedback.email],
        template_name='feedback_response',
        context=context
    )


def send_bulk_announcement(subject, content, recipient_list):
    """
    Send a bulk announcement to a list of recipients.
    
    Args:
        subject (str): Email subject
        content (str): Email content (HTML supported)
        recipient_list (list): List of recipient email addresses
    
    Returns:
        dict: Summary of success and failure counts
    """
    context = {
        'subject': subject,
        'content': content,
        'site_url': settings.SITE_URL,
        'current_year': timezone.now().year
    }
    
    results = {
        'success': 0,
        'failure': 0,
        'total': len(recipient_list)
    }
    
    # Send in batches to avoid hitting limits
    batch_size = getattr(settings, 'EMAIL_BATCH_SIZE', 100)
    
    with get_connection() as connection:
        for i in range(0, len(recipient_list), batch_size):
            batch = recipient_list[i:i+batch_size]
            
            try:
                # Create email message with both plain text and HTML
                html_content = render_to_string('emails/announcement.html', context)
                text_content = strip_tags(html_content)
                
                # Create message
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=getattr(settings, 'ANNOUNCEMENT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    to=[],  # Empty to list since we're using BCC
                    bcc=batch,
                    connection=connection,
                )
                
                email.attach_alternative(html_content, "text/html")
                email.send()
                
                results['success'] += len(batch)
                logger.info(f"Sent announcement to batch of {len(batch)} recipients")
            except Exception as e:
                results['failure'] += len(batch)
                logger.error(f"Failed to send announcement batch: {str(e)}")
    
    return results


def prepare_article_digest(articles, recipient_email):
    """
    Prepare an email digest of recent articles.
    
    Args:
        articles (list): List of article objects
        recipient_email (str): Recipient's email address
    
    Returns:
        EmailMultiAlternatives: Prepared email message ready to send
    """
    context = {
        'articles': articles,
        'site_url': settings.SITE_URL,
        'unsubscribe_url': f"{settings.SITE_URL}/unsubscribe/?email={recipient_email}",
    }
    
    html_content = render_to_string('emails/article_digest.html', context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject="Your Weekly Article Digest",
        body=text_content,
        from_email=getattr(settings, 'DIGEST_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
        to=[recipient_email],
    )
    
    email.attach_alternative(html_content, "text/html")
    return email


def send_welcome_email(email_address, name=None):
    """
    Send a welcome email to a new reader.
    
    Args:
        email_address (str): Recipient's email address
        name (str, optional): Recipient's name
    
    Returns:
        bool: True if successful, False otherwise
    """
    context = {
        'name': name or 'Reader',
        'site_url': settings.SITE_URL,
    }
    
    return send_email(
        subject="Welcome to our Student Newsletter!",
        recipients=[email_address],
        template_name='welcome_email',
        context=context
    )


def send_contact_form_confirmation(contact_form_data):
    """
    Send confirmation email after someone submits a contact form.
    
    Args:
        contact_form_data (dict): Form data including email, name, and message
    
    Returns:
        bool: True if successful, False otherwise
    """
    context = {
        'name': contact_form_data.get('name', 'there'),
        'message': contact_form_data.get('message', ''),
        'site_url': settings.SITE_URL,
    }
    
    return send_email(
        subject="We've received your message",
        recipients=[contact_form_data['email']],
        template_name='contact_form_confirmation',
        context=context
    )


def forward_contact_form_to_admin(contact_form_data):
    """
    Forward contact form submission to site administrators.
    
    Args:
        contact_form_data (dict): Form data including email, name, and message
    
    Returns:
        bool: True if successful, False otherwise
    """
    admin_emails = getattr(settings, 'ADMIN_EMAILS', [settings.DEFAULT_FROM_EMAIL])
    
    context = {
        'name': contact_form_data.get('name', 'Anonymous'),
        'email': contact_form_data.get('email', 'No email provided'),
        'message': contact_form_data.get('message', 'No message'),
        'submit_time': timezone.now(),
    }
    
    return send_email(
        subject="New Contact Form Submission",
        recipients=admin_emails,
        template_name='admin_contact_form',
        context=context
    )