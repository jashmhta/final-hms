#!/usr/bin/env python3
"""
Script to fix unused imports in the HMS codebase
"""

import os
import re
from pathlib import Path

def fix_unused_imports():
    """Fix unused imports in the codebase"""
    
    # Files with unused imports to fix
    fixes = {
        'backend/accounting/admin.py': [
            'from django.db.models import Sum',
            'from django.urls import reverse', 
            'from django.utils.safestring import mark_safe',
            'from .models import AccountingPeriod',
            'from .models import ProviderCommissionStructure'
        ],
        'backend/accounting/models.py': [
            'from datetime import date',
            'from datetime import datetime',
            'from core.models import TimeStampedModel',
            'from django.db.models import Q'
        ],
        'backend/accounting/serializers.py': [
            'from decimal import Decimal',
            'from .models import AccountingPeriod',
            'from .models import ExportLog',
            'from .models import ImportBatch',
            'from .models import ProviderCommissionStructure'
        ],
        'backend/accounting/utils.py': [
            'import csv',
            'import json',
            'from datetime import datetime',
            'from decimal import Decimal',
            'from .models import FinancialYear',
            'from .models import PayrollEntry',
            'from .models import TaxLiability'
        ],
        'backend/accounting/views.py': [
            'from datetime import datetime',
            'from django.db import transaction',
            'from django.db.models import Count',
            'from django_filters.rest_framework import DjangoFilterBackend',
            'from rest_framework.filters import OrderingFilter',
            'from rest_framework.filters import SearchFilter',
            'from .models import AccountingPeriod',
            'from .models import DepreciationSchedule',
            'from .models import InvoiceLineItem',
            'from .models import TaxLiability',
            'from .serializers import AgeingReportSerializer',
            'from .serializers import BalanceSheetSerializer',
            'from .serializers import ProfitLossSerializer',
            'from .serializers import TrialBalanceSerializer',
            'from .utils import ComplianceReporter'
        ]
    }
    
    for file_path, unused_imports in fixes.items():
        if os.path.exists(file_path):
            print(f"Fixing unused imports in {file_path}")
            # Implementation would go here
            # For now, just log what needs to be fixed
            for import_line in unused_imports:
                print(f"  - Remove: {import_line}")

if __name__ == "__main__":
    fix_unused_imports()