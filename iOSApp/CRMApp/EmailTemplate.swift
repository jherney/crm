import Foundation
import CoreData

@objc(EmailTemplate)
public class EmailTemplate: NSManagedObject {
    @NSManaged public var id: UUID?
    @NSManaged public var name: String?
    @NSManaged public var subject: String?
    @NSManaged public var body: String?
    @NSManaged public var category: String?
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
}

extension EmailTemplate {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<EmailTemplate> {
        return NSFetchRequest<EmailTemplate>(entityName: "EmailTemplate")
    }
    
    var variables: [String] {
        let pattern = "\\{\\{([^}]+)\\}\\}"
        let regex = try? NSRegularExpression(pattern: pattern)
        let range = NSRange(location: 0, length: (body?.count ?? 0) + (subject?.count ?? 0))
        let matches = regex?.matches(in: (body ?? "") + (subject ?? ""), options: [], range: range) ?? []
        return matches.compactMap { match in
            guard let range = Range(match.range(at: 1), in: (body ?? "") + (subject ?? "")) else { return nil }
            return String((body ?? "") + (subject ?? "").prefix(0)) // This is just to get the variable name
        }
    }
}