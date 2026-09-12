import Foundation
import CoreData

@objc(CRMTask)
public class CRMTask: NSManagedObject {
    @NSManaged public var id: UUID?
    @NSManaged public var title: String?
    @NSManaged public var details: String?
    @NSManaged public var status: String?
    @NSManaged public var dueDate: Date?
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var contact: Contact?
    @NSManaged public var company: Company?
    @NSManaged public var deal: Deal?
}

extension CRMTask {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<CRMTask> {
        return NSFetchRequest<CRMTask>(entityName: "CRMTask")
    }
    
    static let statuses = ["Pending", "In Progress", "Completed", "Cancelled"]
    
    var isCompleted: Bool {
        return status == "Completed"
    }
}