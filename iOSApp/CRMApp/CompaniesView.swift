import SwiftUI
import CoreData

struct CompaniesView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Company.createdAt, ascending: false)],
        animation: .default)
    private var companies: FetchedResults<Company>
    
    @State private var searchText = ""
    @State private var showingAddCompany = false
    @State private var selectedCompany: Company?
    
    var filteredCompanies: [Company] {
        companies.filter { company in
            searchText.isEmpty ||
            company.name?.localizedCaseInsensitiveContains(searchText) == true ||
            company.email?.localizedCaseInsensitiveContains(searchText) == true
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                SearchBar(text: $searchText, placeholder: "Search companies...")
                    .padding(.vertical, 8)
                    .background(Color(.systemGroupedBackground))
                
                if filteredCompanies.isEmpty {
                    EmptyStateView(
                        icon: "building.2.slash",
                        title: "No Companies",
                        message: searchText.isEmpty 
                            ? "Tap + to add your first company"
                            : "No companies match your search"
                    )
                } else {
                    List {
                        ForEach(filteredCompanies) { company in
                            CompanyRow(company: company)
                                .onTapGesture {
                                    selectedCompany = company
                                }
                                .swipeActions(edge: .trailing) {
                                    Button(role: .destructive) {
                                        deleteCompany(company)
                                    } label: {
                                        Label("Delete", systemImage: "trash")
                                    }
                                    
                                    Button {
                                        selectedCompany = company
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
            .navigationTitle("Companies")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingAddCompany = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddCompany) {
                CompanyFormView()
            }
            .sheet(item: $selectedCompany) { company in
                CompanyDetailView(company: company)
            }
        }
    }
    
    private func deleteCompany(_ company: Company) {
        withAnimation {
            viewContext.delete(company)
            try? viewContext.save()
        }
    }
}

struct CompanyRow: View {
    let company: Company
    
    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(Color.green.opacity(0.2))
                .frame(width: 44, height: 44)
                .overlay(
                    Text(company.name?.prefix(1).uppercased() ?? "?")
                        .font(.headline)
                        .foregroundColor(.green)
                )
            
            VStack(alignment: .leading, spacing: 4) {
                Text(company.name ?? "Unnamed Company")
                    .font(.headline)
                if let email = company.email, !email.isEmpty {
                    Text(email)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                Text("\(company.contactArray.count) contacts")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding(.vertical, 4)
    }
}

struct CompanyFormView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let company: Company?
    
    @State private var name = ""
    @State private var email = ""
    @State private var phone = ""
    @State private var address = ""
    @State private var website = ""
    @State private var notes = ""
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    var isEditing: Bool { company != nil }
    
    init(company: Company? = nil) {
        self.company = company
        if let company = company {
            _name = State(initialValue: company.name ?? "")
            _email = State(initialValue: company.email ?? "")
            _phone = State(initialValue: company.phone ?? "")
            _address = State(initialValue: company.address ?? "")
            _website = State(initialValue: company.website ?? "")
            _notes = State(initialValue: company.notes ?? "")
        }
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Company Info")) {
                    TextField("Name *", text: $name)
                    TextField("Email", text: $email)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                    TextField("Phone", text: $phone)
                        .keyboardType(.phonePad)
                    TextField("Website", text: $website)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                }
                
                Section(header: Text("Address")) {
                    TextField("Address", text: $address, axis: .vertical)
                        .lineLimit(3...)
                }
                
                Section(header: Text("Notes")) {
                    TextEditor(text: $notes)
                        .frame(minHeight: 100)
                }
            }
            .navigationTitle(isEditing ? "Edit Company" : "New Company")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") { saveCompany() }
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
    
    private func saveCompany() {
        let targetCompany = company ?? Company(context: viewContext)
        
        if company == nil {
            targetCompany.id = UUID()
            targetCompany.createdAt = Date()
        }
        
        targetCompany.name = name.trimmingCharacters(in: .whitespaces)
        targetCompany.email = email.trimmingCharacters(in: .whitespaces).isEmpty ? nil : email.trimmingCharacters(in: .whitespaces)
        targetCompany.phone = phone.trimmingCharacters(in: .whitespaces).isEmpty ? nil : phone.trimmingCharacters(in: .whitespaces)
        targetCompany.address = address.trimmingCharacters(in: .whitespaces).isEmpty ? nil : address.trimmingCharacters(in: .whitespaces)
        targetCompany.website = website.trimmingCharacters(in: .whitespaces).isEmpty ? nil : website.trimmingCharacters(in: .whitespaces)
        targetCompany.notes = notes.trimmingCharacters(in: .whitespaces).isEmpty ? nil : notes.trimmingCharacters(in: .whitespaces)
        targetCompany.updatedAt = Date()
        
        do {
            try viewContext.save()
            logActivity(type: isEditing ? "updated" : "created", company: targetCompany)
            dismiss()
        } catch {
            alertMessage = "Failed to save: \(error.localizedDescription)"
            showingAlert = true
        }
    }
    
    private func logActivity(type: String, company: Company) {
        let activity = Activity(context: viewContext)
        activity.id = UUID()
        activity.type = type
        activity.title = "Company \(type): \(company.name ?? "")"
        activity.details = ""
        activity.createdAt = Date()
        activity.company = company
        try? viewContext.save()
    }
}

struct CompanyDetailView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let company: Company
    @State private var showingEdit = false
    @State private var showingDeleteAlert = false
    @State private var activities: [Activity] = []
    @State private var showingAddContact = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    VStack(spacing: 12) {
                        Circle()
                            .fill(Color.green.opacity(0.2))
                            .frame(width: 80, height: 80)
                            .overlay(
                                Text(company.name?.prefix(1).uppercased() ?? "?")
                                    .font(.system(size: 32, weight: .bold))
                                    .foregroundColor(.green)
                            )
                        
                        Text(company.name ?? "Unnamed Company")
                            .font(.title)
                            .fontWeight(.bold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.top)
                    
                    // Info
                    InfoSection(title: "Contact Info", items: [
                        ("Email", company.email, "envelope.fill"),
                        ("Phone", company.phone, "phone.fill"),
                        ("Website", company.website, "globe"),
                        ("Address", company.address, "location.fill")
                    ])
                    
                    // Contacts
                    if !company.contactArray.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Text("Contacts (\(company.contactArray.count))")
                                    .font(.headline)
                                Spacer()
                                Button("Add Contact") {
                                    showingAddContact = true
                                }
                                .font(.subheadline)
                            }
                            .padding(.horizontal)
                            
                            ForEach(company.contactArray.prefix(5)) { contact in
                                ContactRow(contact: contact)
                                    .padding(.horizontal)
                            }
                        }
                    }
                    
                    // Notes
                    if let notes = company.notes, !notes.isEmpty {
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
            .navigationTitle("Company")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button("Edit") { showingEdit = true }
                        Button("Add Contact") { showingAddContact = true }
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
                CompanyFormView(company: company)
            }
            .sheet(isPresented: $showingAddContact) {
                ContactFormView()
            }
            .alert("Delete Company", isPresented: $showingDeleteAlert) {
                Button("Delete", role: .destructive) { deleteCompany() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Are you sure you want to delete this company? This action cannot be undone.")
            }
            .onAppear { loadActivities() }
        }
    }
    
    private func loadActivities() {
        let request: NSFetchRequest<Activity> = Activity.fetchRequest()
        request.predicate = NSPredicate(format: "company == %@", company)
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
        activity.company = company
        try? viewContext.save()
        loadActivities()
    }
    
    private func deleteCompany() {
        viewContext.delete(company)
        try? viewContext.save()
        dismiss()
    }
}