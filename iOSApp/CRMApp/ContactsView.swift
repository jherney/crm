import SwiftUI
import CoreData

struct ContactsView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Contact.createdAt, ascending: false)],
        animation: .default)
    private var contacts: FetchedResults<Contact>
    
    @State private var searchText = ""
    @State private var selectedStatus = ""
    @State private var showingAddContact = false
    @State private var selectedContact: Contact?
    
    let statuses = ["lead", "prospect", "customer", "partner", "vendor"]
    
    var filteredContacts: [Contact] {
        contacts.filter { contact in
            let matchesSearch = searchText.isEmpty ||
                contact.firstName?.localizedCaseInsensitiveContains(searchText) == true ||
                contact.lastName?.localizedCaseInsensitiveContains(searchText) == true ||
                contact.email?.localizedCaseInsensitiveContains(searchText) == true
            let matchesStatus = selectedStatus.isEmpty || contact.status == selectedStatus
            return matchesSearch && matchesStatus
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Search and Filter Bar
                VStack(spacing: 12) {
                    SearchBar(text: $searchText, placeholder: "Search contacts...")
                    
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            FilterChip(title: "All", isSelected: selectedStatus.isEmpty) {
                                selectedStatus = ""
                            }
                            ForEach(statuses, id: \.self) { status in
                                FilterChip(title: status.capitalized, isSelected: selectedStatus == status) {
                                    selectedStatus = status
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                }
                .padding(.vertical, 8)
                .background(Color(.systemGroupedBackground))
                
                // Contacts List
                if filteredContacts.isEmpty {
                    EmptyStateView(
                        icon: "person.2.slash",
                        title: "No Contacts",
                        message: searchText.isEmpty && selectedStatus.isEmpty 
                            ? "Tap + to add your first contact"
                            : "No contacts match your search"
                    )
                } else {
                    List {
                        ForEach(filteredContacts) { contact in
                            ContactRow(contact: contact)
                                .onTapGesture {
                                    selectedContact = contact
                                }
                                .swipeActions(edge: .trailing) {
                                    Button(role: .destructive) {
                                        deleteContact(contact)
                                    } label: {
                                        Label("Delete", systemImage: "trash")
                                    }
                                    
                                    Button {
                                        selectedContact = contact
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
            .navigationTitle("Contacts")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingAddContact = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddContact) {
                ContactFormView()
            }
            .sheet(item: $selectedContact) { contact in
                ContactDetailView(contact: contact)
            }
        }
    }
    
    private func deleteContact(_ contact: Contact) {
        withAnimation {
            viewContext.delete(contact)
            try? viewContext.save()
        }
    }
}

struct SearchBar: View {
    @Binding var text: String
    let placeholder: String
    
    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            TextField(placeholder, text: $text)
                .textFieldStyle(PlainTextFieldStyle())
            if !text.isEmpty {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(10)
        .background(Color(.systemBackground))
        .cornerRadius(10)
        .padding(.horizontal)
    }
}

struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(isSelected ? Color.blue : Color(.systemGray5))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(20)
        }
    }
}

struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            Text(title)
                .font(.title2)
                .fontWeight(.semibold)
            Text(message)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }
}

struct ContactRow: View {
    let contact: Contact
    
    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(Color.blue.opacity(0.2))
                .frame(width: 44, height: 44)
                .overlay(
                    Text(contact.displayName.prefix(1).uppercased())
                        .font(.headline)
                        .foregroundColor(.blue)
                )
            
            VStack(alignment: .leading, spacing: 4) {
                Text(contact.displayName)
                    .font(.headline)
                if let title = contact.title, !title.isEmpty {
                    Text(title)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                HStack(spacing: 12) {
                    if let email = contact.email, !email.isEmpty {
                        Label(email, systemImage: "envelope")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    if let phone = contact.phone, !phone.isEmpty {
                        Label(phone, systemImage: "phone")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            Spacer()
            
            if let status = contact.status {
                Text(status.capitalized)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(statusColor(for: status))
                    .foregroundColor(.white)
                    .cornerRadius(8)
            }
        }
        .padding(.vertical, 4)
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
}