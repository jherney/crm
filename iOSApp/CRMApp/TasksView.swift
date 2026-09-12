import SwiftUI
import CoreData

struct TasksView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @FetchRequest(
        sortDescriptors: [
            NSSortDescriptor(keyPath: \CRMTask.status, ascending: true),
            NSSortDescriptor(keyPath: \CRMTask.dueDate, ascending: true)
        ],
        animation: .default)
    private var tasks: FetchedResults<CRMTask>
    
    @State private var searchText = ""
    @State private var selectedStatus = ""
    @State private var showingAddTask = false
    @State private var selectedTask: CRMTask?
    @State private var showCompleted = true
    
    let statuses = CRMTask.statuses
    
    var filteredTasks: [CRMTask] {
        tasks.filter { task in
            let matchesSearch = searchText.isEmpty ||
                task.title?.localizedCaseInsensitiveContains(searchText) == true ||
                task.details?.localizedCaseInsensitiveContains(searchText) == true
            let matchesStatus = selectedStatus.isEmpty || task.status == selectedStatus
            let matchesCompleted = showCompleted || !task.isCompleted
            return matchesSearch && matchesStatus && matchesCompleted
        }
    }
    
    var pendingTasks: [CRMTask] {
        filteredTasks.filter { !$0.isCompleted }
    }
    
    var completedTasks: [CRMTask] {
        filteredTasks.filter { $0.isCompleted }
    }
    
    var overdueTasks: [CRMTask] {
        pendingTasks.filter { task in
            guard let dueDate = task.dueDate else { return false }
            return dueDate < Date()
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Controls
                VStack(spacing: 12) {
                    SearchBar(text: $searchText, placeholder: "Search tasks...")
                    
                    HStack {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                FilterChip(title: "All", isSelected: selectedStatus.isEmpty) {
                                    selectedStatus = ""
                                }
                                ForEach(statuses, id: \.self) { status in
                                    FilterChip(title: status, isSelected: selectedStatus == status) {
                                        selectedStatus = status
                                    }
                                }
                            }
                            .padding(.horizontal)
                        }
                        
                        Toggle("Completed", isOn: $showCompleted)
                            .labelsHidden()
                            .padding(.trailing)
                    }
                }
                .padding(.vertical, 8)
                .background(Color(.systemGroupedBackground))
                
                if filteredTasks.isEmpty {
                    EmptyStateView(
                        icon: "checklist.unchecked",
                        title: "No Tasks",
                        message: searchText.isEmpty && selectedStatus.isEmpty
                            ? "Tap + to create your first task"
                            : "No tasks match your filters"
                    )
                } else {
                    List {
                        if !overdueTasks.isEmpty {
                            Section(header: Text("Overdue (\(overdueTasks.count))").foregroundColor(.red)) {
                                ForEach(overdueTasks) { task in
                                    TaskRow(task: task, selectedTask: $selectedTask)
                                }
                            }
                        }
                        
                        let otherPending = pendingTasks.filter { !overdueTasks.contains($0) }
                        if !otherPending.isEmpty {
                            Section(header: Text("Pending (\(otherPending.count))")) {
                                ForEach(otherPending) { task in
                                    TaskRow(task: task, selectedTask: $selectedTask)
                                }
                            }
                        }
                        
                        if showCompleted && !completedTasks.isEmpty {
                            Section(header: Text("Completed (\(completedTasks.count))")) {
                                ForEach(completedTasks) { task in
                                    TaskRow(task: task, selectedTask: $selectedTask)
                                }
                            }
                        }
                    }
                    .listStyle(InsetGroupedListStyle())
                }
            }
            .navigationTitle("Tasks")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingAddTask = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddTask) {
                TaskFormView()
            }
            .sheet(item: $selectedTask) { task in
                TaskDetailView(task: task)
            }
        }
    }
}

struct TaskRow: View {
    let task: CRMTask
    @Binding var selectedTask: CRMTask?
    
