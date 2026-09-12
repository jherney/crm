import SwiftUI
import CoreData

struct SettingsView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @AppStorage("theme") private var theme = "system"
    @AppStorage("notificationsEnabled") private var notificationsEnabled = true
    @AppStorage("autoBackup") private var autoBackup = false
    @AppStorage("defaultCurrency") private var defaultCurrency = "USD"
    
    @State private var showingExport = false
    @State private var showingImport = false
    @State private var showingResetAlert = false
    @State private var showingDeleteAllAlert = false
    @State private var exportURL: URL?
    @State private var importError: String?
    @State private var showingImportError = false
    
    let themes = ["system", "light", "dark"]
    let currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]
    
    var body: some View {
        NavigationView {
            Form {
                // Appearance
                Section(header: Text("Appearance")) {
                    Picker("Theme", selection: $theme) {
                        ForEach(themes, id: \.self) { theme in
                            Text(theme.capitalized).tag(theme)
                        }
                    }
                    .onChange(of: theme) { _ in applyTheme() }
                }
                
                // Notifications
                Section(header: Text("Notifications")) {
                    Toggle("Enable Notifications", isOn: $notificationsEnabled)
                    
                    if notificationsEnabled {
                        NavigationLink("Notification Settings") {
                            NotificationSettingsView()
                        }
                    }
                }
                
                // Data & Backup
                Section(header: Text("Data & Backup")) {
                    Toggle("Auto Backup", isOn: $autoBackup)
                    
                    Button(action: exportData) {
                        Label("Export Data", systemImage: "square.and.arrow.up")
                    }
                    
                    Button(action: { showingImport = true }) {
                        Label("Import Data", systemImage: "square.and.arrow.down")
                    }
                    
                    Button(action: { showingResetAlert = true }) {
                        Label("Reset to Defaults", systemImage: "arrow.counterclockwise")
                            .foregroundColor(.orange)
                    }
                }
                
                // Defaults
                Section(header: Text("Defaults")) {
                    Picker("Default Currency", selection: $defaultCurrency) {
                        ForEach(currencies, id: \.self) { currency in
                            Text(currency).tag(currency)
                        }
                    }
                }
                
                // Danger Zone
                Section(header: Text("Danger Zone")) {
                    Button(action: { showingDeleteAllAlert = true }) {
                        Label("Delete All Data", systemImage: "trash")
                            .foregroundColor(.red)
                    }
                }
                
                // About
                Section(header: Text("About")) {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                    
                    Link("Privacy Policy", destination: URL(string: "https://example.com/privacy")!)
                    Link("Terms of Service", destination: URL(string: "https://example.com/terms")!)
                    Link("Support", destination: URL(string: "https://example.com/support")!)
                }
            }
            .navigationTitle("Settings")
            .sheet(isPresented: $showingExport) {
                if let url = exportURL {
                    ShareSheet(activityItems: [url])
                }
            }
            .fileImporter(
                isPresented: $showingImport,
                allowedContentTypes: [.json],
                allowsMultipleSelection: false
            ) { result in
                handleImport(result: result)
            }
            .alert("Reset Settings", isPresented: $showingResetAlert) {
                Button("Reset", role: .destructive) { resetSettings() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("This will reset all settings to their default values. Your data will not be affected.")
            }
            .alert("Delete All Data", isPresented: $showingDeleteAllAlert) {
                Button("Delete Everything", role: .destructive) { deleteAllData() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("This will permanently delete ALL contacts, companies, deals, activities, tasks, and templates. This action cannot be undone.")
            }
            .alert("Import Error", isPresented: $showingImportError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(importError ?? "Failed to import data")
            }
        }
    }
    
    private func applyTheme() {
        let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene
        switch theme {
        case "light":
            windowScene?.windows.forEach { $0.overrideUserInterfaceStyle = .light }
        case "dark":
            windowScene?.windows.forEach { $0.overrideUserInterfaceStyle = .dark }
        default:
            windowScene?.windows.forEach { $0.overrideUserInterfaceStyle = .unspecified }
        }
    }
    
    private func exportData() {
        // Fetch all data
        let contactsRequest: NSFetchRequest<Contact> = Contact.fetchRequest()
        let companiesRequest: NSFetchRequest<Company> = Company.fetchRequest()
        let dealsRequest: NSFetchRequest<Deal> = Deal.fetchRequest()
        let activitiesRequest: NSFetchRequest<Activity> = Activity.fetchRequest()
        let tasksRequest: NSFetchRequest<CRMTask> = CRMTask.fetchRequest()
        let templatesRequest: NSFetchRequest<EmailTemplate> = EmailTemplate.fetchRequest()
        
        do {
            let contacts = try viewContext.fetch(contactsRequest)
            let companies = try viewContext.fetch(companiesRequest)
            let deals = try viewContext.fetch(dealsRequest)
            let activities = try viewContext.fetch(activitiesRequest)
            let tasks = try viewContext.fetch(tasksRequest)
            let templates = try viewContext.fetch(templatesRequest)
            
            let exportData = CRMExportData(
                contacts: contacts.map { $0.exportDictionary },
                companies: companies.map { $0.exportDictionary },
                deals: deals.map { $0.exportDictionary },
                activities: activities.map { $0.exportDictionary },
                tasks: tasks.map { $0.exportDictionary },
                templates: templates.map { $0.exportDictionary },
                exportDate: Date()
            )
            
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            encoder.outputFormatting = .prettyPrinted
            
            let data = try encoder.encode(exportData)
            let url = FileManager.default.temporaryDirectory.appendingPathComponent("crm-backup-\(Date().timeIntervalSince1970).json")
            try data.write(to: url)
            exportURL = url
            showingExport = true
        } catch {
            importError = "Export failed: \(error.localizedDescription)"
            showingImportError = true
        }
    }
    
    private func handleImport(result: Result<[URL], Error>) {
        guard let url = try? result.get().first else { return }
        
        do {
            let data = try Data(contentsOf: url)
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            let importData = try decoder.decode(CRMExportData.self, from: data)
            
            // Clear existing data
            deleteAllEntities()
            
            // Import contacts
            for contactDict in importData.contacts {
                let contact = Contact(context: viewContext)
                contact.importFromDictionary(contactDict)
            }
            
            // Import companies
            for companyDict in importData.companies {
                let company = Company(context: viewContext)
                company.importFromDictionary(companyDict)
            }
            
            // Import deals
            for dealDict in importData.deals {
                let deal = Deal(context: viewContext)
                deal.importFromDictionary(dealDict)
            }
            
            // Import activities
            for activityDict in importData.activities {
                let activity = Activity(context: viewContext)
                activity.importFromDictionary(activityDict)
            }
            
            // Import tasks
            for taskDict in importData.tasks {
                let task = CRMTask(context: viewContext)
                task.importFromDictionary(taskDict)
            }
            
            // Import templates
            for templateDict in importData.templates {
                let template = EmailTemplate(context: viewContext)
                template.importFromDictionary(templateDict)
            }
            
            try viewContext.save()
        } catch {
            importError = "Import failed: \(error.localizedDescription)"
            showingImportError = true
        }
    }
    
    private func resetSettings() {
        theme = "system"
        notificationsEnabled = true
        autoBackup = false
        defaultCurrency = "USD"
        applyTheme()
    }
    
    private func deleteAllData() {
        deleteAllEntities()
        try? viewContext.save()
    }
    
    private func deleteAllEntities() {
        let entities = ["Contact", "Company", "Deal", "Activity", "CRMTask", "EmailTemplate"]
        for entityName in entities {
            let fetchRequest = NSFetchRequest<NSFetchRequestResult>(entityName: entityName)
            let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
            try? viewContext.execute(deleteRequest)
        }
    }
}

struct NotificationSettingsView: View {
    @AppStorage("notifyNewContact") private var notifyNewContact = true
    @AppStorage("notifyDealUpdates") private var notifyDealUpdates = true
    @AppStorage("notifyTaskDue") private var notifyTaskDue = true
    @AppStorage("notifyActivities") private var notifyActivities = false
    
    var body: some View {
        Form {
            Section(header: Text("New Items")) {
                Toggle("New Contact Added", isOn: $notifyNewContact)
                Toggle("Deal Stage Changed", isOn: $notifyDealUpdates)
            }
            
            Section(header: Text("Tasks & Reminders")) {
                Toggle("Task Due Soon", isOn: $notifyTaskDue)
                Toggle("Overdue Tasks", isOn: $notifyTaskDue)
            }
            
            Section(header: Text("Activity Feed")) {
                Toggle("New Activities", isOn: $notifyActivities)
            }
        }
        .navigationTitle("Notifications")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct ShareSheet: UIViewControllerRepresentable {
    let activityItems: [Any]
    
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: activityItems, applicationActivities: nil)
    }
    
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

// Export/Import data structures
struct CRMExportData: Codable {
    let contacts: [[String: Any]]
    let companies: [[String: Any]]
    let deals: [[String: Any]]
    let activities: [[String: Any]]
    let tasks: [[String: Any]]
    let templates: [[String: Any]]
    let exportDate: Date
    
    enum CodingKeys: String, CodingKey {
        case contacts, companies, deals, activities, tasks, templates, exportDate
    }
    
    init(contacts: [[String: Any]], companies: [[String: Any]], deals: [[String: Any]],
         activities: [[String: Any]], tasks: [[String: Any]], templates: [[String: Any]],
         exportDate: Date) {
        self.contacts = contacts
        self.companies = companies
        self.deals = deals
        self.activities = activities
        self.tasks = tasks
        self.templates = templates
        self.exportDate = exportDate
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(contacts, forKey: .contacts)
        try container.encode(companies, forKey: .companies)
        try container.encode(deals, forKey: .deals)
        try container.encode(activities, forKey: .activities)
        try container.encode(tasks, forKey: .tasks)
        try container.encode(templates, forKey: .templates)
        try container.encode(exportDate, forKey: .exportDate)
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        contacts = try container.decode([[String: Any]].self, forKey: .contacts)
        companies = try container.decode([[String: Any]].self, forKey: .companies)
        deals = try container.decode([[String: Any]].self, forKey: .deals)
        activities = try container.decode([[String: Any]].self, forKey: .activities)
        tasks = try container.decode([[String: Any]].self, forKey: .tasks)
        templates = try container.decode([[String: Any]].self, forKey: .templates)
        exportDate = try container.decode(Date.self, forKey: .exportDate)
    }
}

// Extension to make [String: Any] codable
extension Dictionary: Encodable where Key == String, Value == Any {
    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        let jsonData = try JSONSerialization.data(withJSONObject: self, options: [])
        let json = try JSONSerialization.jsonObject(with: jsonData, options: [])
        try container.encode(json)
    }
}

extension Dictionary: Decodable where Key == String, Value == Any {
    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        let json = try container.decode(Any.self)
        self = json as? [String: Any] ?? [:]
    }
}

