import SwiftUI
import CoreData

struct ContentView: View {
    @Environment(\.managedObjectContext) private var viewContext
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            ContactsView()
                .tabItem {
                    Label("Contacts", systemImage: "person.2.fill")
                }
                .tag(0)
            
            CompaniesView()
                .tabItem {
                    Label("Companies", systemImage: "building.2.fill")
                }
                .tag(1)
            
            DealsView()
                .tabItem {
                    Label("Deals", systemImage: "briefcase.fill")
                }
                .tag(2)
            
            ActivitiesView()
                .tabItem {
                    Label("Activities", systemImage: "clock.fill")
                }
                .tag(3)
            
            TasksView()
                .tabItem {
                    Label("Tasks", systemImage: "checklist")
                }
                .tag(4)
            
            TemplatesView()
                .tabItem {
                    Label("Templates", systemImage: "doc.text.fill")
                }
                .tag(5)
            
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
                .tag(6)
        }
        .accentColor(.blue)
    }
}