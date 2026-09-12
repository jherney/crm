import SwiftUI
import CoreData

struct TemplatesView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \EmailTemplate.createdAt, ascending: false)],
        animation: .default)
    private var templates: FetchedResults<EmailTemplate>
    
    @State private var searchText = ""
    @State private var selectedCategory = ""
    @State private var showingAddTemplate = false
    @State private var selectedTemplate: EmailTemplate?
    
    let categories = ["Sales", "Support", "Marketing", "Onboarding", "Follow-up", "General"]
    
    var filteredTemplates: [EmailTemplate] {
        templates.filter { template in
            let matchesSearch = searchText.isEmpty ||
                template.name?.localizedCaseInsensitiveContains(searchText) == true ||
                template.subject?.localizedCaseInsensitiveContains(searchText) == true
            let matchesCategory = selectedCategory.isEmpty || template.category == selectedCategory
            return matchesSearch && matchesCategory
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                SearchBar(text: $searchText, placeholder: "Search templates...")
                    .padding(.vertical, 8)
                    .background(Color(.systemGroupedBackground))
                
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        FilterChip(title: "All", isSelected: selectedCategory.isEmpty) {
                            selectedCategory = ""
                        }
                        ForEach(categories, id: \.self) { category in
                            FilterChip(title: category, isSelected: selectedCategory == category) {
                                selectedCategory = category
                            }
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.bottom, 8)
                .background(Color(.systemGroupedBackground))
                
                if filteredTemplates.isEmpty {
                    EmptyStateView(
                        icon: "doc.text.slash",
                        title: "No Templates",
                        message: searchText.isEmpty && selectedCategory.isEmpty
                            ? "Tap + to create your first email template"
                            : "No templates match your filters"
                    )
                } else {
                    List {
                        ForEach(filteredTemplates) { template in
                            TemplateRow(template: template)
                                .onTapGesture {
                                    selectedTemplate = template
                                }
                                .swipeActions(edge: .trailing) {
                                    Button(role: .destructive) {
                                        deleteTemplate(template)
                                    } label: {
                                        Label("Delete", systemImage: "trash")
                                    }
                                    
                                    Button {
                                        selectedTemplate = template
                                    } label: {
                                        Label("Edit", systemImage: "pencil")
                                    }
                                    .tint(.blue)
                                }
                        }
                    }
                    .listStyle(PlainListStyle())
                }
            }
            .navigationTitle("Templates")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingAddTemplate = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddTemplate) {
                TemplateFormView()
            }
            .sheet(item: $selectedTemplate) { template in
                TemplateDetailView(template: template)
            }
        }
    }
    
    private func deleteTemplate(_ template: EmailTemplate) {
        withAnimation {
            viewContext.delete(template)
            try? viewContext.save()
        }
    }
}

struct TemplateRow: View {
    let template: EmailTemplate
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(template.name ?? "Unnamed Template")
                        .font(.headline)
                    
                    if let category = template.category, !category.isEmpty {
                        Text(category)
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .cornerRadius(4)
                    }
                }
                
                Spacer()
                
                Image(systemName: "doc.text.fill")
                    .font(.title2)
                    .foregroundColor(.blue)
            }
            
            if let subject = template.subject, !subject.isEmpty {
                Text(subject)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }
            
            if let variables = extractVariables(from: template.body ?? ""), !variables.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 4) {
                        ForEach(variables, id: \.self) { variable in
                            Text("{\(variable)}")
                                .font(.caption2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.purple.opacity(0.1))
                                .foregroundColor(.purple)
                                .cornerRadius(4)
                        }
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }
    
    private func extractVariables(from text: String) -> [String] {
        let pattern = "\\{\\{([^}]+)\\}\\}"
        let regex = try? NSRegularExpression(pattern: pattern)
        let range = NSRange(location: 0, length: text.count)
        let matches = regex?.matches(in: text, options: [], range: range) ?? []
        return matches.compactMap { match in
            guard let range = Range(match.range(at: 1), in: text) else { return nil }
            return String(text[range])
        }
    }
}