// Import/Export helpers for models
extension Contact {
    var exportDictionary: [String: Any] {
        var dict: [String: Any] = [
            "id": id?.uuidString ?? "",
            "firstName": firstName ?? "",
            "lastName": lastName ?? "",
            "email": email ?? "",
            "phone": phone ?? "",
            "title": title ?? "",
            "status": status ?? "lead",
            "notes": notes ?? "",
            "createdAt": createdAt?.iso8601 ?? "",
            "updatedAt": updatedAt?.iso8601 ?? "",
            "tags": tags ?? []
        ]
        if let company = company {
            dict["companyId"] = company.id?.uuidString ?? ""
        }
        return dict
    }
    
    func importFromDictionary(_ dict: [String: Any]) {
        id = UUID(uuidString: dict["id"] as? String ?? "") ?? UUID()
        firstName = dict["firstName"] as? String
        lastName = dict["lastName"] as? String
        email = dict["email"] as? String
        phone = dict["phone"] as? String
        title = dict["title"] as? String
        status = dict["status"] as? String ?? "lead"
        notes = dict["notes"] as? String
        createdAt = (dict["createdAt"] as? String)?.iso8601Date
        updatedAt = (dict["updatedAt"] as? String)?.iso8601Date
        tags = dict["tags"] as? [String] ?? []
        // Company relationship would need to be resolved separately
    }
}

