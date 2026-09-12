import Foundation
import CoreData

@objc(Contact)
public class Contact: NSManagedObject {
    @NSManaged public var id: UUID?
    @NSManaged public var firstName: String?
    @NSManaged public var lastName: String?
    @NSManaged public var email: String?
    @NSManaged public var phone: String?
    @NSManaged public var title: String?
    @NSManaged public var status: String?
    @NSManaged public var notes: String?
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var tags: [String]?
    @NSManaged public var company: Company?
}

extension Contact {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<Contact> {
        return NSFetchRequest<Contact>(entityName: "Contact")
    }
    
    var fullName: String {
        let first = firstName ?? ""
        let last = lastName ?? ""
        return "\(first) \(last)".trimmingCharacters(in: .whitespaces)
    }
    
    var displayName: String {
        let name = fullName
        return name.isEmpty ? "Unnamed Contact" : name
    }
}