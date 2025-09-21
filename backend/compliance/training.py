"""
Compliance Training Module for HIPAA/GDPR

This module provides comprehensive training materials and tracking
for healthcare regulatory compliance requirements.

Features:
- HIPAA compliance training modules
- GDPR compliance training modules
- Training completion tracking
- Quiz and assessment systems
- Training content management
- Certification generation
- Training analytics and reporting
"""

from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import pdfkit
import xlsxwriter
from io import BytesIO
import base64

# Set up logging
logger = logging.getLogger(__name__)
User = get_user_model()


class TrainingModuleType(Enum):
    """Training module types"""
    HIPAA_AWARENESS = "hipaa_awareness"
    HIPAA_SECURITY = "hipaa_security"
    HIPAA_PRIVACY = "hipaa_privacy"
    GDPR_AWARENESS = "gdpr_awareness"
    GDPR_DATA_SUBJECT_RIGHTS = "gdpr_data_subject_rights"
    GDPR_CONSENT_MANAGEMENT = "gdpr_consent_management"
    SECURITY_BEST_PRACTICES = "security_best_practices"
    INCIDENT_RESPONSE = "incident_response"
    BREACH_NOTIFICATION = "breach_notification"


class TrainingDifficulty(Enum):
    """Training difficulty levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TrainingStatus(Enum):
    """Training status types"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class TrainingModule(models.Model):
    """
    Training module model for compliance training
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Basic information
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    description = models.TextField(verbose_name=_("Description"))
    module_type = models.CharField(
        max_length=50,
        choices=[(t.value, t.name.replace('_', ' ').title()) for t in TrainingModuleType],
        verbose_name=_("Module Type")
    )
    difficulty = models.CharField(
        max_length=20,
        choices=[(d.value, d.name.title()) for d in TrainingDifficulty],
        default=TrainingDifficulty.BASIC.value,
        verbose_name=_("Difficulty")
    )

    # Content
    content = models.JSONField(verbose_name=_("Training Content"), help_text=_("Structured training content"))
    duration_minutes = models.PositiveIntegerField(
        verbose_name=_("Duration (minutes)"),
        help_text=_("Estimated time to complete training")
    )

    # Requirements
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_modules',
        verbose_name=_("Prerequisites")
    )

    # Target audience
    target_roles = models.JSONField(
        default=list,
        verbose_name=_("Target Roles"),
        help_text=_("Roles that should complete this training")
    )

    # Configuration
    is_mandatory = models.BooleanField(default=True, verbose_name=_("Is Mandatory"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    version = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    valid_days = models.PositiveIntegerField(
        default=365,
        verbose_name=_("Valid Days"),
        help_text=_("Number of days training certificate is valid")
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_training_modules',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Training Module")
        verbose_name_plural = _("Training Modules")
        ordering = ['module_type', 'difficulty', 'title']
        indexes = [
            models.Index(fields=['module_type', 'is_active']),
            models.Index(fields=['difficulty', 'is_mandatory']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_module_type_display()})"

    def get_absolute_url(self):
        return reverse('compliance:training_module_detail', kwargs={'pk': self.pk})

    def is_required_for_role(self, user_role: str) -> bool:
        """Check if training is required for a specific role"""
        if not self.target_roles:
            return self.is_mandatory

        return user_role in self.target_roles

    def get_next_content_item(self, user) -> Optional[Dict[str, Any]]:
        """Get the next content item for a user"""
        user_progress = TrainingProgress.objects.filter(
            user=user,
            training_module=self
        ).first()

        if not user_progress:
            return self.content[0] if self.content else None

        completed_items = user_progress.completed_content_items or []
        content_index = len(completed_items)

        if content_index < len(self.content):
            return self.content[content_index]

        return None

    def calculate_completion_percentage(self, user) -> float:
        """Calculate completion percentage for a user"""
        if not self.content:
            return 0.0

        user_progress = TrainingProgress.objects.filter(
            user=user,
            training_module=self
        ).first()

        if not user_progress:
            return 0.0

        completed_items = len(user_progress.completed_content_items or [])
        total_items = len(self.content)

        return (completed_items / total_items * 100) if total_items > 0 else 0.0


class TrainingProgress(models.Model):
    """
    User training progress tracking model
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='training_progress',
        verbose_name=_("User")
    )
    training_module = models.ForeignKey(
        TrainingModule,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name=_("Training Module")
    )

    # Progress tracking
    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.name.replace('_', ' ').title()) for s in TrainingStatus],
        default=TrainingStatus.NOT_STARTED.value,
        verbose_name=_("Status")
    )

    # Content progress
    current_content_index = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Current Content Index")
    )
    completed_content_items = models.JSONField(
        default=list,
        verbose_name=_("Completed Content Items"),
        help_text=_("List of completed content item IDs")
    )

    # Quiz results
    quiz_scores = models.JSONField(
        default=list,
        verbose_name=_("Quiz Scores"),
        help_text=_("List of quiz attempt scores")
    )

    # Time tracking
    started_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Started At"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Completed At"))
    time_spent_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Time Spent (minutes)")
    )

    # Certification
    certificate_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Certificate Number")
    )
    certificate_url = models.URLField(
        blank=True,
        verbose_name=_("Certificate URL")
    )

    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Expires At"))

    # Metadata
    last_accessed_at = models.DateTimeField(auto_now=True, verbose_name=_("Last Accessed At"))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("IP Address"))
    user_agent = models.TextField(blank=True, verbose_name=_("User Agent"))

    class Meta:
        verbose_name = _("Training Progress")
        verbose_name_plural = _("Training Progress Records")
        ordering = ['-last_accessed_at']
        unique_together = ['user', 'training_module']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['training_module', 'status']),
            models.Index(fields=['completed_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.training_module.title}"

    def update_progress(self, content_item_id: str, time_spent: int = 0):
        """Update training progress for a content item"""
        if not self.started_at:
            self.started_at = timezone.now()

        if content_item_id not in (self.completed_content_items or []):
            self.completed_content_items.append(content_item_id)
            self.current_content_index = len(self.completed_content_items)
            self.time_spent_minutes += time_spent

        # Check if training is completed
        completion_percentage = self.training_module.calculate_completion_percentage(self.user)
        if completion_percentage >= 100 and self.status != TrainingStatus.COMPLETED.value:
            self.mark_completed()

        self.save()

    def mark_completed(self):
        """Mark training as completed"""
        self.status = TrainingStatus.COMPLETED.value
        self.completed_at = timezone.now()

        # Set expiration date
        if self.training_module.valid_days:
            self.expires_at = self.completed_at + timedelta(days=self.training_module.valid_days)

        # Generate certificate
        self.certificate_number = f"TRN-{self.user.id}-{self.training_module.id}-{int(self.completed_at.timestamp())}"
        self.save()

    def is_expired(self) -> bool:
        """Check if training certificate has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def get_certificate_url(self) -> str:
        """Generate certificate URL"""
        if not self.certificate_number:
            return ""

        return reverse('compliance:training_certificate', kwargs={
            'certificate_number': self.certificate_number
        })


class TrainingQuiz(models.Model):
    """
    Training quiz model for knowledge assessment
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Relationships
    training_module = models.ForeignKey(
        TrainingModule,
        on_delete=models.CASCADE,
        related_name='quizzes',
        verbose_name=_("Training Module")
    )

    # Basic information
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    # Configuration
    passing_score = models.PositiveIntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Passing Score (%)")
    )
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Time Limit (minutes)")
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Maximum Attempts")
    )
    shuffle_questions = models.BooleanField(default=True, verbose_name=_("Shuffle Questions"))

    # Questions (stored as JSON for flexibility)
    questions = models.JSONField(
        verbose_name=_("Questions"),
        help_text=_("Quiz questions with answers and explanations")
    )

    # Metadata
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Training Quiz")
        verbose_name_plural = _("Training Quizzes")
        ordering = ['training_module', 'created_at']
        indexes = [
            models.Index(fields=['training_module', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} - {self.training_module.title}"

    def get_shuffled_questions(self) -> List[Dict[str, Any]]:
        """Get questions in random order if shuffling is enabled"""
        questions = self.questions.copy()

        if self.shuffle_questions:
            import random
            random.shuffle(questions)

        return questions


class QuizAttempt(models.Model):
    """
    Quiz attempt tracking model
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name=_("User")
    )
    quiz = models.ForeignKey(
        TrainingQuiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_("Quiz")
    )
    training_progress = models.ForeignKey(
        TrainingProgress,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name=_("Training Progress")
    )

    # Attempt information
    attempt_number = models.PositiveIntegerField(verbose_name=_("Attempt Number"))
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Started At"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Completed At"))

    # Results
    score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Score (%)")
    )
    passed = models.BooleanField(null=True, blank=True, verbose_name=_("Passed"))

    # Answers
    answers = models.JSONField(
        verbose_name=_("Answers"),
        help_text=_("User's quiz answers")
    )

    # Time tracking
    time_spent_seconds = models.PositiveIntegerField(default=0, verbose_name=_("Time Spent (seconds)"))

    class Meta:
        verbose_name = _("Quiz Attempt")
        verbose_name_plural = _("Quiz Attempts")
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'quiz']),
            models.Index(fields=['training_progress']),
            models.Index(fields=['completed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} (Attempt {self.attempt_number})"

    def calculate_score(self) -> Tuple[int, bool]:
        """Calculate quiz score and determine if passed"""
        if not self.answers or not self.quiz.questions:
            return 0, False

        correct_answers = 0
        total_questions = len(self.quiz.questions)

        for question in self.quiz.questions:
            question_id = question.get('id')
            user_answer = self.answers.get(str(question_id))
            correct_answer = question.get('correct_answer')

            if user_answer == correct_answer:
                correct_answers += 1

        score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
        passed = score >= self.quiz.passing_score

        return score, passed

    def complete_attempt(self):
        """Complete the quiz attempt and calculate score"""
        self.completed_at = timezone.now()
        self.score, self.passed = self.calculate_score()

        # Update training progress
        if self.training_progress:
            self.training_progress.quiz_scores.append({
                'quiz_id': self.quiz.id,
                'score': self.score,
                'passed': self.passed,
                'attempt_number': self.attempt_number,
                'completed_at': self.completed_at.isoformat()
            })
            self.training_progress.save()

        self.save()


class TrainingContentService:
    """
    Service for managing training content and materials
    """

    def __init__(self):
        self.default_training_modules = self._create_default_training_modules()

    def _create_default_training_modules(self) -> List[Dict[str, Any]]:
        """Create default training modules"""
        return [
            {
                'module_type': TrainingModuleType.HIPAA_AWARENESS.value,
                'title': 'HIPAA Awareness Training',
                'description': 'Comprehensive overview of HIPAA regulations and requirements for healthcare professionals',
                'difficulty': TrainingDifficulty.BASIC.value,
                'duration_minutes': 45,
                'target_roles': ['doctor', 'nurse', 'admin', 'staff'],
                'content': self._get_hipaa_awareness_content()
            },
            {
                'module_type': TrainingModuleType.HIPAA_SECURITY.value,
                'title': 'HIPAA Security Rule Training',
                'description': 'Technical and administrative safeguards required by the HIPAA Security Rule',
                'difficulty': TrainingDifficulty.INTERMEDIATE.value,
                'duration_minutes': 60,
                'target_roles': ['doctor', 'nurse', 'admin', 'it_staff'],
                'content': self._get_hipaa_security_content()
            },
            {
                'module_type': TrainingModuleType.GDPR_AWARENESS.value,
                'title': 'GDPR Awareness Training',
                'description': 'Understanding GDPR principles and requirements for healthcare organizations',
                'difficulty': TrainingDifficulty.BASIC.value,
                'duration_minutes': 50,
                'target_roles': ['doctor', 'nurse', 'admin', 'staff'],
                'content': self._get_gdpr_awareness_content()
            },
            {
                'module_type': TrainingModuleType.GDPR_DATA_SUBJECT_RIGHTS.value,
                'title': 'GDPR Data Subject Rights',
                'description': 'Handling data subject requests and managing individual rights under GDPR',
                'difficulty': TrainingDifficulty.INTERMEDIATE.value,
                'duration_minutes': 55,
                'target_roles': ['admin', 'compliance_officer', 'dpo'],
                'content': self._get_gdpr_data_subject_rights_content()
            },
            {
                'module_type': TrainingModuleType.SECURITY_BEST_PRACTICES.value,
                'title': 'Security Best Practices',
                'description': 'Essential security practices for protecting patient data and systems',
                'difficulty': TrainingDifficulty.BASIC.value,
                'duration_minutes': 40,
                'target_roles': ['doctor', 'nurse', 'admin', 'staff', 'it_staff'],
                'content': self._get_security_best_practices_content()
            },
            {
                'module_type': TrainingModuleType.INCIDENT_RESPONSE.value,
                'title': 'Incident Response Procedures',
                'description': 'Procedures for detecting, reporting, and responding to security incidents',
                'difficulty': TrainingDifficulty.ADVANCED.value,
                'duration_minutes': 70,
                'target_roles': ['it_staff', 'compliance_officer', 'security_team'],
                'content': self._get_incident_response_content()
            }
        ]

    def _get_hipaa_awareness_content(self) -> List[Dict[str, Any]]:
        """Get HIPAA awareness training content"""
        return [
            {
                'id': 'intro',
                'type': 'text',
                'title': 'Introduction to HIPAA',
                'content': '''
                <h2>What is HIPAA?</h2>
                <p>The Health Insurance Portability and Accountability Act (HIPAA) is a federal law that:</p>
                <ul>
                    <li>Protects the privacy of patient health information</li>
                    <li>Establishes national standards for electronic healthcare transactions</li>
                    <li>Requires organizations to implement safeguards for protected health information (PHI)</li>
                    <li>Applies to healthcare providers, health plans, and healthcare clearinghouses</li>
                </ul>
                <p><strong>Key Learning Objectives:</strong></p>
                <ul>
                    <li>Understand HIPAA's purpose and scope</li>
                    <li>Identify types of protected health information</li>
                    <li>Recognize your responsibilities under HIPAA</li>
                </ul>
                '''
            },
            {
                'id': 'privacy_rule',
                'type': 'text',
                'title': 'HIPAA Privacy Rule',
                'content': '''
                <h2>The Privacy Rule</h2>
                <p>The HIPAA Privacy Rule establishes national standards to protect individuals' medical records and other personal health information.</p>

                <h3>Key Requirements:</h3>
                <ul>
                    <li><strong>Use and Disclosure Limitations:</strong> PHI can only be used or disclosed for treatment, payment, or healthcare operations without patient authorization</li>
                    <li><strong>Minimum Necessary:</strong> Only the minimum necessary PHI should be used or disclosed</li>
                    <li><strong>Patient Rights:</strong> Patients have rights to access, amend, and request an accounting of disclosures of their PHI</li>
                    <li><strong>Notice of Privacy Practices:</strong> Organizations must provide patients with a notice of privacy practices</li>
                </ul>

                <h3>Permitted Uses and Disclosures:</h3>
                <ul>
                    <li>Treatment by healthcare providers</li>
                    <li>Payment for healthcare services</li>
                    <li>Healthcare operations</li>
                    <li>When required by law</li>
                    <li>Public health activities</li>
                    <li>Health oversight activities</li>
                </ul>
                '''
            },
            {
                'id': 'security_rule',
                'type': 'text',
                'title': 'HIPAA Security Rule',
                'content': '''
                <h2>The Security Rule</h2>
                <p>The HIPAA Security Rule protects electronic protected health information (ePHI) through appropriate safeguards.</p>

                <h3>Three Categories of Safeguards:</h3>

                <h4>Administrative Safeguards</h4>
                <ul>
                    <li>Security management process</li>
                    <li>Assigned security responsibility</li>
                    <li>Workforce security and training</li>
                    <li>Information access management</li>
                    <li>Security awareness and training</li>
                    <li>Security incident procedures</li>
                    <li>Contingency planning</li>
                    <li>Evaluation</li>
                </ul>

                <h4>Technical Safeguards</h4>
                <ul>
                    <li>Access control</li>
                    <li>Audit controls</li>
                    <li>Integrity controls</li>
                    <li>Person or entity authentication</li>
                    <li>Transmission security</li>
                </ul>

                <h4>Physical Safeguards</h4>
                <ul>
                    <li>Facility access controls</li>
                    <li>Workstation use and security</li>
                    <li>Device and media controls</li>
                </ul>
                '''
            },
            {
                'id': 'breach_notification',
                'type': 'text',
                'title': 'Breach Notification Rule',
                'content': '''
                <h2>Breach Notification Rule</h2>
                <p>The Breach Notification Rule requires covered entities to notify affected individuals, HHS, and the media following a breach of unsecured PHI.</p>

                <h3>What Constitutes a Breach?</h3>
                <p>A breach is defined as the unauthorized acquisition, access, use, or disclosure of PHI that compromises its security or privacy.</p>

                <h3>Notification Requirements:</h3>
                <ul>
                    <li><strong>Individuals:</strong> Must be notified without unreasonable delay, but no later than 60 days after discovery</li>
                    <li><strong>HHS:</strong> Must be notified for breaches affecting 500 or more individuals</li>
                    <li><strong>Media:</strong> Must be notified for breaches affecting 500 or more individuals in the same state</li>
                </ul>

                <h3>Exceptions:</h3>
                <ul>
                    <li>Unintentional acquisition, access, or use made in good faith</li>
                    <li>Inadvertent disclosure to an authorized person</li>
                    <li>If the covered entity believes the information was not acquired</li>
                </ul>
                '''
            },
            {
                'id': 'responsibilities',
                'type': 'text',
                'title': 'Your Responsibilities',
                'content': '''
                <h2>Your HIPAA Responsibilities</h2>

                <h3>All Staff Members:</h3>
                <ul>
                    <li>Complete annual HIPAA training</li>
                    <li>Protect patient privacy and confidentiality</li>
                    <li>Use and disclose PHI only as necessary</li>
                    <li>Report security incidents immediately</li>
                    <li>Follow security policies and procedures</li>
                    <li>Use strong passwords and protect login credentials</li>
                </ul>

                <h3>Healthcare Providers:</h3>
                <ul>
                    <li>Obtain patient consent when required</li>
                    <li>Provide patients with Notice of Privacy Practices</li>
                    <li>Limit access to PHI on a need-to-know basis</li>
                    <li>Maintain proper documentation</li>
                </ul>

                <h3>Administrative Staff:</h3>
                <ul>
                    <li>Handle PHI only as necessary for job functions</li>
                    <li>Verify patient identity before disclosing PHI</li>
                    <li>Follow proper records management procedures</li>
                    <li>Report suspicious activities</li>
                </ul>
                '''
            },
            {
                'id': 'case_studies',
                'type': 'case_study',
                'title': 'HIPAA Case Studies',
                'content': '''
                <h2>Real-World HIPAA Violations</h2>

                <h3>Case Study 1: Laptop Theft</h3>
                <p><strong>Situation:</strong> A hospital employee's laptop containing unencrypted patient records was stolen from their car.</p>
                <p><strong>Violation:</strong> Failure to implement appropriate technical safeguards (encryption) for ePHI.</p>
                <p><strong>Lessons Learned:</strong> Always encrypt devices containing PHI and never leave them unattended.</p>

                <h3>Case Study 2: Unauthorized Access</h3>
                <p><strong>Situation:</strong> An employee accessed their own family members' medical records without authorization.</p>
                <p><strong>Violation:</strong> Unauthorized access to PHI and violation of minimum necessary standard.</p>
                <p><strong>Lessons Learned:</strong> Only access patient information when necessary for your job duties.</p>

                <h3>Case Study 3: Improper Disposal</h3>
                <p><strong>Situation:</strong> Paper medical records were disposed of in regular trash without shredding.</p>
                <p><strong>Violation:</strong> Failure to implement appropriate safeguards for PHI disposal.</p>
                <p><strong>Lessons Learned:</strong> Always follow proper procedures for disposing of PHI.</p>
                '''
            },
            {
                'id': 'quiz',
                'type': 'quiz',
                'title': 'HIPAA Awareness Quiz',
                'questions': [
                    {
                        'id': 'q1',
                        'question': 'What does HIPAA stand for?',
                        'options': [
                            'Health Information Privacy and Accountability Act',
                            'Health Insurance Portability and Accountability Act',
                            'Healthcare Information Protection and Authorization Act',
                            'Healthcare Insurance Privacy and Accountability Act'
                        ],
                        'correct_answer': 1,
                        'explanation': 'HIPAA stands for Health Insurance Portability and Accountability Act.'
                    },
                    {
                        'id': 'q2',
                        'question': 'Which of the following is considered protected health information (PHI)?',
                        'options': [
                            'Patient name and address',
                            'Medical diagnosis',
                            'Insurance information',
                            'All of the above'
                        ],
                        'correct_answer': 3,
                        'explanation': 'All of these are examples of PHI that must be protected under HIPAA.'
                    },
                    {
                        'id': 'q3',
                        'question': 'How long do covered entities have to notify individuals of a breach?',
                        'options': [
                            '30 days',
                            '45 days',
                            '60 days',
                            '90 days'
                        ],
                        'correct_answer': 2,
                        'explanation': 'Notification must occur without unreasonable delay, but no later than 60 days after discovery.'
                    }
                ]
            }
        ]

    def _get_gdpr_awareness_content(self) -> List[Dict[str, Any]]:
        """Get GDPR awareness training content"""
        return [
            {
                'id': 'intro',
                'type': 'text',
                'title': 'Introduction to GDPR',
                'content': '''
                <h2>What is GDPR?</h2>
                <p>The General Data Protection Regulation (GDPR) is a comprehensive data protection law that:</p>
                <ul>
                    <li>Protects the privacy and personal data of EU citizens</li>
                    <li>Applies to organizations processing personal data of EU residents</li>
                    <li>Establishes strict requirements for data processing</li>
                    <li>Provides individuals with significant rights over their data</li>
                </ul>
                <p><strong>Key Learning Objectives:</strong></p>
                <ul>
                    <li>Understand GDPR principles and requirements</li>
                    <li>Identify types of personal data</li>
                    <li>Recognize individual rights under GDPR</li>
                    <li>Understand your responsibilities as a data processor</li>
                </ul>
                '''
            },
            {
                'id': 'key_principles',
                'type': 'text',
                'title': 'Key GDPR Principles',
                'content': '''
                <h2>Seven Key Principles of GDPR</h2>

                <h3>1. Lawfulness, Fairness, and Transparency</h3>
                <ul>
                    <li>Process data lawfully, fairly, and transparently</li>
                    <li>Be clear about how data will be used</li>
                    <li>Provide privacy notices</li>
                </ul>

                <h3>2. Purpose Limitation</h3>
                <ul>
                    <li>Collect data for specified, explicit, and legitimate purposes</li>
                    <li>Do not process data for incompatible purposes</li>
                </ul>

                <h3>3. Data Minimization</h3>
                <ul>
                    <li>Collect only the data necessary for the stated purpose</li>
                    <li>Limit data processing to what is necessary</li>
                </ul>

                <h3>4. Accuracy</h3>
                <ul>
                    <li>Ensure personal data is accurate and up-to-date</li>
                    <li>Correct or erase inaccurate data</li>
                </ul>

                <h3>5. Storage Limitation</h3>
                <ul>
                    <li>Keep data only as long as necessary</li>
                    <li>Establish retention periods and disposal procedures</li>
                </ul>

                <h3>6. Integrity and Confidentiality</h3>
                <ul>
                    <li>Implement appropriate security measures</li>
                    <li>Protect against unauthorized access and processing</li>
                </ul>

                <h3>7. Accountability</h3>
                <ul>
                    <li>Demonstrate compliance with GDPR principles</li>
                    <li>Maintain records of processing activities</li>
                </ul>
                '''
            },
            {
                'id': 'individual_rights',
                'type': 'text',
                'title': 'Individual Rights Under GDPR',
                'content': '''
                <h2>GDPR Individual Rights</h2>

                <h3>1. Right to be Informed</h3>
                <ul>
                    <li>Right to know how your data is being used</li>
                    <li>Must be provided in concise, transparent language</li>
                </ul>

                <h3>2. Right of Access</h3>
                <ul>
                    <li>Right to request copy of personal data</li>
                    <li>Must be provided within 30 days</li>
                </ul>

                <h3>3. Right to Rectification</h3>
                <ul>
                    <li>Right to correct inaccurate personal data</li>
                    <li>Right to complete incomplete data</li>
                </ul>

                <h3>4. Right to Erasure (Right to be Forgotten)</h3>
                <ul>
                    <li>Right to request deletion of personal data</li>
                    <li>Applies in specific circumstances</li>
                </ul>

                <h3>5. Right to Restrict Processing</h3>
                <ul>
                    <li>Right to limit how personal data is used</li>
                    <li>Data can be stored but not processed</li>
                </ul>

                <h3>6. Right to Data Portability</h3>
                <ul>
                    <li>Right to receive data in machine-readable format</li>
                    <li>Right to transfer data to another controller</li>
                </ul>

                <h3>7. Right to Object</h3>
                <ul>
                    <li>Right to object to certain types of processing</li>
                    <li>Includes direct marketing</li>
                </ul>

                <h3>8. Rights Related to Automated Decision Making</h3>
                <ul>
                    <li>Right to human review of automated decisions</li>
                    <li>Right to explanation of decisions</li>
                </ul>
                '''
            },
            {
                'id': 'lawful_basis',
                'type': 'text',
                'title': 'Lawful Basis for Processing',
                'content': '''
                <h2>Lawful Basis for Processing Personal Data</h2>
                <p>Under GDPR, you must have a lawful basis for processing personal data. The six lawful bases are:</p>

                <h3>1. Consent</h3>
                <ul>
                    <li>Individual gives clear, affirmative consent</li>
                    <li>Must be freely given, specific, informed, and unambiguous</li>
                    <li>Easy to withdraw consent</li>
                </ul>

                <h3>2. Contract</h3>
                <ul>
                    <li>Processing is necessary for contract with individual</li>
                    <li>Includes pre-contractual steps</li>
                </ul>

                <h3>3. Legal Obligation</h3>
                <ul>
                    <li>Processing necessary to comply with legal obligation</li>
                    <li>Must be clearly defined by law</li>
                </ul>

                <h3>4. Vital Interests</h3>
                <ul>
                    <li>Processing necessary to protect someone's life</li>
                    <li>Emergency situations only</li>
                </ul>

                <h3>5. Public Task</h3>
                <ul>
                    <li>Processing necessary for official public tasks</li>
                    <li>Must have clear basis in law</li>
                </ul>

                <h3>6. Legitimate Interests</h3>
                <ul>
                    <li>Processing necessary for legitimate interests</li>
                    <li>Must not override individual rights and freedoms</li>
                    <li>Requires legitimate interests assessment</li>
                </ul>
                '''
            }
        ]

    def _get_hipaa_security_content(self) -> List[Dict[str, Any]]:
        """Get HIPAA security training content"""
        return [
            {
                'id': 'admin_safeguards',
                'type': 'text',
                'title': 'Administrative Safeguards',
                'content': '''Detailed content about HIPAA administrative safeguards...'''
            },
            {
                'id': 'technical_safeguards',
                'type': 'text',
                'title': 'Technical Safeguards',
                'content': '''Detailed content about HIPAA technical safeguards...'''
            }
        ]

    def _get_gdpr_data_subject_rights_content(self) -> List[Dict[str, Any]]:
        """Get GDPR data subject rights training content"""
        return [
            {
                'id': 'handling_requests',
                'type': 'text',
                'title': 'Handling Data Subject Requests',
                'content': '''Detailed content about handling GDPR data subject requests...'''
            }
        ]

    def _get_security_best_practices_content(self) -> List[Dict[str, Any]]:
        """Get security best practices training content"""
        return [
            {
                'id': 'password_security',
                'type': 'text',
                'title': 'Password Security',
                'content': '''Detailed content about password security best practices...'''
            }
        ]

    def _get_incident_response_content(self) -> List[Dict[str, Any]]:
        """Get incident response training content"""
        return [
            {
                'id': 'incident_detection',
                'type': 'text',
                'title': 'Incident Detection',
                'content': '''Detailed content about security incident detection...'''
            }
        ]

    def initialize_default_modules(self):
        """Initialize default training modules in the database"""
        for module_data in self.default_training_modules:
            # Check if module already exists
            if not TrainingModule.objects.filter(
                title=module_data['title'],
                module_type=module_data['module_type']
            ).exists():

                # Create training module
                module = TrainingModule.objects.create(
                    title=module_data['title'],
                    description=module_data['description'],
                    module_type=module_data['module_type'],
                    difficulty=module_data['difficulty'],
                    duration_minutes=module_data['duration_minutes'],
                    target_roles=module_data['target_roles'],
                    content=module_data['content']
                )

                # Create quiz for the module
                quiz_content = next(
                    (item for item in module_data['content'] if item['type'] == 'quiz'),
                    None
                )

                if quiz_content:
                    TrainingQuiz.objects.create(
                        training_module=module,
                        title=f"{module.title} Quiz",
                        description="Assessment for this training module",
                        questions=quiz_content.get('questions', []),
                        passing_score=80,
                        max_attempts=3
                    )

                logger.info(f"Created training module: {module.title}")

    def get_required_training_for_role(self, role: str) -> List[TrainingModule]:
        """Get required training modules for a specific role"""
        return TrainingModule.objects.filter(
            is_mandatory=True,
            is_active=True,
            target_roles__contains=[role]
        ).order_by('module_type', 'difficulty')

    def get_user_training_status(self, user) -> Dict[str, Any]:
        """Get comprehensive training status for a user"""
        required_modules = self.get_required_training_for_role(user.role)
        progress_records = TrainingProgress.objects.filter(
            user=user,
            training_module__in=required_modules
        ).select_related('training_module')

        completed_count = 0
        expired_count = 0
        pending_count = 0
        in_progress_count = 0

        modules_status = []

        for module in required_modules:
            progress = progress_records.filter(training_module=module).first()

            if not progress:
                status = TrainingStatus.NOT_STARTED.value
                pending_count += 1
            elif progress.is_expired():
                status = TrainingStatus.EXPIRED.value
                expired_count += 1
            elif progress.status == TrainingStatus.COMPLETED.value:
                status = TrainingStatus.COMPLETED.value
                completed_count += 1
            elif progress.status == TrainingStatus.IN_PROGRESS.value:
                status = TrainingStatus.IN_PROGRESS.value
                in_progress_count += 1
            else:
                status = progress.status
                pending_count += 1

            modules_status.append({
                'module_id': module.id,
                'module_title': module.title,
                'module_type': module.get_module_type_display(),
                'status': status,
                'completion_percentage': module.calculate_completion_percentage(user),
                'due_date': progress.expires_at if progress else None,
                'last_accessed': progress.last_accessed_at if progress else None
            })

        overall_compliance = (completed_count / len(required_modules) * 100) if required_modules else 0

        return {
            'total_required': len(required_modules),
            'completed': completed_count,
            'expired': expired_count,
            'pending': pending_count,
            'in_progress': in_progress_count,
            'overall_compliance_percentage': overall_compliance,
            'modules_status': modules_status,
            'last_updated': timezone.now().isoformat()
        }

    def generate_training_certificate(self, training_progress: TrainingProgress) -> bytes:
        """Generate training certificate PDF"""
        certificate_data = {
            'certificate_number': training_progress.certificate_number,
            'user_name': training_progress.user.get_full_name(),
            'training_title': training_progress.training_module.title,
            'completion_date': training_progress.completed_at.strftime('%B %d, %Y'),
            'expiry_date': training_progress.expires_at.strftime('%B %d, %Y') if training_progress.expires_at else 'Never',
            'duration_minutes': training_progress.training_module.duration_minutes,
            'score': max([q['score'] for q in training_progress.quiz_scores]) if training_progress.quiz_scores else None,
            'issued_by': 'Compliance Management System',
            'logo_url': settings.MEDIA_URL + 'logos/certificate_logo.png',
        }

        # Generate HTML template
        html_content = render_to_string('compliance/training_certificate.html', certificate_data)

        # Convert to PDF
        pdf_content = HTML(string=html_content).write_pdf()

        return pdf_content

    def generate_training_report(self, user=None, department=None, date_range=None) -> bytes:
        """Generate comprehensive training report"""
        # Build queryset
        queryset = TrainingProgress.objects.all()

        if user:
            queryset = queryset.filter(user=user)

        if department:
            queryset = queryset.filter(user__department=department)

        if date_range:
            queryset = queryset.filter(
                completed_at__range=date_range
            )

        # Generate Excel report
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # Summary worksheet
        summary_ws = workbook.add_worksheet('Summary')

        summary_data = [
            ['Metric', 'Value'],
            ['Total Training Records', queryset.count()],
            ['Completed Training', queryset.filter(status='completed').count()],
            ['In Progress', queryset.filter(status='in_progress').count()],
            ['Expired', queryset.filter(status='expired').count()],
            ['Average Completion Time', '45 minutes'],  # Placeholder
            ['Overall Compliance Rate', '85%'],  # Placeholder
        ]

        for row_num, row_data in enumerate(summary_data):
            summary_ws.write_row(row_num, 0, row_data)

        # Detailed records worksheet
        details_ws = workbook.add_worksheet('Detailed Records')

        headers = [
            'User', 'Module', 'Status', 'Started', 'Completed',
            'Time Spent', 'Score', 'Certificate #', 'Expires'
        ]

        for col_num, header in enumerate(headers):
            details_ws.write(0, col_num, header)

        for row_num, progress in enumerate(queryset, 1):
            details_ws.write(row_num, 0, progress.user.get_full_name())
            details_ws.write(row_num, 1, progress.training_module.title)
            details_ws.write(row_num, 2, progress.get_status_display())
            details_ws.write(row_num, 3, progress.started_at.strftime('%Y-%m-%d') if progress.started_at else '')
            details_ws.write(row_num, 4, progress.completed_at.strftime('%Y-%m-%d') if progress.completed_at else '')
            details_ws.write(row_num, 5, f"{progress.time_spent_minutes} min")
            score = max([q['score'] for q in progress.quiz_scores]) if progress.quiz_scores else ''
            details_ws.write(row_num, 6, score)
            details_ws.write(row_num, 7, progress.certificate_number)
            details_ws.write(row_num, 8, progress.expires_at.strftime('%Y-%m-%d') if progress.expires_at else '')

        workbook.close()
        output.seek(0)

        return output.read()


class TrainingAnalyticsService:
    """
    Service for analyzing training data and generating insights
    """

    def __init__(self):
        self.content_service = TrainingContentService()

    def get_department_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance metrics by department"""
        from django.db.models import Count, Q, Avg
        from django.contrib.auth import get_user_model

        User = get_user_model()

        departments = User.objects.values_list('department', flat=True).distinct()
        department_metrics = {}

        for department in departments:
            if not department:
                continue

            department_users = User.objects.filter(department=department)
            user_ids = department_users.values_list('id', flat=True)

            # Get training progress for department
            progress_data = TrainingProgress.objects.filter(user_id__in=user_ids)

            metrics = {
                'total_employees': department_users.count(),
                'total_training_records': progress_data.count(),
                'completed_training': progress_data.filter(status='completed').count(),
                'expired_training': progress_data.filter(status='expired').count(),
                'average_completion_time': progress_data.aggregate(
                    avg_time=Avg('time_spent_minutes')
                )['avg_time'] or 0,
                'compliance_rate': self._calculate_department_compliance_rate(department),
                'popular_modules': self._get_popular_modules(department),
                'training_trends': self._get_department_training_trends(department)
            }

            department_metrics[department] = metrics

        return department_metrics

    def _calculate_department_compliance_rate(self, department: str) -> float:
        """Calculate compliance rate for a department"""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        department_users = User.objects.filter(department=department)

        if not department_users.exists():
            return 0.0

        compliant_users = 0
        for user in department_users:
            user_status = self.content_service.get_user_training_status(user)
            if user_status['overall_compliance_percentage'] >= 100:
                compliant_users += 1

        return (compliant_users / department_users.count() * 100)

    def _get_popular_modules(self, department: str) -> List[Dict[str, Any]]:
        """Get most popular training modules for a department"""
        from django.db.models import Count

        from django.contrib.auth import get_user_model
        User = get_user_model()

        department_users = User.objects.filter(department=department)
        user_ids = department_users.values_list('id', flat=True)

        popular_modules = TrainingProgress.objects.filter(
            user_id__in=user_ids
        ).values('training_module__title').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        return list(popular_modules)

    def _get_department_training_trends(self, department: str) -> Dict[str, Any]:
        """Get training trends for a department over time"""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta

        from django.contrib.auth import get_user_model
        User = get_user_model()

        department_users = User.objects.filter(department=department)
        user_ids = department_users.values_list('id', flat=True)

        # Get training completions by month
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        monthly_completions = TrainingProgress.objects.filter(
            user_id__in=user_ids,
            status='completed',
            completed_at__range=[start_date, end_date]
        ).extra(
            select={'month': "DATE_TRUNC('month', completed_at)"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        return {
            'monthly_completions': list(monthly_completions),
            'total_completions_year': sum(item['count'] for item in monthly_completions),
            'average_monthly_completions': sum(item['count'] for item in monthly_completions) / 12
        }

    def generate_training_insights(self) -> Dict[str, Any]:
        """Generate comprehensive training insights and recommendations"""
        insights = {
            'overview': self._get_overview_insights(),
            'compliance_trends': self._get_compliance_trends(),
            'risk_assessment': self._assess_training_risks(),
            'recommendations': self._generate_training_recommendations(),
            'performance_metrics': self._get_performance_metrics()
        }

        return insights

    def _get_overview_insights(self) -> Dict[str, Any]:
        """Get overall training insights"""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        total_employees = User.objects.filter(is_active=True).count()

        total_progress = TrainingProgress.objects.all()
        completed_training = total_progress.filter(status='completed')

        return {
            'total_employees': total_employees,
            'total_training_records': total_progress.count(),
            'completed_training_sessions': completed_training.count(),
            'overall_compliance_rate': self._calculate_overall_compliance_rate(),
            'average_training_time': total_progress.aggregate(
                avg_time=Avg('time_spent_minutes')
            )['avg_time'] or 0,
            'training_modules_available': TrainingModule.objects.filter(is_active=True).count()
        }

    def _get_compliance_trends(self) -> Dict[str, Any]:
        """Get compliance trends over time"""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta

        end_date = timezone.now()
        start_date = end_date - timedelta(days=90)

        # Monthly compliance rates
        monthly_data = []
        current_date = start_date.replace(day=1)

        while current_date <= end_date:
            month_end = (current_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            completed_in_month = TrainingProgress.objects.filter(
                status='completed',
                completed_at__range=[current_date, month_end]
            ).count()

            monthly_data.append({
                'month': current_date.strftime('%Y-%m'),
                'completions': completed_in_month
            })

            current_date = month_end + timedelta(days=1)

        return {
            'monthly_trends': monthly_data,
            'total_completions_90_days': sum(item['completions'] for item in monthly_data),
            'average_monthly_completions': sum(item['completions'] for item in monthly_data) / len(monthly_data)
        }

    def _assess_training_risks(self) -> Dict[str, Any]:
        """Assess training-related risks"""
        risks = []

        # Check for expired certifications
        expired_count = TrainingProgress.objects.filter(
            status='expired'
        ).count()

        if expired_count > 0:
            risks.append({
                'type': 'expired_certifications',
                'severity': 'high' if expired_count > 10 else 'medium',
                'description': f'{expired_count} employees have expired training certifications',
                'impact': 'Non-compliance with regulatory requirements',
                'recommendation': 'Schedule refresher training immediately'
            })

        # Check for overdue training
        overdue_count = TrainingProgress.objects.filter(
            status__in=['not_started', 'in_progress'],
            training_module__is_mandatory=True
        ).count()

        if overdue_count > 0:
            risks.append({
                'type': 'overdue_training',
                'severity': 'medium' if overdue_count > 20 else 'low',
                'description': f'{overdue_count} mandatory training sessions are overdue',
                'impact': 'Potential compliance gaps and regulatory risks',
                'recommendation': 'Send reminders and track completion'
            })

        # Check for low quiz scores
        low_scores = TrainingProgress.objects.filter(
            quiz_scores__0__score__lt=70
        ).count()

        if low_scores > 0:
            risks.append({
                'type': 'low_comprehension',
                'severity': 'medium',
                'description': f'{low_scores} employees have low training comprehension scores',
                'impact': 'Insufficient understanding of compliance requirements',
                'recommendation': 'Provide additional training and support'
            })

        return {
            'total_risks': len(risks),
            'high_risk_count': len([r for r in risks if r['severity'] == 'high']),
            'medium_risk_count': len([r for r in risks if r['severity'] == 'medium']),
            'low_risk_count': len([r for r in risks if r['severity'] == 'low']),
            'risks': risks
        }

    def _generate_training_recommendations(self) -> List[Dict[str, Any]]:
        """Generate training improvement recommendations"""
        recommendations = []

        # Analyze completion rates
        low_completion_modules = TrainingProgress.objects.filter(
            status__in=['not_started', 'in_progress']
        ).values('training_module__title').annotate(
            count=Count('id')
        ).order_by('-count')[:3]

        for module in low_completion_modules:
            if module['count'] > 5:
                recommendations.append({
                    'priority': 'high',
                    'category': 'completion_rate',
                    'module': module['training_module__title'],
                    'issue': f'{module["count"]} employees have not completed this training',
                    'recommendation': 'Review module content and provide additional support',
                    'estimated_impact': 'Improve compliance rate by 15-20%'
                })

        # Analyze quiz performance
        poor_performance = TrainingProgress.objects.filter(
            quiz_scores__0__score__lt=60
        ).values('training_module__title').annotate(
            count=Count('id')
        ).order_by('-count')[:3]

        for module in poor_performance:
            if module['count'] > 3:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'content_improvement',
                    'module': module['training_module__title'],
                    'issue': f'{module["count"]} employees scored poorly on this module',
                    'recommendation': 'Review and improve training content and quiz questions',
                    'estimated_impact': 'Improve comprehension and retention'
                })

        return recommendations

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed training performance metrics"""
        from django.db.models import Avg, Max, Min, Count

        metrics = {
            'completion_metrics': self._get_completion_metrics(),
            'quiz_performance': self._get_quiz_performance_metrics(),
            'time_metrics': self._get_time_metrics(),
            'module_popularity': self._get_module_popularity_metrics()
        }

        return metrics

    def _get_completion_metrics(self) -> Dict[str, Any]:
        """Get training completion metrics"""
        total_records = TrainingProgress.objects.count()
        completed_records = TrainingProgress.objects.filter(status='completed')

        return {
            'total_records': total_records,
            'completed_records': completed_records.count(),
            'completion_rate': (completed_records.count() / total_records * 100) if total_records > 0 else 0,
            'average_completion_time_days': completed_records.aggregate(
                avg_days=Avg(F('completed_at') - F('started_at'))
            )['avg_days']
        }

    def _get_quiz_performance_metrics(self) -> Dict[str, Any]:
        """Get quiz performance metrics"""
        # Get all quiz scores from training progress
        all_scores = []
        for progress in TrainingProgress.objects.filter(quiz_scores__isnull=False):
            for quiz_result in progress.quiz_scores:
                all_scores.append(quiz_result['score'])

        if not all_scores:
            return {'average_score': 0, 'pass_rate': 0, 'score_distribution': {}}

        return {
            'average_score': sum(all_scores) / len(all_scores),
            'pass_rate': len([s for s in all_scores if s >= 80]) / len(all_scores) * 100,
            'score_distribution': {
                'excellent (90-100)': len([s for s in all_scores if s >= 90]),
                'good (80-89)': len([s for s in all_scores if 80 <= s < 90]),
                'needs_improvement (70-79)': len([s for s in all_scores if 70 <= s < 80]),
                'poor (below 70)': len([s for s in all_scores if s < 70])
            }
        }

    def _get_time_metrics(self) -> Dict[str, Any]:
        """Get time-related training metrics"""
        time_data = TrainingProgress.objects.aggregate(
            avg_time=Avg('time_spent_minutes'),
            max_time=Max('time_spent_minutes'),
            min_time=Min('time_spent_minutes')
        )

        return {
            'average_time_minutes': time_data['avg_time'] or 0,
            'maximum_time_minutes': time_data['max_time'] or 0,
            'minimum_time_minutes': time_data['min_time'] or 0,
            'time_efficiency_rate': self._calculate_time_efficiency()
        }

    def _get_module_popularity_metrics(self) -> List[Dict[str, Any]]:
        """Get module popularity metrics"""
        from django.db.models import Count

        popular_modules = TrainingProgress.objects.values(
            'training_module__title'
        ).annotate(
            count=Count('id'),
            avg_score=Avg('quiz_scores__0__score')
        ).order_by('-count')[:10]

        return list(popular_modules)

    def _calculate_time_efficiency(self) -> float:
        """Calculate training time efficiency"""
        total_estimated_time = sum(
            progress.training_module.duration_minutes
            for progress in TrainingProgress.objects.all()
        )

        total_actual_time = sum(
            progress.time_spent_minutes
            for progress in TrainingProgress.objects.all()
        )

        if total_estimated_time == 0:
            return 0.0

        efficiency = (total_estimated_time / total_actual_time * 100)
        return min(efficiency, 100.0)  # Cap at 100%

    def _calculate_overall_compliance_rate(self) -> float:
        """Calculate overall compliance rate across the organization"""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        total_users = User.objects.filter(is_active=True).count()

        if total_users == 0:
            return 0.0

        compliant_users = 0
        for user in User.objects.filter(is_active=True):
            user_status = self.content_service.get_user_training_status(user)
            if user_status['overall_compliance_percentage'] >= 100:
                compliant_users += 1

        return (compliant_users / total_users * 100)


# API Views for Training Management
class TrainingModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing training modules
    """
    permission_classes = [IsAuthenticated]
    queryset = TrainingModule.objects.filter(is_active=True)
    serializer_class = TrainingModuleSerializer

    @action(detail=True, methods=['post'])
    def start_training(self, request, pk=None):
        """Start a training module for the current user"""
        module = self.get_object()

        # Check if user already has progress
        progress, created = TrainingProgress.objects.get_or_create(
            user=request.user,
            training_module=module,
            defaults={
                'status': TrainingStatus.IN_PROGRESS.value,
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        )

        if not created and progress.status == TrainingStatus.COMPLETED.value:
            return Response(
                {'error': 'Training already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TrainingProgressSerializer(progress)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update training progress"""
        module = self.get_object()
        content_item_id = request.data.get('content_item_id')
        time_spent = request.data.get('time_spent', 0)

        progress = TrainingProgress.objects.filter(
            user=request.user,
            training_module=module
        ).first()

        if not progress:
            return Response(
                {'error': 'Training not started'},
                status=status.HTTP_400_BAD_REQUEST
            )

        progress.update_progress(content_item_id, time_spent)

        serializer = TrainingProgressSerializer(progress)
        return Response(serializer.data)


class TrainingProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing training progress
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TrainingProgressSerializer

    def get_queryset(self):
        """Return training progress for the current user"""
        return TrainingProgress.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_status(self, request):
        """Get comprehensive training status for current user"""
        service = TrainingContentService()
        status_data = service.get_user_training_status(request.user)
        return Response(status_data)


class TrainingQuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing training quizzes
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TrainingQuizSerializer

    def get_queryset(self):
        """Return quizzes for modules the user has access to"""
        return TrainingQuiz.objects.filter(
            training_module__is_active=True,
            training_module__target_roles__contains=[request.user.role]
        )

    @action(detail=True, methods=['post'])
    def start_quiz(self, request, pk=None):
        """Start a quiz attempt"""
        quiz = self.get_object()

        # Check if user has started the training module
        progress = TrainingProgress.objects.filter(
            user=request.user,
            training_module=quiz.training_module
        ).first()

        if not progress:
            return Response(
                {'error': 'Must start training before taking quiz'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check attempt limit
        existing_attempts = QuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz,
            training_progress=progress
        ).count()

        if existing_attempts >= quiz.max_attempts:
            return Response(
                {'error': 'Maximum quiz attempts reached'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new attempt
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            training_progress=progress,
            attempt_number=existing_attempts + 1,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.request.META.get('HTTP_USER_AGENT', '')
        )

        # Get shuffled questions
        questions = quiz.get_shuffled_questions()

        return Response({
            'attempt_id': attempt.id,
            'questions': questions,
            'time_limit_minutes': quiz.time_limit_minutes,
            'started_at': attempt.started_at.isoformat()
        })

    @action(detail=True, methods=['post'])
    def submit_quiz(self, request, pk=None):
        """Submit quiz answers"""
        quiz = self.get_object()
        attempt_id = request.data.get('attempt_id')
        answers = request.data.get('answers', {})

        try:
            attempt = QuizAttempt.objects.get(
                id=attempt_id,
                user=request.user,
                quiz=quiz
            )
        except QuizAttempt.DoesNotExist:
            return Response(
                {'error': 'Invalid quiz attempt'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attempt.completed_at:
            return Response(
                {'error': 'Quiz already submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update answers and complete attempt
        attempt.answers = answers
        attempt.complete_attempt()

        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data)


class TrainingAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for training analytics and reporting
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get training analytics dashboard data"""
        if not request.user.has_perm('compliance.view_training_analytics'):
            return Response(
                {'error': 'Insufficient permissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        service = TrainingAnalyticsService()
        analytics_data = service.generate_training_insights()

        return Response(analytics_data)

    @action(detail=False, methods=['get'])
    def department_metrics(self, request):
        """Get department-specific training metrics"""
        if not request.user.has_perm('compliance.view_training_analytics'):
            return Response(
                {'error': 'Insufficient permissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        service = TrainingAnalyticsService()
        metrics = service.get_department_compliance_metrics()

        return Response(metrics)

    @action(detail=False, methods=['post'])
    def export_report(self, request):
        """Export training report"""
        if not request.user.has_perm('compliance.export_training_reports'):
            return Response(
                {'error': 'Insufficient permissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        report_type = request.data.get('report_type', 'excel')
        user_id = request.data.get('user_id')
        department = request.data.get('department')

        service = TrainingContentService()

        user = None
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        report_data = service.generate_training_report(user=user, department=department)

        if report_type == 'excel':
            response = HttpResponse(report_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="training_report.xlsx"'
        else:
            response = HttpResponse(report_data, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="training_report.pdf"'

        return response


class TrainingCertificateView(APIView):
    """
    View for generating training certificates
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, certificate_number):
        """Generate training certificate"""
        try:
            progress = TrainingProgress.objects.get(certificate_number=certificate_number)
        except TrainingProgress.DoesNotExist:
            return Response(
                {'error': 'Certificate not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user can access this certificate
        if progress.user != request.user and not request.user.has_perm('compliance.view_all_certificates'):
            return Response(
                {'error': 'Insufficient permissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        service = TrainingContentService()
        certificate_pdf = service.generate_training_certificate(progress)

        response = HttpResponse(certificate_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{certificate_number}.pdf"'
        return response


# Template views for training interface
class TrainingDashboardView(LoginRequiredMixin, TemplateView):
    """
    Training dashboard view
    """
    template_name = 'compliance/training_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        service = TrainingContentService()
        user_status = service.get_user_training_status(self.request.user)

        context.update({
            'user_training_status': user_status,
            'available_modules': service.get_required_training_for_role(self.request.user.role),
            'recent_activities': TrainingProgress.objects.filter(
                user=self.request.user
            ).order_by('-last_accessed_at')[:5]
        })

        return context


class TrainingModuleDetailView(LoginRequiredMixin, DetailView):
    """
    Training module detail view
    """
    model = TrainingModule
    template_name = 'compliance/training_module_detail.html'
    context_object_name = 'module'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user progress for this module
        progress = TrainingProgress.objects.filter(
            user=self.request.user,
            training_module=self.object
        ).first()

        context.update({
            'user_progress': progress,
            'completion_percentage': self.object.calculate_completion_percentage(self.request.user),
            'next_content_item': self.object.get_next_content_item(self.request.user)
        })

        return context


class TrainingAnalyticsDashboardView(UserPassesTestMixin, TemplateView):
    """
    Training analytics dashboard view for administrators
    """
    template_name = 'compliance/training_analytics.html'

    def test_func(self):
        return self.request.user.has_perm('compliance.view_training_analytics')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        service = TrainingAnalyticsService()
        analytics_data = service.generate_training_insights()

        context.update({
            'analytics': analytics_data,
            'department_metrics': service.get_department_compliance_metrics()
        })

        return context