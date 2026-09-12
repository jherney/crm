import SwiftUI
import CoreData

struct ActivitiesView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Activity.createdAt, ascending: false)],
        animation: .default)
    private var activities: FetchedResults<Activity>
    
    @State private var searchText = ""
    @State private var selectedType = ""
    @State private var showingAddActivity = false
    @State private var selectedEntityType = "Contact"
    @State private var selectedContact: Contact?
    @State private var selectedCompany: Company?
    @State private var selectedDeal: Deal?
    
    let activityTypes = ["note", "email", "call", "meeting", "created", "updated"]
    
    var filteredActivities: [Activity] {
        activities.filter { activity in
            let matchesSearch = searchText.isEmpty ||
                activity.title?.localizedCaseInsensitiveContains(searchText) == true ||
                activity.details?.localizedCaseInsensitiveContains(searchText) == true
            let matchesType = selectedType.isEmpty || activity.type == selectedType
            return matchesSearch && matchesType
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                SearchBar(text: $searchText, placeholder: "Search activities...")
                    .padding(.vertical, 8)
                    .background(Color(.systemGroupedBackground))
                
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        FilterChip(title: "All", isSelected: selectedType.isEmpty) {
                            selectedType = ""
                        }
                        ForEach(activityTypes, id: \.self) { type in
                            FilterChip(title: type.capitalized, isSelected: selectedType == type) {
                                selectedType = type
                            }
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.bottom, 8)
                .background(Color(.systemGroupedBackground))
                
                if filteredActivities.isEmpty {
                    EmptyStateView(
                        icon: "clock.slash",
                        title: "No Activities",
                        message: searchText.isEmpty && selectedType.isEmpty
                            ? "Activities will appear here automatically"
                            : "No activities match your filters"
                    )
                } else {
                    List {
                        ForEach(filteredActivities) { activity in
                            ActivityDetailRow(activity: activity)
                        }
                    }
                    .listStyle(PlainListStyle())
                }
            }
            .navigationTitle("Activities")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingAddActivity = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddActivity) {
                AddActivityView()
            }
        }
    }
}

struct ActivityDetailRow: View {
    let activity: Activity
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 12) {
                Image(systemName: activityIcon(for: activity.type))
                    .foregroundColor(activityColor(for: activity.type))
                    .frame(width: 36, height: 36)
                    .background(activityColor(for: activity.type).opacity(0.1))
                    .cornerRadius(8)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(activity.title ?? "")
                        .font(.headline)
                    Text(activity.type?.capitalized ?? "")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Text(activity.createdAt?.formatted(date: .abbreviated, time: .shortened) ?? "")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if let details = activity.details, !details.isEmpty {
                Text(details)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .padding(.leading, 48)
            }
            
            // Associated entity
            HStack(spacing: 12) {
                if let contact = activity.contact {
                    EntityLink(name: contact.displayName, icon: "person.fill", color: .blue)
                }
                if let company = activity.company {
                    EntityLink(name: company.name ?? "", icon: "building.2.fill", color: .green)
                }
                if let deal = activity.deal {
                    EntityLink(name: deal.name ?? "", icon: "briefcase.fill", color: .orange)
                }
            }
            .padding(.leading, 48)
        }
        .padding(.vertical, 8)
    }
    
    private func activityIcon(for type: String?) -> String {
        switch type?.lowercased() {
        case "email": return "envelope.fill"
        case "call": return "phone.fill"
        case "meeting": return "calendar.fill"
        case "note": return "note.text"
        case "created": return "plus.circle.fill"
        case "updated": return "pencil.circle.fill"
        default: return "circle.fill"
        }
    }
    
    private func activityColor(for type: String?) -> Color {
        switch type?.lowercased() {
        case "email": return .blue
        case "call": return .green
        case "meeting": return .orange
        case "note": return .purple
        case "created": return .green
        case "updated": return .blue
        default: return .gray
        }
    }
}

struct EntityLink: View {
    let name: String
    let icon: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption)
            Text(name)
                .font(.caption)
                .lineLimit(1)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(color.opacity(0.1))
        .foregroundColor(color)
        .cornerRadius(6)
    }
}

struct AddActivityView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Contact.lastName, ascending: true)],
        animation: .default)
    private var contacts: FetchedResults<Contact>
    
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Company.name, ascending: true)],
        animation: .default)
    private var companies: FetchedResults<Company>
    
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Deal.createdAt, ascending: false)],
        animation: .default)
    private var deals: FetchedResults<Deal>
    
    @State private var type = "note"
    @State private var title = ""
    @State private var details = ""
    @State private var selectedContact: Contact?
    @State private var selectedCompany: Company?
    @State private var selectedDeal: Deal?
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    let types = ["note", "email", "call", "meeting"]
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Activity Type")) {
                    Picker("Type", selection: $type) {
                        ForEach(types, id: \.self) { t in
                            Text(t.capitalized).tag(t)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
                
                Section(header: Text("Details")) {
                    TextField("Title *", text: $title)
                    TextEditor(text: $details)
                        .frame(minHeight: 100)
                }
                
                Section(header: Text("Associate With (optional)")) {
                    Picker("Contact", selection: $selectedContact) {
                        Text("None").tag(Contact?.none)
                        ForEach(contacts) { contact in
                            Text(contact.displayName).tag(contact as Contact?)
                        }
                    }
                    
                    Picker("Company", selection: $selectedCompany) {
                        Text("None").tag(Company?.none)
                        ForEach(companies) { company in
                            Text(company.name ?? "").tag(company as Company?)
                        }
                    }
                    
                    Picker("Deal", selection: $selectedDeal) {
                        Text("None").tag(Deal?.none)
                        ForEach(deals) { deal in
                            Text(deal.name ?? "").tag(deal as Deal?)
                        }
                    }
                }
            }
            .navigationTitle("New Activity")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") { saveActivity() }
                        .disabled(title.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .alert("Error", isPresented: $showingAlert) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(alertMessage)
            }
        }
    }
    
    private func saveActivity() {
        let activity = Activity(context: viewContext)
        activity.id = UUID()
        activity.type = type
        activity.title = title.trimmingCharacters(in: .whitespaces)
        activity.details = details.trimmingCharacters(in: .whitespaces).isEmpty ? nil : details.trimmingCharacters(in: .whitespaces)
        activity.createdAt = Date()
        activity.contact = selectedContact
        activity.company = selectedCompany
        activity.deal = selectedDeal
        
        do {
            try viewContext.save()
            dismiss()
        } catch {
            alertMessage = "Failed to save: \(error.localizedDescription)"
            showingAlert = true
        }
    }
}