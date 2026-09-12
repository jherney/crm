import SwiftUI
import CoreData

struct ContactFormView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let contact: Contact?
    let companies: [Company]
    
    @State private var firstName = ""
    @State private var lastName = ""
    @State private var email = ""
    @State private var phone = ""
    @State private var title = ""
    @State private var status = "lead"
    @State private var selectedCompany: Company?
    @State private var tags = ""
    @State private var notes = ""
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    let statuses = ["lead", "prospect", "customer", "partner", "vendor"]
    
    var isEditing: Bool {
        contact != nil
    }
    
    init(contact: Contact? = nil) {
        self.contact = contact
        let request: NSFetchRequest<Company> = Company.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(keyPath: \Company.name, ascending: true)]
        let context = PersistenceController.shared.container.viewContext
        self.companies = (try? context.fetch(request)) ?? []
        
        if let contact = contact {
            _firstName = State(initialValue: contact.firstName ?? "")
            _lastName = State(initialValue: contact.lastName ?? "")
            _email = State(initialValue: contact.email ?? "")
            _phone = State(initialValue: contact.phone ?? "")
            _title = State(initialValue: contact.title ?? "")
            _status = State(initialValue: contact.status ?? "lead")
            _selectedCompany = State(initialValue: contact.company)
            _tags = State(initialValue: (contact.tags ?? []).joined(separator: ", "))
            _notes = State(initialValue: contact.notes ?? "")
        }
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Name")) {
                    TextField("First Name *", text: $firstName)
                    TextField("Last Name", text: $lastName)
                }
                
                Section(header: Text("Contact Info")) {
                    TextField("Email", text: $email)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                    TextField("Phone", text: $phone)
                        .keyboardType(.phonePad)
                    TextField("Title", text: $title)
                }
                
                Section(header: Text("Status")) {
                    Picker("Status", selection: $status) {
                        ForEach(statuses, id: \.self) { s in
                            Text(s.capitalized).tag(s)
                        }
                    }
                    .pickerStyle(MenuPickerStyle())
                }
                
                Section(header: Text("Company")) {
                    Picker("Company", selection: $selectedCompany) {
                        Text("None").tag(Company?.none)
                        ForEach(companies) { company in
                            Text(company.name ?? "").tag(company as Company?)
                        }
                    }
                }
                
                Section(header: Text("Tags (comma separated)")) {
                    TextField("e.g., VIP, Enterprise, Follow-up", text: $tags)
                }
                
                Section(header: Text("Notes")) {
                    TextEditor(text: $notes)
                        .frame(minHeight: 100)
                }
            }
            .navigationTitle(isEditing ? "Edit Contact" : "New Contact")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") { saveContact() }
                        .disabled(firstName.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .alert("Error", isPresented: $showingAlert) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(alertMessage)
            }
        }
    }
    
    private func saveContact() {
        let targetContact = contact ?? Contact(context: viewContext)
        
        if contact == nil {
            targetContact.id = UUID()
            targetContact.createdAt = Date()
        }
        
        targetContact.firstName = firstName.trimmingCharacters(in: .whitespaces)
        targetContact.lastName = lastName.trimmingCharacters(in: .whitespaces)
        targetContact.email = email.trimmingCharacters(in: .whitespaces).isEmpty ? nil : email.trimmingCharacters(in: .whitespaces)
        targetContact.phone = phone.trimmingCharacters(in: .whitespaces).isEmpty ? nil : phone.trimmingCharacters(in: .whitespaces)
        targetContact.title = title.trimmingCharacters(in: .whitespaces).isEmpty ? nil : title.trimmingCharacters(in: .whitespaces)
        targetContact.status = status
        targetContact.company = selectedCompany
        targetContact.tags = tags.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
        targetContact.notes = notes.trimmingCharacters(in: .whitespaces).isEmpty ? nil : notes.trimmingCharacters(in: .whitespaces)
        targetContact.updatedAt = Date()
        
        do {
            try viewContext.save()
            logActivity(type: isEditing ? "updated" : "created", contact: targetContact)
            dismiss()
        } catch {
            alertMessage = "Failed to save: \(error.localizedDescription)"
            showingAlert = true
        }
    }
    
    private func logActivity(type: String, contact: Contact) {
        let activity = Activity(context: viewContext)
        activity.id = UUID()
        activity.type = type
        activity.title = "Contact \(type): \(contact.displayName)"
        activity.details = "Status: \(contact.status ?? "N/A")"
        activity.createdAt = Date()
        activity.contact = contact
        try? viewContext.save()
    }
}

