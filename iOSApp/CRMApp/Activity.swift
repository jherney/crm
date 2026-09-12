import Foundation
import CoreData

@objc(Activity)
public class Activity: NSManagedObject {
    @NSManaged public var id: UUID?
    @NSManaged public var type: String?
    @NSManaged public var title: String?
    @NSManaged public var details: String?
    @NSManaged public var createdAt: Date?
    @NSManaged public var contact: Contact?
    @NSManaged public var company: Company?
    @NSManaged public var deal: Deal?
}

extension Activity {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<Activity> {
        return NSFetchRequest<Activity>(entityName: "Activity")
    }
    
    var displayType: String {
        return type?.capitalized ?? "Activity"
    }
}