extension Company {
    var exportDictionary: [String: Any] {
        return [
            "id": id?.uuidString ?? "",
            "name": name ?? "",
            "email": email ?? "",
            "phone": phone ?? "",
            "address": address ?? "",
            "website": website ?? "",
            "notes": notes ?? "",
            "createdAt": createdAt?.iso8601 ?? "",
            "updatedAt": updatedAt?.iso8601 ?? ""
        ]
    }
    
    func importFromDictionary(_ dict: [String: Any]) {
        id = UUID(uuidString: dict["id"] as? String ?? "") ?? UUID()
        name = dict["name"] as? String
        email = dict["email"] as? String
        phone = dict["phone"] as? String
        address = dict["address"] as? String
        website = dict["website"] as? String
        notes = dict["notes"] as? String
        createdAt = (dict["createdAt"] as? String)?.iso8601Date
        updatedAt = (dict["updatedAt"] as? String)?.iso8601Date
    }
}

extension Deal {
    var exportDictionary: [String: Any] {
        var dict: [String: Any] = [
            "id": id?.uuidString ?? "",
            "name": name ?? "",
            "value": value,
            "stage": stage ?? "Lead",
            "probability": probability,
            "expectedCloseDate": expectedCloseDate?.iso8601 ?? "",
            "notes": notes ?? "",
            "createdAt": createdAt?.iso8601 ?? "",
            "updatedAt": updatedAt?.iso8601 ?? ""
        ]
        if let contact = contact {
            dict["contactId"] = contact.id?.uuidString ?? ""
        }
        if let company = company {
            dict["companyId"] = company.id?.uuidString ?? ""
        }
        return dict
    }
    
