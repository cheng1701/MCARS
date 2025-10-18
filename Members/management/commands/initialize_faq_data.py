from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from Members.models import FAQCategory, FAQ

class Command(BaseCommand):
    help = 'Initialize FAQ categories and questions from the default template'

    def handle(self, *args, **options):
        # Get admin user for attribution
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.WARNING('No admin user found. Creating FAQs without attribution.'))

        # Create categories
        categories = [
            {'name': 'General Questions', 'order': 1},
            {'name': 'Membership', 'order': 2},
            {'name': 'Payment & Billing', 'order': 3},
            {'name': 'Family Memberships', 'order': 4},
            {'name': 'Account Management', 'order': 5},
            {'name': 'Technical Support', 'order': 6},
        ]

        created_categories = {}
        for cat in categories:
            category, created = FAQCategory.objects.get_or_create(
                name=cat['name'],
                defaults={'order': cat['order']}
            )
            created_categories[cat['name']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {category.name}'))

        # Create FAQs
        faqs = [
            # General Questions
            {
                'category': 'General Questions',
                'question': 'What is the Federation\'s MCARS Portal?',
                'answer': '<p>The MCARS (Membership Club Administration and Registration System) Portal is our organization\'s dedicated platform for managing memberships, providing member services, and facilitating community engagement. It allows members to access exclusive benefits, manage their profiles, track payments, and much more.</p>',
                'order': 1
            },
            {
                'category': 'General Questions',
                'question': 'Who can join the Federation\'s MCARS Portal?',
                'answer': '<p>Our membership is open to anyone interested in our organization\'s mission and activities. We offer various membership tiers to accommodate different needs and preferences, including individual and family plans.</p>',
                'order': 2
            },
            {
                'category': 'General Questions',
                'question': 'What benefits do members receive?',
                'answer': '<p>Our members enjoy numerous benefits including:</p><ul><li>Access to exclusive events and services</li><li>Special discounts with our partners</li><li>Networking opportunities with other members</li><li>Regular newsletters and updates</li><li>Voting rights on important organizational matters</li><li>Access to member-only resources and content</li></ul><p>Benefits vary by membership type. See our Membership Plans page for detailed information.</p>',
                'order': 3
            },

            # Membership
            {
                'category': 'Membership',
                'question': 'What membership plans do you offer?',
                'answer': '<p>We offer several membership tiers to suit different needs including individual, family, and premium plans. Each plan has different benefits and pricing. Visit our Membership Plans page for more details about each plan.</p>',
                'order': 1
            },
            {
                'category': 'Membership',
                'question': 'How long does membership approval take?',
                'answer': '<p>After registration, membership applications typically go through an approval process that takes 1-2 business days. You\'ll receive an email notification once your membership has been approved.</p>',
                'order': 2
            },
            {
                'category': 'Membership',
                'question': 'Can I upgrade or downgrade my membership plan?',
                'answer': '<p>Yes, you can change your membership plan at any time. Simply log in to your account, go to the Subscription Management section, and select a new plan. If upgrading, you\'ll be charged the prorated difference. If downgrading, the change will take effect at the end of your current billing cycle.</p>',
                'order': 3
            },
            {
                'category': 'Membership',
                'question': 'How do I renew my membership?',
                'answer': '<p>For monthly and yearly plans, memberships renew automatically unless canceled. Lifetime memberships never expire. If you\'ve canceled previously and wish to renew, simply log in and visit the Subscription Management section to reactivate your membership.</p>',
                'order': 4
            },

            # Payment & Billing
            {
                'category': 'Payment & Billing',
                'question': 'What payment methods do you accept?',
                'answer': '<p>We accept all major credit cards (Visa, MasterCard, American Express, Discover) and PayPal for online payments. For annual plans, we also offer options for checks or bank transfers. Contact our billing department for more information.</p>',
                'order': 1
            },
            {
                'category': 'Payment & Billing',
                'question': 'Is my payment information secure?',
                'answer': '<p>Yes, we take security seriously. We use industry-standard encryption and secure payment processors. We do not store your complete credit card information on our servers. All transactions are processed through secure, PCI-compliant systems.</p>',
                'order': 2
            },
            {
                'category': 'Payment & Billing',
                'question': 'Can I get a refund if I\'m not satisfied?',
                'answer': '<p>We offer a 30-day money-back guarantee for new members who are dissatisfied with our services. After this period, refunds are considered on a case-by-case basis. Lifetime memberships have a 60-day refund policy. Please contact our support team to request a refund.</p>',
                'order': 3
            },
            {
                'category': 'Payment & Billing',
                'question': 'How can I view my payment history?',
                'answer': '<p>You can view your complete payment history by logging into your account and navigating to the "Payment History" section in your member dashboard. From there, you can also download receipts for your records.</p>',
                'order': 4
            },

            # Family Memberships
            {
                'category': 'Family Memberships',
                'question': 'What is included in a family membership?',
                'answer': '<p>Family memberships cover one primary member and their immediate family members (spouse/partner and children under 18). All family members receive membership benefits, can participate in events, and have access to member-only resources.</p>',
                'order': 1
            },
            {
                'category': 'Family Memberships',
                'question': 'How do I add family members to my account?',
                'answer': '<p>Once you have a family membership, you can add family members by logging into your account and navigating to the "Family Management" section. Click "Add Child" and fill out the required information. There is no limit to the number of children you can add to a family membership.</p>',
                'order': 2
            },
            {
                'category': 'Family Memberships',
                'question': 'Can my children access the member portal?',
                'answer': '<p>Children under 18 do not receive separate login credentials. The primary account holder manages all family members through their account. When children turn 18, they can create their own individual membership if desired.</p>',
                'order': 3
            },

            # Account Management
            {
                'category': 'Account Management',
                'question': 'How do I update my personal information?',
                'answer': '<p>You can update your personal information by logging into your account and clicking on "Profile" in your dashboard. From there, select "Edit Profile" to update your name, email, phone number, and address information.</p>',
                'order': 1
            },
            {
                'category': 'Account Management',
                'question': 'I forgot my password. How do I reset it?',
                'answer': '<p>If you forget your password, click on the "Forgot Password" link on the login page. Enter your email address, and we\'ll send you instructions to reset your password. If you don\'t receive the email, check your spam folder or contact support.</p>',
                'order': 2
            },
            {
                'category': 'Account Management',
                'question': 'How do I cancel my membership?',
                'answer': '<p>To cancel your membership, log into your account and go to "Subscription Management." Click on "Cancel Membership" and follow the instructions. Please note that cancellations take effect at the end of your current billing cycle, and no partial refunds are provided for unused portions of a payment period.</p>',
                'order': 3
            },
            {
                'category': 'Account Management',
                'question': 'Can I change my username or email address?',
                'answer': '<p>You can change your email address in your profile settings. However, usernames cannot be changed once created. If you need to use a different username, you would need to create a new account. Contact support if you need assistance transferring your membership to a new account.</p>',
                'order': 4
            },

            # Technical Support
            {
                'category': 'Technical Support',
                'question': 'What browsers are supported?',
                'answer': '<p>Our portal supports all modern browsers, including the latest versions of Chrome, Firefox, Safari, and Edge. For the best experience, we recommend keeping your browser updated to the latest version.</p>',
                'order': 1
            },
            {
                'category': 'Technical Support',
                'question': 'The site isn\'t working properly. What should I do?',
                'answer': '<p>If you\'re experiencing technical issues:</p><ol><li>Clear your browser cache and cookies</li><li>Try using a different browser</li><li>Check if your internet connection is stable</li><li>If the problem persists, contact our technical support with details about the issue, including screenshots if possible</li></ol>',
                'order': 2
            },
            {
                'category': 'Technical Support',
                'question': 'How do I report a bug or suggest a feature?',
                'answer': '<p>We welcome feedback from our members! To report a bug or suggest a feature, please use the Contact Us form and select "Bug Report" or "Feature Suggestion" from the subject dropdown. Include as much detail as possible to help us understand your feedback.</p>',
                'order': 3
            },
        ]

        # Create FAQs
        for faq_data in faqs:
            category = created_categories[faq_data['category']]
            faq, created = FAQ.objects.get_or_create(
                category=category,
                question=faq_data['question'],
                defaults={
                    'answer': faq_data['answer'],
                    'order': faq_data['order'],
                    'is_active': True,
                    'created_by': admin,
                    'updated_by': admin
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created FAQ: {faq.question}'))
            else:
                self.stdout.write(self.style.WARNING(f'FAQ already exists: {faq.question}'))

        self.stdout.write(self.style.SUCCESS('FAQ initialization complete'))