struct ContactDetailView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let contact: Contact
    @State private var showingEdit = false
    @State private var showingDeleteAlert = false
    @State private var activities: [Activity] = []
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    VStack(spacing: 12) {
                        Circle()
                            .fill(Color.blue.opacity(0.2))
                            .frame(width: 80, height: 80)
                            .overlay(
                                Text(contact.displayName.prefix(1).uppercased())
                                    .font(.system(size: 32, weight: .bold))
                                    .foregroundColor(.blue)
                            )
                        
                        Text(contact.displayName)
                            .font(.title)
                            .fontWeight(.bold)
                        
                        if let title = contact.title, !title.isEmpty {
                            Text(title)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        
                        if let status = contact.status {
                            Text(status.capitalized)
                                .font(.caption)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(statusColor(for: status))
                                .foregroundColor(.white)
                                .cornerRadius(12)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.top)
                    
                    // Contact Info
                    InfoSection(title: "Contact Info", items: [
                        ("Email", contact.email, "envelope.fill"),
                        ("Phone", contact.phone, "phone.fill")
                    ])
                    
                    // Company
                    if let company = contact.company {
                        InfoSection(title: "Company", items: [
                            (company.name ?? "", nil, "building.2.fill")
                        ])
                    }
                    
                    // Tags
                    if let tags = contact.tags, !tags.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Tags")
                                .font(.headline)
                                .padding(.horizontal)
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack {
                                    ForEach(tags, id: \.self) { tag in
                                        Text(tag)
                                            .font(.caption)
                                            .padding(.horizontal, 10)
                                            .padding(.vertical, 5)
                                            .background(Color.blue.opacity(0.1))
                                            .foregroundColor(.blue)
                                            .cornerRadius(8)
                                    }
                                }
                                .padding(.horizontal)
                            }
                        }
                    }
                    
                    // Notes
                    if let notes = contact.notes, !notes.isEmpty {
                        InfoSection(title: "Notes", items: [
                            (notes, nil, "note.text")
                        ])
                    }
                    
                    // Recent Activities
                    if !activities.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Recent Activity")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            ForEach(activities.prefix(5)) { activity in
                                ActivityRow(activity: activity)
                            }
                        }
                    }
                }
                .padding(.bottom)
            }
            .navigationTitle("Contact")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button("Edit") { showingEdit = true }
                        Button("Add Activity") { addActivity() }
                        Button(role: .destructive, action: { showingDeleteAlert = true }) {
                            Label("Delete", systemImage: "trash")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showingEdit) {
                ContactFormView(contact: contact)
            }
            .alert("Delete Contact", isPresented: $showingDeleteAlert) {
                Button("Delete", role: .destructive) { deleteContact() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Are you sure you want to delete this contact? This action cannot be undone.")
            }
            .onAppear { loadActivities() }
        }
    }
    
    private func statusColor(for status: String) -> Color {
        switch status.lowercased() {
        case "lead": return .orange
        case "prospect": return .blue
        case "customer": return .green
        case "partner": return .purple
        case "vendor": return .red
        default: return .gray
        }
    }
    
    private func loadActivities() {
        let request: NSFetchRequest<Activity> = Activity.fetchRequest()
        request.predicate = NSPredicate(format: "contact == %@", contact)
        request.sortDescriptors = [NSSortDescriptor(keyPath: \Activity.createdAt, ascending: false)]
        request.fetchLimit = 10
        activities = (try? viewContext.fetch(request)) ?? []
    }
    
    private func addActivity() {
        let activity = Activity(context: viewContext)
        activity.id = UUID()
        activity.type = "note"
        activity.title = "Note added"
        activity.details = ""
        activity.createdAt = Date()
        activity.contact = contact
        try? viewContext.save()
        loadActivities()
    }
    
    private func deleteContact() {
        viewContext.delete(contact)
        try? viewContext.save()
        dismiss()
    }
}

struct InfoSection: View {
    let title: String
    let items: [(String, String?, String)]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .padding(.horizontal)
            
            VStack(spacing: 0) {
                ForEach(Array(items.enumerated()), id: \.offset) { index, item in
                    HStack(spacing: 12) {
                        Image(systemName: item.2)
                            .foregroundColor(.blue)
                            .frame(width: 24)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text(item.0)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            if let value = item.1, !value.isEmpty {
                                Text(value)
                                    .font(.body)
                            }
                        }
                        
                        Spacer()
                    }
                    .padding()
                    .background(Color(.systemBackground))
                    
                    if index < items.count - 1 {
                        Divider().padding(.leading, 44)
                    }
                }
            }
            .background(Color(.systemGroupedBackground))
            .cornerRadius(12)
            .padding(.horizontal)
        }
    }
}

struct ActivityRow: View {
    let activity: Activity
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: activityIcon(for: activity.type))
                .foregroundColor(.blue)
                .frame(width: 24)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(activity.title ?? "")
                    .font(.subheadline)
                    .fontWeight(.medium)
                if let details = activity.details, !details.isEmpty {
                    Text(details)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                Text(activity.createdAt?.formatted(date: .abbreviated, time: .shortened) ?? "")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding()
        .background(Color(.systemGroupedBackground))
        .cornerRadius(10)
        .padding(.horizontal)
    }
    
    private func activityIcon(for type: String?) -> String {
        switch type?.lowercased() {
        case "created": return "plus.circle"
        case "updated": return "pencil.circle"
        case "deleted": return "trash.circle"
        case "note": return "note.text"
        case "email": return "envelope"
        case "call": return "phone"
        case "meeting": return "calendar"
        default: return "circle"
        }
    }
}