    var body: some View {
        HStack(spacing: 12) {
            Button(action: { toggleCompletion() }) {
                Image(systemName: task.isCompleted ? "checkmark.circle.fill" : "circle")
                    .font(.title2)
                    .foregroundColor(task.isCompleted ? .green : .secondary)
            }
            .buttonStyle(PlainButtonStyle())
            
            VStack(alignment: .leading, spacing: 4) {
                Text(task.title ?? "Untitled Task")
                    .font(.headline)
                    .strikethrough(task.isCompleted)
                    .foregroundColor(task.isCompleted ? .secondary : .primary)
                
                HStack(spacing: 12) {
                    if let dueDate = task.dueDate {
                        Label(dueDate.formatted(date: .abbreviated, time: .omitted), systemImage: "calendar")
                            .font(.caption)
                            .foregroundColor(dueDate < Date() && !task.isCompleted ? .red : .secondary)
                    }
                    
                    if let contact = task.contact {
                        Label(contact.displayName, systemImage: "person")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            Spacer()
            
            Text(task.status ?? "Pending")
                .font(.caption)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(statusColor(for: task.status))
                .foregroundColor(.white)
                .cornerRadius(8)
        }
        .padding(.vertical, 4)
        .contentShape(Rectangle())
        .onTapGesture {
            selectedTask = task
        }
        .swipeActions(edge: .trailing) {
            Button(role: .destructive) {
                deleteTask()
            } label: {
                Label("Delete", systemImage: "trash")
            }
            
            Button {
                selectedTask = task
            } label: {
                Label("Edit", systemImage: "pencil")
            }
            .tint(.blue)
        }
    }
    
    private func toggleCompletion() {
        let context = PersistenceController.shared.container.viewContext
        task.status = task.isCompleted ? "Pending" : "Completed"
        task.updatedAt = Date()
        try? context.save()
    }
    
    private func deleteTask() {
        let context = PersistenceController.shared.container.viewContext
        context.delete(task)
        try? context.save()
    }
    
    private func statusColor(for status: String?) -> Color {
        switch status?.lowercased() {
        case "pending": return .orange
        case "in progress": return .blue
        case "completed": return .green
        case "cancelled": return .red
        default: return .gray
        }
    }
}

struct TaskFormView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let task: CRMTask?
    
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
    
    @State private var title = ""
    @State private var details = ""
    @State private var status = "Pending"
    @State private var dueDate = Date().addingTimeInterval(7*24*60*60)
    @State private var selectedContact: Contact?
    @State private var selectedCompany: Company?
    @State private var selectedDeal: Deal?
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    var isEditing: Bool { task != nil }
    
    init(task: CRMTask? = nil) {
        self.task = task
        if let task = task {
            _title = State(initialValue: task.title ?? "")
            _details = State(initialValue: task.details ?? "")
            _status = State(initialValue: task.status ?? "Pending")
            _dueDate = State(initialValue: task.dueDate ?? Date().addingTimeInterval(7*24*60*60))
            _selectedContact = State(initialValue: task.contact)
            _selectedCompany = State(initialValue: task.company)
            _selectedDeal = State(initialValue: task.deal)
        }
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Task")) {
                    TextField("Title *", text: $title)
                    TextEditor(text: $details)
                        .frame(minHeight: 100)
                }
                
                Section(header: Text("Status & Due Date")) {
                    Picker("Status", selection: $status) {
                        ForEach(CRMTask.statuses, id: \.self) { s in
                            Text(s).tag(s)
                        }
                    }
                    
                    DatePicker("Due Date", selection: $dueDate, displayedComponents: .date)
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
            .navigationTitle(isEditing ? "Edit Task" : "New Task")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") { saveTask() }
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
    
    private func saveTask() {
        let targetTask = task ?? CRMTask(context: viewContext)
        
        if task == nil {
            targetTask.id = UUID()
            targetTask.createdAt = Date()
        }
        
        targetTask.title = title.trimmingCharacters(in: .whitespaces)
        targetTask.details = details.trimmingCharacters(in: .whitespaces).isEmpty ? nil : details.trimmingCharacters(in: .whitespaces)
        targetTask.status = status
        targetTask.dueDate = dueDate
        targetTask.contact = selectedContact
        targetTask.company = selectedCompany
        targetTask.deal = selectedDeal
        targetTask.updatedAt = Date()
        
        do {
            try viewContext.save()
            dismiss()
        } catch {
            alertMessage = "Failed to save: \(error.localizedDescription)"
            showingAlert = true
        }
    }
}

struct TaskDetailView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let task: CRMTask
    @State private var showingEdit = false
    @State private var showingDeleteAlert = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Status Header
                    VStack(spacing: 12) {
                        Circle()
                            .fill(statusColor.opacity(0.2))
                            .frame(width: 80, height: 80)
                            .overlay(
                                Image(systemName: task.isCompleted ? "checkmark.circle.fill" : "circle")
                                    .font(.system(size: 32))
                                    .foregroundColor(statusColor)
                            )
                        
                        Text(task.title ?? "Untitled Task")
                            .font(.title)
                            .fontWeight(.bold)
                            .multilineTextAlignment(.center)
                            .strikethrough(task.isCompleted)
                        
                        Text(task.status ?? "Pending")
                            .font(.subheadline)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(statusColor)
                            .foregroundColor(.white)
                            .cornerRadius(16)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.top)
                    
                    // Details
                    if let details = task.details, !details.isEmpty {
                        InfoSection(title: "Details", items: [
                            (details, nil, "doc.text")
                        ])
                    }
                    
                    // Due Date
                    if let dueDate = task.dueDate {
                        InfoSection(title: "Due Date", items: [
                            (dueDate.formatted(date: .complete, time: .omitted), nil, "calendar")
                        ])
                    }
                    
                    // Associations
                    VStack(alignment: .leading, spacing: 12) {
                        if let contact = task.contact {
                            ContactRow(contact: contact)
                                .padding(.horizontal)
                        }
                        if let company = task.company {
                            CompanyRow(company: company)
                                .padding(.horizontal)
                        }
                        if let deal = task.deal {
                            DealRow(deal: deal)
                                .padding(.horizontal)
                        }
                    }
                }
                .padding(.bottom)
            }
            .navigationTitle("Task")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button("Edit") { showingEdit = true }
                        Button(task.isCompleted ? "Mark Pending" : "Mark Complete") {
                            toggleCompletion()
                        }
                        Button(role: .destructive, action: { showingDeleteAlert = true }) {
                            Label("Delete", systemImage: "trash")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showingEdit) {
                TaskFormView(task: task)
            }
            .alert("Delete Task", isPresented: $showingDeleteAlert) {
                Button("Delete", role: .destructive) { deleteTask() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Are you sure you want to delete this task? This action cannot be undone.")
            }
        }
    }
    
    private var statusColor: Color {
        switch task.status?.lowercased() {
        case "pending": return .orange
        case "in progress": return .blue
        case "completed": return .green
        case "cancelled": return .red
        default: return .gray
        }
    }
    
    private func toggleCompletion() {
        task.status = task.isCompleted ? "Pending" : "Completed"
        task.updatedAt = Date()
        try? viewContext.save()
    }
    
    private func deleteTask() {
        viewContext.delete(task)
        try? viewContext.save()
        dismiss()
    }
}