struct TemplateFormView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let template: EmailTemplate?
    
    @State private var name = ""
    @State private var subject = ""
    @State private var body = ""
    @State private var category = "General"
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    let categories = ["Sales", "Support", "Marketing", "Onboarding", "Follow-up", "General"]
    
    var isEditing: Bool { template != nil }
    
    init(template: EmailTemplate? = nil) {
        self.template = template
        if let template = template {
            _name = State(initialValue: template.name ?? "")
            _subject = State(initialValue: template.subject ?? "")
            _body = State(initialValue: template.body ?? "")
            _category = State(initialValue: template.category ?? "General")
        }
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Template Info")) {
                    TextField("Template Name *", text: $name)
                    
                    Picker("Category", selection: $category) {
                        ForEach(categories, id: \.self) { c in
                            Text(c).tag(c)
                        }
                    }
                }
                
                Section(header: Text("Email Content")) {
                    TextField("Subject", text: $subject)
                    
                    TextEditor(text: $body)
                        .frame(minHeight: 200)
                        .font(.system(.body, design: .monospaced))
                }
                
                Section(header: Text("Available Variables")) {
                    Text("Use double curly braces for variables:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    VariableList()
                }
            }
            .navigationTitle(isEditing ? "Edit Template" : "New Template")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") { saveTemplate() }
                        .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .alert("Error", isPresented: $showingAlert) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(alertMessage)
            }
        }
    }
    
    private func saveTemplate() {
        let targetTemplate = template ?? EmailTemplate(context: viewContext)
        
        if template == nil {
            targetTemplate.id = UUID()
            targetTemplate.createdAt = Date()
        }
        
        targetTemplate.name = name.trimmingCharacters(in: .whitespaces)
        targetTemplate.subject = subject.trimmingCharacters(in: .whitespaces).isEmpty ? nil : subject.trimmingCharacters(in: .whitespaces)
        targetTemplate.body = body.trimmingCharacters(in: .whitespaces).isEmpty ? nil : body.trimmingCharacters(in: .whitespaces)
        targetTemplate.category = category
        targetTemplate.updatedAt = Date()
        
        do {
            try viewContext.save()
            dismiss()
        } catch {
            alertMessage = "Failed to save: \(error.localizedDescription)"
            showingAlert = true
        }
    }
}

struct VariableList: View {
    let variables = [
        ("Contact", ["first_name", "last_name", "full_name", "email", "phone", "title", "company"]),
        ("Company", ["name", "email", "phone", "address", "website"]),
        ("Deal", ["name", "value", "stage", "probability", "close_date"]),
        ("Date", ["current_date", "current_datetime"])
    ]
    
    var body: some View {
        ForEach(variables, id: \.0) { category, vars in
            VStack(alignment: .leading, spacing: 4) {
                Text(category)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
                ForEach(vars, id: \.self) { variable in
                    Text("{{\(variable)}}")
                        .font(.caption)
                        .font(.system(.caption, design: .monospaced))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(Color(.systemGray5))
                        .cornerRadius(4)
                }
            }
        }
    }
}

