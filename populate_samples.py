#!/usr/bin/env python3
"""
Sample data population script for Futuristic Contact Manager
Creates realistic test contacts for development and testing
"""

import sys
from datetime import datetime, timedelta
from backend.api import store, Contact, ContactRole

def create_sample_contacts():
    """Create sample contacts for testing and development"""
    
    print("🏢 Populating database with sample contacts...")
    
    # Sample contacts with realistic data
    sample_contacts = [
        {
            "id": "sample-001",
            "name": "John Doe",
            "email": "john.doe@company.com",
            "phone": "+1-555-0123",
            "role": ContactRole.ADMIN,
            "tags": ["executive", "priority", "client"],
            "created_at": datetime.now() - timedelta(days=30),
            "updated_at": datetime.now() - timedelta(days=5),
            "metadata": {"department": "Executive", "level": "C-suite"},
            "attachments": [],
            "audit_log": []
        },
        {
            "id": "sample-002", 
            "name": "Jane Smith",
            "email": "jane.smith@company.com",
            "phone": "+1-555-0456",
            "role": ContactRole.MEMBER,
            "tags": ["marketing", "campaign", "client"],
            "created_at": datetime.now() - timedelta(days=25),
            "updated_at": datetime.now() - timedelta(days=2),
            "metadata": {"department": "Marketing", "campaign": "Q4-2026"},
            "attachments": [],
            "audit_log": []
        },
        {
            "id": "sample-003",
            "name": "Robert Johnson",
            "email": "robert.j@techcorp.com", 
            "phone": "+1-555-0789",
            "role": ContactRole.MEMBER,
            "tags": ["engineering", "technical", "vendor"],
            "created_at": datetime.now() - timedelta(days=20),
            "updated_at": datetime.now() - timedelta(days=1),
            "metadata": {"department": "Engineering", "level": "Senior"},
            "attachments": ["contract.pdf"],
            "audit_log": []
        },
        {
            "id": "sample-004",
            "name": "Sarah Williams",
            "email": "sarah.williams@company.com",
            "phone": "+1-555-0321", 
            "role": ContactRole.GUEST,
            "tags": ["design", "creative", "partner"],
            "created_at": datetime.now() - timedelta(days=15),
            "updated_at": datetime.now() - timedelta(days=1),
            "metadata": {"department": "Design", "access_level": "guest"},
            "attachments": ["portfolio.pdf", "agreement.pdf"],
            "audit_log": []
        },
        {
            "id": "sample-005",
            "name": "Michael Brown",
            "email": "m.brown@company.com",
            "phone": "+1-555-0654",
            "role": ContactRole.MEMBER,
            "tags": ["finance", "budget", "client"],
            "created_at": datetime.now() - timedelta(days=10),
            "updated_at": datetime.now() - timedelta(days=3),
            "metadata": {"department": "Finance", "account": "ACC-789"},
            "attachments": ["invoice.pdf"],
            "audit_log": []
        },
        {
            "id": "sample-006",
            "name": "Emily Davis",
            "email": "emily.davis@company.com",
            "phone": "+1-555-0987",
            "role": ContactRole.MEMBER,
            "tags": ["sales", "client", "vip"],
            "created_at": datetime.now() - timedelta(days=8),
            "updated_at": datetime.now() - timedelta(hours=12),
            "metadata": {"department": "Sales", "tier": "VIP"},
            "attachments": [],
            "audit_log": []
        },
        {
            "id": "sample-007",
            "name": "David Wilson",
            "email": "d.wilson@company.com",
            "phone": "+1-555-0222",
            "role": ContactRole.ADMIN,
            "tags": ["hr", "recruitment", "employee"],
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now() - timedelta(hours=6),
            "metadata": {"department": "Human Resources", "type": "employee"},
            "attachments": ["offer_letter.pdf"],
            "audit_log": []
        },
        {
            "id": "sample-008",
            "name": "Lisa Anderson",
            "email": "lisa.anderson@company.com",
            "phone": "+1-555-0555",
            "role": ContactRole.MEMBER,
            "tags": ["operations", "support", "internal"],
            "created_at": datetime.now() - timedelta(days=3),
            "updated_at": datetime.now() - timedelta(hours=2),
            "metadata": {"department": "Operations", "status": "active"},
            "attachments": [],
            "audit_log": []
        }
    ]
    
    # Clear existing data
    store.contacts.clear()
    print(f"✅ Cleared existing contacts ({len(store.contacts)} contacts)")
    
    # Add sample contacts
    for contact_data in sample_contacts:
        contact = Contact(**contact_data)
        store.create(contact)
        print(f"✅ Added contact: {contact.name} ({contact.email})")
    
    print(f"\n🎉 Database populated successfully!")
    print(f"📊 Total contacts: {len(store.contacts)}")
    print(f"🏢 Departments represented: Executive, Marketing, Engineering, Design, Finance, Sales, HR, Operations")
    print(f"🏷️  Tags available: executive, priority, client, marketing, campaign, technical, vendor, creative, partner, budget, vip, recruitment, employee, support, internal")

if __name__ == "__main__":
    print("🚀 Futuristic Contact Manager - Sample Data Population")
    print("=" * 60)
    create_sample_contacts()
