import SwiftUI
import CoreData

struct DealsView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Deal.createdAt, ascending: false)],
        animation: .default)
    private var deals: FetchedResults<Deal>
    
    @State private var searchText = ""
    @State private var selectedStage = ""
    @State private var showingAddDeal = false
    @State private var selectedDeal: Deal?
    @State private var viewMode = 0 // 0 = list, 1 = pipeline
    
    let stages = Deal.stages
    
    var filteredDeals: [Deal] {
        deals.filter { deal in
            let matchesSearch = searchText.isEmpty ||
                deal.name?.localizedCaseInsensitiveContains(searchText) == true
            let matchesStage = selectedStage.isEmpty || deal.stage == selectedStage
            return matchesSearch && matchesStage
        }
    }
    
    var dealsByStage: [String: [Deal]] {
        Dictionary(grouping: filteredDeals) { $0.stage ?? "Lead" }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // View Mode Selector
                Picker("View", selection: $viewMode) {
                    Text("List").tag(0)
                    Text("Pipeline").tag(1)
                }
                .pickerStyle(SegmentedPickerStyle())
                .padding()
                
                // Search and Filter
                VStack(spacing: 12) {
                    SearchBar(text: $searchText, placeholder: "Search deals...")
                    
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            FilterChip(title: "All", isSelected: selectedStage.isEmpty) {
                                selectedStage = ""
                            }
                            ForEach(stages, id: \.self) { stage in
                                FilterChip(title: stage, isSelected: selectedStage == stage) {
                                    selectedStage = stage
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                }
                .padding(.vertical, 8)
                .background(Color(.systemGroupedBackground))
                
                if viewMode == 0 {
                    // List View
                    if filteredDeals.isEmpty {
                        EmptyStateView(
                            icon: "briefcase.slash",
                            title: "No Deals",
                            message: searchText.isEmpty && selectedStage.isEmpty
                                ? "Tap + to create your first deal"
                                : "No deals match your filters"
                        )
                    } else {
                        List {
                            ForEach(filteredDeals) { deal in
                                DealRow(deal: deal)
                                    .onTapGesture {
                                        selectedDeal = deal
                                    }
                                    .swipeActions(edge: .trailing) {
                                        Button(role: .destructive) {
                                            deleteDeal(deal)
                                        } label: {
                                            Label("Delete", systemImage: "trash")
                                        }
                                        
                                        Button {
                                            selectedDeal = deal
                                        } label: {
                                            Label("Edit", systemImage: "pencil")
                                        }
                                        .tint(.blue)
                                    }
                            }
                        }
                        .listStyle(PlainListStyle())
                    }
                } else {
                    // Pipeline View
                    PipelineView(dealsByStage: dealsByStage, selectedDeal: $selectedDeal)
                }
            }
            .navigationTitle("Deals")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingAddDeal = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddDeal) {
                DealFormView()
            }
            .sheet(item: $selectedDeal) { deal in
                DealDetailView(deal: deal)
            }
        }
    }
    
    private func deleteDeal(_ deal: Deal) {
        withAnimation {
            viewContext.delete(deal)
            try? viewContext.save()
        }
    }
}

struct DealRow: View {
    let deal: Deal
    
    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(stageColor(for: deal.stage).opacity(0.2))
                .frame(width: 44, height: 44)
                .overlay(
                    Image(systemName: "dollarsign.circle.fill")
                        .font(.title2)
                        .foregroundColor(stageColor(for: deal.stage))
                )
            
            VStack(alignment: .leading, spacing: 4) {
                Text(deal.name ?? "Unnamed Deal")
                    .font(.headline)
                
                HStack(spacing: 12) {
                    if let contact = deal.contact {
                        Text(contact.displayName)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    if let company = deal.company {
                        Text(company.name ?? "")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Text(deal.formattedValue)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(.blue)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text(deal.stage ?? "Lead")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(stageColor(for: deal.stage))
                    .foregroundColor(.white)
                    .cornerRadius(8)
                
                Text("\(deal.probability)%")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
    
    private func stageColor(for stage: String?) -> Color {
        switch stage?.lowercased() {
        case "lead": return .orange
        case "qualified": return .blue
        case "proposal": return .purple
        case "negotiation": return .indigo
        case "closed won": return .green
        case "closed lost": return .red
        default: return .gray
        }
    }
}

struct PipelineView: View {
    let dealsByStage: [String: [Deal]]
    @Binding var selectedDeal: Deal?
    
    let stages = Deal.stages
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(alignment: .top, spacing: 16) {
                ForEach(stages, id: \.self) { stage in
                    PipelineColumn(
                        stage: stage,
                        deals: dealsByStage[stage] ?? [],
                        selectedDeal: $selectedDeal
                    )
                }
            }
            .padding()
        }
    }
}

struct PipelineColumn: View {
    let stage: String
    let deals: [Deal]
    @Binding var selectedDeal: Deal?
    
    var totalValue: Double {
        deals.reduce(0) { $0 + $1.value }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Text(stage)
                    .font(.headline)
                Text("\(deals.count) deals · \(totalValue, format: .currency(code: "USD"))")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            ForEach(deals) { deal in
                PipelineDealCard(deal: deal, stageColor: stageColor(for: stage))
                    .onTapGesture {
                        selectedDeal = deal
                    }
            }
            
            Spacer()
        }
        .frame(width: 280)
        .padding()
        .background(Color(.systemGroupedBackground))
        .cornerRadius(12)
    }
    
    private func stageColor(for stage: String) -> Color {
        switch stage.lowercased() {
        case "lead": return .orange
        case "qualified": return .blue
        case "proposal": return .purple
        case "negotiation": return .indigo
        case "closed won": return .green
        case "closed lost": return .red
        default: return .gray
        }
    }
}

struct PipelineDealCard: View {
    let deal: Deal
    let stageColor: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(deal.name ?? "Unnamed Deal")
                .font(.subheadline)
                .fontWeight(.medium)
                .lineLimit(2)
            