struct TemplateDetailView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let template: EmailTemplate
    @State private var showingEdit = false
    @State private var showingDeleteAlert = false
    @State private var showingPreview = false
    @State private var previewSubject = ""
    @State private var previewBody = ""
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Image(systemName: "doc.text.fill")
                                .font(.system(size: 40))
                                .foregroundColor(.blue)
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text(template.name ?? "Unnamed Template")
                                    .font(.title)
                                    .fontWeight(.bold)
                                
                                if let category = template.category, !category.isEmpty {
                                    Text(category)
                                        .font(.subheadline)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 4)
                                        .background(Color.blue.opacity(0.1))
                                        .foregroundColor(.blue)
                                        .cornerRadius(8)
                                }
                            }
                            
                            Spacer()
                        }
                    }
                    .padding()
                    .background(Color(.systemGroupedBackground))
                    .cornerRadius(12)
                    .padding(.horizontal)
                    
                    // Subject
                    if let subject = template.subject, !subject.isEmpty {
                        InfoSection(title: "Subject", items: [
                            (subject, nil, "textformat")
                        ])
                    }
                    
                    // Body
                    if let body = template.body, !body.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Body")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            Text(body)
                                .font(.system(.body, design: .monospaced))
                                .padding()
                                .background(Color(.systemGroupedBackground))
                                .cornerRadius(12)
                                .padding(.horizontal)
                        }
                    }
                    
                    // Variables used
                    let usedVariables = extractVariables(from: (template.body ?? "") + (template.subject ?? ""))
                    if !usedVariables.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Variables Used")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 8) {
                                    ForEach(usedVariables, id: \.self) { variable in
                                        Text("{\(variable)}")
                                            .font(.caption)
                                            .font(.system(.caption, design: .monospaced))
                                            .padding(.horizontal, 10)
                                            .padding(.vertical, 6)
                                            .background(Color.purple.opacity(0.1))
                                            .foregroundColor(.purple)
                                            .cornerRadius(8)
                                    }
                                }
                                .padding(.horizontal)
                            }
                        }
                    }
                }
                .padding(.bottom)
            }
            .navigationTitle("Template")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button("Edit") { showingEdit = true }
                        Button("Preview") { generatePreview() }
                        Button("Duplicate") { duplicateTemplate() }
                        Button(role: .destructive, action: { showingDeleteAlert = true }) {
                            Label("Delete", systemImage: "trash")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showingEdit) {
                TemplateFormView(template: template)
            }
            .sheet(isPresented: $showingPreview) {
                TemplatePreviewView(subject: previewSubject, body: previewBody)
            }
            .alert("Delete Template", isPresented: $showingDeleteAlert) {
                Button("Delete", role: .destructive) { deleteTemplate() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Are you sure you want to delete this template? This action cannot be undone.")
            }
        }
    }
    
    private func extractVariables(from text: String) -> [String] {
        let pattern = "\\{\\{([^}]+)\\}\\}"
        let regex = try? NSRegularExpression(pattern: pattern)
        let range = NSRange(location: 0, length: text.count)
        let matches = regex?.matches(in: text, options: [], range: range) ?? []
        return matches.compactMap { match in
            guard let range = Range(match.range(at: 1), in: text) else { return nil }
            return String(text[range])
        }
    }
    
    private func generatePreview() {
        previewSubject = template.subject ?? ""
        previewBody = template.body ?? ""
        
        // Replace variables with sample data
        let sampleData: [String: String] = [
            "first_name": "John",
            "last_name": "Doe",
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1 (555) 123-4567",
            "title": "CEO",
            "company": "Acme Inc.",
            "name": "Acme Inc.",
            "address": "123 Main St, City, State",
            "website": "https://acme.com",
            "value": "$50,000",
            "stage": "Proposal",
            "probability": "75%",
            "close_date": "Dec 31, 2024",
            "current_date": Date().formatted(date: .abbreviated, time: .omitted),
            "current_datetime": Date().formatted(date: .abbreviated, time: .shortened)
        ]
        
        for (key, value) in sampleData {
            previewSubject = previewSubject.replacingOccurrences(of: "{{\(key)}}", with: value)
            previewBody = previewBody.replacingOccurrences(of: "{{\(key)}}", with: value)
        }
        
        showingPreview = true
    }
    
    private func duplicateTemplate() {
        let newTemplate = EmailTemplate(context: viewContext)
        newTemplate.id = UUID()
        newTemplate.name = (template.name ?? "") + " (Copy)"
        newTemplate.subject = template.subject
        newTemplate.body = template.body
        newTemplate.category = template.category
        newTemplate.createdAt = Date()
        newTemplate.updatedAt = Date()
        try? viewContext.save()
        dismiss()
    }
    
    private func deleteTemplate() {
        viewContext.delete(template)
        try? viewContext.save()
        dismiss()
    }
}

struct TemplatePreviewView: View {
    @Environment(\.dismiss) private var dismiss
    let subject: String
    let body: String
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Email header
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Preview")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Text(subject.isEmpty ? "(No subject)" : subject)
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Divider()
                    }
                    .padding()
                    .background(Color(.systemGroupedBackground))
                    .cornerRadius(12)
                    .padding(.horizontal)
                    
                    // Email body
                    Text(body.isEmpty ? "(No body content)" : body)
                        .font(.body)
                        .padding()
                        .background(Color(.systemBackground))
                        .cornerRadius(12)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color(.separator), lineWidth: 1)
                        )
                        .padding(.horizontal)
                }
                .padding(.vertical)
            }
            .navigationTitle("Preview")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}