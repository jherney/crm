# CRM iOS App

A complete iPhone CRM application built with SwiftUI and Core Data, featuring local SQLite storage and full CRM functionality.

## Features

### Contact Management
- Full CRUD operations for contacts
- Search and filter by status (Lead, Prospect, Customer, Partner, Vendor)
- Contact tagging system
- Company associations
- Notes and activity tracking

### Company Management
- Company records with contact relationships
- Contact listing per company
- Full contact info (email, phone, address, website)

### Deal Pipeline
- Visual pipeline view with drag-and-drop stages
- List view with search and filtering
- Deal value tracking and probability
- Expected close dates
- Contact and company associations

### Activity Tracking
- Automatic activity logging
- Activity types: Notes, Emails, Calls, Meetings
- Association with contacts, companies, and deals
- Search and filter capabilities

### Task Management
- Task creation with due dates
- Status tracking (Pending, In Progress, Completed, Cancelled)
- Overdue task highlighting
- Association with contacts, companies, and deals

### Email Templates
- Template library with categories
- Variable substitution system ({{first_name}}, {{company}}, etc.)
- Preview functionality
- Duplicate templates

### Data Management
- Local SQLite storage via Core Data
- Export/Import JSON backup
- Theme support (Light/Dark/System)
- Settings persistence

## Project Structure

```
CRMApp/
├── CRMApp.swift              # App entry point
├── PersistenceController.swift # Core Data stack
├── Info.plist                # App configuration
├── Entitlements.plist        # App entitlements
├── Main.storyboard           # Launch screen
├── CRMModel.xcdatamodeld/    # Core Data model
│   └── contents
├── Models/
│   ├── Contact.swift
│   ├── Company.swift
│   ├── Activity.swift
│   ├── Deal.swift
│   ├── CRMTask.swift
│   └── EmailTemplate.swift
├── Views/
│   ├── ContentView.swift          # Main tab view
│   ├── ContactsView.swift         # Contacts list/detail
│   ├── ContactFormView.swift      # Contact create/edit
│   ├── CompaniesView.swift        # Companies list/detail
│   ├── DealsView.swift            # Deals list/pipeline
│   ├── DealFormView.swift         # Deal create/edit
│   ├── ActivitiesView.swift       # Activity feed
│   ├── TasksView.swift            # Task management
│   ├── TemplatesView.swift        # Email templates
│   └── SettingsView.swift         # App settings
└── CRMApp.csproj               # Xamarin project file
```

## Core Data Model

Entities:
- **Contact**: firstName, lastName, email, phone, title, status, tags, notes, company (relationship)
- **Company**: name, email, phone, address, website, notes, contacts (relationship)
- **Activity**: type, title, details, contact/company/deal (relationships)
- **Deal**: name, value, stage, probability, expectedCloseDate, notes, contact/company (relationships)
- **CRMTask**: title, details, status, dueDate, contact/company/deal (relationships)
- **EmailTemplate**: name, subject, body, category

## Requirements

- iOS 16.0+
- Xcode 15.0+
- Swift 5.9+

## Building the App

### Using Xcode
1. Open the project in Xcode
2. Select a simulator or device
3. Build and run (⌘R)

### Using Command Line
```bash
# Build for simulator
xcodebuild -project CRMApp.csproj -scheme CRMApp -destination 'platform=iOS Simulator,name=iPhone 15' build

# Build for device
xcodebuild -project CRMApp.csproj -scheme CRMApp -destination 'platform=iOS,name=Your Device' build
```

## Data Persistence

All data is stored locally in SQLite via Core Data:
- Database file: `CRMModel.sqlite` in app's Documents directory
- Automatic migrations enabled
- Background context for heavy operations
- Export/Import for backup and transfer

## Key Implementation Details

### SwiftUI Architecture
- MVVM pattern with `@Environment(\.managedObjectContext)`
- `@FetchRequest` for reactive data binding
- Sheet presentations for forms
- NavigationStack for detail views

### Core Data Best Practices
- Lightweight migrations
- Batch delete for bulk operations
- Relationship management with inverse relationships
- UUID primary keys for sync compatibility

### Offline-First Design
- All operations work locally
- No network dependency for core features
- Export/Import for data portability
- Settings persisted with `@AppStorage`

## Extending the App

### Adding New Fields
1. Update `CRMModel.xcdatamodeld/contents`
2. Regenerate NSManagedObject subclasses
3. Update corresponding views

### Adding New Modules
1. Create new entity in data model
2. Create model class
3. Create list/detail/form views
4. Add tab to ContentView

### Sync Integration
- UUIDs ready for cloud sync
- CloudKit entitlements configured
- Export format supports sync metadata

## License

MIT License - Feel free to use and modify for your projects.