            HStack {
                Text(deal.formattedValue)
                    .font(.headline)
                    .foregroundColor(.blue)
                Spacer()
                Text("\(deal.probability)%")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if let contact = deal.contact {
                Text(contact.displayName)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if let expectedClose = deal.expectedCloseDate {
                Text("Closes: \(expectedClose.formatted(date: .abbreviated, time: .omitted))")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(12)
        .background(Color(.systemBackground))
        .cornerRadius(10)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(stageColor.opacity(0.3), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
    }
}

struct DealFormView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let deal: Deal?
    
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Contact.lastName, ascending: true)],
        animation: .default)
    private var contacts: FetchedResults<Contact>
    
    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Company.name, ascending: true)],
        animation: .default)
    private var companies: FetchedResults<Company>
    
    @State private var name = ""
    @State private var value = ""
    @State private var stage = "Lead"
    @State private var probability = 10
    @State private var expectedCloseDate = Date().addingTimeInterval(30*24*60*60)
    @State private var selectedContact: Contact?
    @State private var selectedCompany: Company?
    @State private var notes = ""
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    var isEditing: Bool { deal != nil }
    
    init(deal: Deal? = nil) {
        self.deal = deal
        if let deal = deal {
            _name = State(initialValue: deal.name ?? "")
            _value = State(initialValue: String(deal.value))
            _stage = State(initialValue: deal.stage ?? "Lead")
            _probability = State(initialValue: Int(deal.probability))
            _expectedCloseDate = State(initialValue: deal.expectedCloseDate ?? Date().addingTimeInterval(30*24*60*60))
            _selectedContact = State(initialValue: deal.contact)
            _selectedCompany = State(initialValue: deal.company)
            _notes = State(initialValue: deal.notes ?? "")
        }
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Deal Info")) {
                    TextField("Deal Name *", text: $name)
                    TextField("Value", text: $value)
                        .keyboardType(.decimalPad)
                }
                
                Section(header: Text("Pipeline")) {
                    Picker("Stage", selection: $stage) {
                        ForEach(Deal.stages, id: \.self) { s in
                            Text(s).tag(s)
                        }
                    }
                    
                    Stepper("Probability: \(probability)%", value: $probability, in: 0...100, step: 10)
                    
                    DatePicker("Expected Close", selection: $expectedCloseDate, displayedComponents: .date)
                }
                
                Section(header: Text("Associations")) {
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
                }
                
                Section(header: Text("Notes")) {
                    TextEditor(text: $notes)
                        .frame(minHeight: 100)
                }
            }
            .navigationTitle(isEditing ? "Edit Deal" : "New Deal")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") { saveDeal() }
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
    
    private func saveDeal() {
        let targetDeal = deal ?? Deal(context: viewContext)
        
        if deal == nil {
            targetDeal.id = UUID()
            targetDeal.createdAt = Date()
        }
        
        targetDeal.name = name.trimmingCharacters(in: .whitespaces)
        targetDeal.value = Double(value) ?? 0
        targetDeal.stage = stage
        targetDeal.probability = Int16(probability)
        targetDeal.expectedCloseDate = expectedCloseDate
        targetDeal.contact = selectedContact
        targetDeal.company = selectedCompany
        targetDeal.notes = notes.trimmingCharacters(in: .whitespaces).isEmpty ? nil : notes.trimmingCharacters(in: .whitespaces)
        targetDeal.updatedAt = Date()
        
        do {
            try viewContext.save()
            logActivity(type: isEditing ? "updated" : "created", deal: targetDeal)
            dismiss()
        } catch {
            alertMessage = "Failed to save: \(error.localizedDescription)"
            showingAlert = true
        }
    }
    
    private func logActivity(type: String, deal: Deal) {
        let activity = Activity(context: viewContext)
        activity.id = UUID()
        activity.type = type
        activity.title = "Deal \(type): \(deal.name ?? "")"
        activity.details = "Stage: \(deal.stage ?? ""), Value: \(deal.formattedValue)"
        activity.createdAt = Date()
        activity.deal = deal
        try? viewContext.save()
    }
}