    func importFromDictionary(_ dict: [String: Any]) {
        id = UUID(uuidString: dict["id"] as? String ?? "") ?? UUID()
        name = dict["name"] as? String
        value = dict["value"] as? Double ?? 0
        stage = dict["stage"] as? String ?? "Lead"
        probability = dict["probability"] as? Int16 ?? 0
        expectedCloseDate = (dict["expectedCloseDate"] as? String)?.iso8601Date
        notes = dict["notes"] as? String
        createdAt = (dict["createdAt"] as? String)?.iso8601Date
        updatedAt = (dict["updatedAt"] as? String)?.iso8601Date
    }
}

extension Activity {
    var exportDictionary: [String: Any] {
        var dict: [String: Any] = [
            "id": id?.uuidString ?? "",
            "type": type ?? "",
            "title": title ?? "",
            "details": details ?? "",
            "createdAt": createdAt?.iso8601 ?? ""
        ]
        if let contact = contact {
            dict["contactId"] = contact.id?.uuidString ?? ""
        }
        if let company = company {
            dict["companyId"] = company.id?.uuidString ?? ""
        }
        if let deal = deal {
            dict["dealId"] = deal.id?.uuidString ?? ""
        }
        return dict
    }
    
    func importFromDictionary(_ dict: [String: Any]) {
        id = UUID(uuidString: dict["id"] as? String ?? "") ?? UUID()
        type = dict["type"] as? String
        title = dict["title"] as? String
        details = dict["details"] as? String
        createdAt = (dict["createdAt"] as? String)?.iso8601Date
    }
}

extension CRMTask {
    var exportDictionary: [String: Any] {
        var dict: [String: Any] = [
            "id": id?.uuidString ?? "",
            "title": title ?? "",
            "details": details ?? "",
            "status": status ?? "Pending",
            "dueDate": dueDate?.iso8601 ?? "",
            "createdAt": createdAt?.iso8601 ?? "",
            "updatedAt": updatedAt?.iso8601 ?? ""
        ]
        if let contact = contact {
            dict["contactId"] = contact.id?.uuidString ?? ""
        }
        if let company = company {
            dict["companyId"] = company.id?.uuidString ?? ""
        }
        if let deal = deal {
            dict["dealId"] = deal.id?.uuidString ?? ""
        }
        return dict
    }
    
    func importFromDictionary(_ dict: [String: Any]) {
        id = UUID(uuidString: dict["id"] as? String ?? "") ?? UUID()
        title = dict["title"] as? String
        details = dict["details"] as? String
        status = dict["status"] as? String ?? "Pending"
        dueDate = (dict["dueDate"] as? String)?.iso8601Date
        createdAt = (dict["createdAt"] as? String)?.iso8601Date
        updatedAt = (dict["updatedAt"] as? String)?.iso8601Date
    }
}

extension EmailTemplate {
    var exportDictionary: [String: Any] {
        return [
            "id": id?.uuidString ?? "",
            "name": name ?? "",
            "subject": subject ?? "",
            "body": body ?? "",
            "category": category ?? "General",
            "createdAt": createdAt?.iso8601 ?? "",
            "updatedAt": updatedAt?.iso8601 ?? ""
        ]
    }
    
    func importFromDictionary(_ dict: [String: Any]) {
        id = UUID(uuidString: dict["id"] as? String ?? "") ?? UUID()
        name = dict["name"] as? String
        subject = dict["subject"] as? String
        body = dict["body"] as? String
        category = dict["category"] as? String ?? "General"
        createdAt = (dict["createdAt"] as? String)?.iso8601Date
        updatedAt = (dict["updatedAt"] as? String)?.iso8601Date
    }
}

extension Date {
    var iso8601: String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.string(from: self)
    }
    
    var iso8601Date: Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: self)
    }
}

extension String {
    var iso8601Date: Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: self)
    }
}