struct DealDetailView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @Environment(\.dismiss) private var dismiss
    
    let deal: Deal
    @State private var showingEdit = false
    @State private var showingDeleteAlert = false
    @State private var activities: [Activity] = []
    @State private var tasks: [CRMTask] = []
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    VStack(spacing: 12) {
                        Circle()
                            .fill(stageColor.opacity(0.2))
                            .frame(width: 80, height: 80)
                            .overlay(
                                Image(systemName: "dollarsign.circle.fill")
                                    .font(.system(size: 32))
                                    .foregroundColor(stageColor)
                            )
                        
                        Text(deal.name ?? "Unnamed Deal")
                            .font(.title)
                            .fontWeight(.bold)
                        
                        Text(deal.formattedValue)
                            .font(.title2)
                            .foregroundColor(.blue)
                        
                        Text(deal.stage ?? "Lead")
                            .font(.subheadline)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(stageColor)
                            .foregroundColor(.white)
                            .cornerRadius(16)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.top)
                    
                    // Details
                    VStack(spacing: 12) {
                        DetailRow(label: "Probability", value: "\(deal.probability)%")
                        if let closeDate = deal.expectedCloseDate {
                            DetailRow(label: "Expected Close", value: closeDate.formatted(date: .abbreviated, time: .omitted))
                        }
                    }
                    .padding()
                    .background(Color(.systemGroupedBackground))
                    .cornerRadius(12)
                    .padding(.horizontal)
                    
                    // Associations
                    if deal.contact != nil || deal.company != nil {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Associated")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            if let contact = deal.contact {
                                ContactRow(contact: contact)
                                    .padding(.horizontal)
                            }
                            if let company = deal.company {
                                CompanyRow(company: company)
                                    .padding(.horizontal)
                            }
                        }
                    }
                    
                    // Notes
                    if let notes = deal.notes, !notes.isEmpty {
                        InfoSection(title: "Notes", items: [
                            (notes, nil, "note.text")
                        ])
                    }
                    
                    // Tasks
                    if !tasks.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Tasks")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            ForEach(tasks) { task in
                                TaskRow(task: task)
                            }
                        }
                    }
                    
                    // Activities
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
            .navigationTitle("Deal")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button("Edit") { showingEdit = true }
                        Button("Add Task") { addTask() }
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
                DealFormView(deal: deal)
            }
            .alert("Delete Deal", isPresented: $showingDeleteAlert) {
                Button("Delete", role: .destructive) { deleteDeal() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Are you sure you want to delete this deal? This action cannot be undone.")
            }
            .onAppear { loadData() }
        }
    }
    
    private var stageColor: Color {
        switch deal.stage?.lowercased() {
        case "lead": return .orange
        case "qualified": return .blue
        case "proposal": return .purple
        case "negotiation": return .indigo
        case "closed won": return .green
        case "closed lost": return .red
        default: return .gray
        }
    }
    
    private func loadData() {
        let actRequest: NSFetchRequest<Activity> = Activity.fetchRequest()
        actRequest.predicate = NSPredicate(format: "deal == %@", deal)
        actRequest.sortDescriptors = [NSSortDescriptor(keyPath: \Activity.createdAt, ascending: false)]
        actRequest.fetchLimit = 10
        activities = (try? viewContext.fetch(actRequest)) ?? []
        
        let taskRequest: NSFetchRequest<CRMTask> = CRMTask.fetchRequest()
        taskRequest.predicate = NSPredicate(format: "deal == %@", deal)
        taskRequest.sortDescriptors = [NSSortDescriptor(keyPath: \CRMTask.dueDate, ascending: true)]
        tasks = (try? viewContext.fetch(taskRequest)) ?? []
    }
    
    private func addTask() {
        let task = CRMTask(context: viewContext)
        task.id = UUID()
        task.title = "New Task"
        task.status = "Pending"
        task.dueDate = Date().addingTimeInterval(7*24*60*60)
        task.createdAt = Date()
        task.deal = deal
        try? viewContext.save()
        loadData()
    }
    
    private func addActivity() {
        let activity = Activity(context: viewContext)
        activity.id = UUID()
        activity.type = "note"
        activity.title = "Note added"
        activity.details = ""
        activity.createdAt = Date()
        activity.deal = deal
        try? viewContext.save()
        loadData()
    }
    
    private func deleteDeal() {
        viewContext.delete(deal)
        try? viewContext.save()
        dismiss()
    }
}

struct DetailRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .font(.subheadline)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .font(.subheadline)
                .fontWeight(.medium)
        }
    }
}

struct CompanyRow: View {
    let company: Company
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "building.2.fill")
                .foregroundColor(.green)
                .frame(width: 24)
            VStack(alignment: .leading, spacing: 2) {
                Text(company.name ?? "Unnamed Company")
                    .font(.subheadline)
                    .fontWeight(.medium)
                if let email = company.email {
                    Text(email)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            Spacer()
        }
        .padding()
        .background(Color(.systemGroupedBackground))
        .cornerRadius(10)
        .padding(.horizontal)
    }
}